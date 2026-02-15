import sys
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.app.models.schemas import ChatRequest, ChatResponse
from rag_engine.agents.onboarding_agent import agent_executor
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage

app = FastAPI(title="Nebula AI Onboarding API", version="1.0")

# This allows a Frontend (running on localhost:3000) to talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _extract_text(raw_content) -> str:
    """Extract plain text from Gemini's response format."""
    if isinstance(raw_content, list):
        return "".join(
            part.get("text", "") for part in raw_content if part.get("type") == "text"
        )
    return str(raw_content)

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "Nebula Onboarding AI"}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response = agent_executor.invoke(
            {"messages": [HumanMessage(content=request.query)]},
            config={"configurable": {"thread_id": request.thread_id}}
        )
        final_message = response["messages"][-1]
        return ChatResponse(answer=_extract_text(final_message.content))

    except Exception as e:
        print(f"Error: {str(e)}")
        # Print the full error to logs for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@app.post("/api/v1/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """SSE streaming endpoint that yields agent events in real-time."""
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
                                yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'args': tc['args']})}\n\n"
                        elif isinstance(msg, ToolMessage):
                            yield f"data: {json.dumps({'type': 'tool_result', 'name': msg.name, 'content': msg.content[:200]})}\n\n"
                        elif hasattr(msg, "content") and msg.content:
                            text = _extract_text(msg.content)
                            if text:
                                yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': 'An internal error occurred.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
