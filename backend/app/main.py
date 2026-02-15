import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# We need to add the project root to python path so we can import 'rag_engine'
# This allows the backend to "see" the agent code we wrote earlier.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.app.models.schemas import ChatRequest, ChatResponse
from rag_engine.agents.onboarding_agent import agent_executor
from langchain_core.messages import HumanMessage

app = FastAPI(title="Nebula AI Onboarding API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8501").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "Nebula Onboarding AI"}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"Received: {request.query}")
        
        # Invoke the Agent
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")