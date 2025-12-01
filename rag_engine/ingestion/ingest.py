import os
import glob
import json
import hashlib
from typing import List, Dict
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()

# --- CONFIGURATION ---
DATA_PATH = "./data_seed/policies"
DB_PATH = "./chroma_db"
STATE_FILE = "ingestion_state.json"  # The "Registry" of what we've already learned

def calculate_file_hash(filepath: str) -> str:
    """Creates a unique fingerprint (MD5) for a file's content."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def load_state() -> Dict[str, str]:
    """Loads the registry of known files and their hashes."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state: Dict[str, str]):
    """Saves the registry back to disk."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def process_document(file_path: str) -> List[Document]:
    """Reads and splits a single document."""
    try:
        loader = TextLoader(file_path, encoding='utf-8')
        raw_docs = loader.load()
        
        # 1. Split by Header
        headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        
        md_header_splits = []
        for doc in raw_docs:
            splits = markdown_splitter.split_text(doc.page_content)
            for split in splits:
                split.metadata.update(doc.metadata)
                md_header_splits.append(split)

        # 2. Split by Character (for large sections)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        final_splits = text_splitter.split_documents(md_header_splits)
        return final_splits
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def ingest_data():
    print("--- Starting Incremental Ingestion ---")
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in .env")
        return

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_store = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    
    # 1. Load the current registry (What we knew properly before)
    known_files = load_state()
    current_files = glob.glob(f"{DATA_PATH}/*.md")
    
    current_file_hashes = {}
    docs_to_add = []
    files_to_remove = []

    print(f"Scanning {len(current_files)} files...")

    # 2. Identify Changes (The "Diff" Logic)
    for file_path in current_files:
        filename = os.path.basename(file_path)
        new_hash = calculate_file_hash(file_path)
        current_file_hashes[filename] = new_hash
        
        # Check if file is new or modified
        if filename not in known_files:
            print(f"New File Detected: {filename}")
            docs_to_add.extend(process_document(file_path))
        elif known_files[filename] != new_hash:
            print(f"Modified File: {filename} (Re-ingesting...)")
            # Mark old version for deletion logic below
            files_to_remove.append(filename) 
            docs_to_add.extend(process_document(file_path))
        else:
            # Hash matches -> No change -> Skip
            pass

    # 3. Identify Deletions (Files that existed before but are gone now)
    for filename in known_files:
        if filename not in current_file_hashes:
            print(f"Deleted File Detected: {filename}")
            files_to_remove.append(filename)

    # 4. EXECUTE DB UPDATES
    
    # A. Remove old/changed chunks first
    if files_to_remove:
        print(f"Removing {len(files_to_remove)} outdated documents from DB...")
        # Chroma allows deleting by metadata "source"
        for filename in files_to_remove:
            # We reconstruct the full path because TextLoader saves full path in metadata
            full_path_guess = os.path.join(DATA_PATH, filename)
            # Use specific Chroma collection delete method
            vector_store._collection.delete(where={"source": full_path_guess})

    # B. Add new chunks
    if docs_to_add:
        print(f"Upserting {len(docs_to_add)} new chunks...")
        vector_store.add_documents(docs_to_add)
        print("Database Updated.")
    else:
        print("No content changes detected.")

    # 5. Save new state
    save_state(current_file_hashes)
    print("--- Ingestion Complete ---")

if __name__ == "__main__":
    ingest_data()