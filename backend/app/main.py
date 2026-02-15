import sys
import os
import json
import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

# We need to add the project root to python path so we can import 'rag_engine'
# This allows the backend to "see" the agent code we wrote earlier.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.app.models.schemas import ChatRequest, ChatResponse
from rag_engine.agents.onboarding_agent import agent_executor
from langchain_core.messages import HumanMessage

# --- Logging ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nebula.api")

app = FastAPI(title="Nebula AI Onboarding API", version="1.0")

# This allows a Frontend (running on localhost:3000) to talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration_ms:.0f}ms)")
    return response

def _extract_text(raw_content) -> str:
    """Extract plain text from Gemini's response format."""
    if isinstance(raw_content, list):
        return "".join(
            part.get("text", "") for part in raw_content if part.get("type") == "text"
        )
    return str(raw_content)

@app.get("/")
async def root():
    return {"status": "ok", "service": "Nebula Onboarding AI"}

@app.get("/health")
async def health_check():
    """Detailed health check with database and LLM status."""
    health = {"status": "ok", "service": "Nebula Onboarding AI", "checks": {}}

    # Check ChromaDB
    try:
        from langchain_chroma import Chroma
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        db_path = os.getenv("DB_PATH", "./chroma_db")
        if os.path.exists(db_path):
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
            db = Chroma(persist_directory=db_path, embedding_function=embeddings)
            doc_count = db._collection.count()
            health["checks"]["vector_db"] = {"status": "ok", "doc_count": doc_count}
        else:
            health["checks"]["vector_db"] = {"status": "warning", "doc_count": 0}
    except Exception as e:
        health["checks"]["vector_db"] = {"status": "error", "detail": str(e)}
        health["status"] = "degraded"

    # Check data files
    data_path = os.getenv("DATA_PATH", "./data_seed")
    health["checks"]["data_files"] = {
        "org_chart": os.path.exists(os.path.join(data_path, "structured", "org_chart.json")),
        "role_definitions": os.path.exists(os.path.join(data_path, "structured", "role_definitions.json")),
    }

    return health

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        logger.info(f"Chat request: {request.query[:80]}...")
        response = agent_executor.invoke(
            {"messages": [HumanMessage(content=request.query)]},
            config={"configurable": {"thread_id": request.thread_id}}
        )
        final_message = response["messages"][-1]
        raw_content = final_message.content
        
        # Handle different content types from Gemini
        if isinstance(raw_content, list):
            # It's a list of parts: [{'type': 'text', 'text': '...'}]
            final_answer = "".join(
                [part.get("text", "") for part in raw_content if part.get("type") == "text"]
            )
        else:
            # It's already a string
            final_answer = str(raw_content)
        
        print(f"Sending: {final_answer[:50]}...")
        return ChatResponse(answer=final_answer)

    except Exception as e:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@app.post("/api/v1/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """SSE streaming endpoint that yields agent events in real-time."""
    logger.info(f"Stream request: {request.query[:80]}...")

    def event_generator():
        try:
            for event in agent_executor.stream(
                {"messages": [HumanMessage(content=request.query)]},
                config={"configurable": {"thread_id": request.thread_id}},
                stream_mode="updates",
            ):
                for node_name, node_data in event.items():
                    messages = node_data.get("messages", [])
                    for msg in messages:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                logger.info(f"Tool call: {tc['name']}({tc['args']})")
                                yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'args': tc['args']})}\n\n"
                        elif isinstance(msg, ToolMessage):
                            yield f"data: {json.dumps({'type': 'tool_result', 'name': msg.name, 'content': msg.content[:200]})}\n\n"
                        elif hasattr(msg, "content") and msg.content:
                            text = _extract_text(msg.content)
                            if text:
                                yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.exception("Stream error")
            yield f"data: {json.dumps({'type': 'error', 'content': 'An internal error occurred.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
