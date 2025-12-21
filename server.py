"""
FastAPI Server for AI Agent Blueprint
Exposes agents as REST API endpoints for Kubernetes deployment
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
import uvicorn
import asyncio
import json
from datetime import datetime
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from agent_blueprint import (
    create_react_agent,
    create_plan_execute_agent,
    create_reflection_agent,
    create_multi_agent_system
)
from langchain_core.messages import HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('agent_requests_total', 'Total agent requests', ['pattern', 'status'])
REQUEST_DURATION = Histogram('agent_request_duration_seconds', 'Request duration', ['pattern'])
AGENT_ERRORS = Counter('agent_errors_total', 'Total agent errors', ['pattern', 'error_type'])

# Initialize FastAPI
app = FastAPI(
    title="AI Agent Blueprint API",
    description="LangGraph-based AI agents with 4 design patterns",
    version="1.0.0"
)

# Initialize agents (singleton pattern)
agents = {
    "react": None,
    "plan_execute": None,
    "reflection": None,
    "multi_agent": None
}

def get_agent(pattern: str):
    """Lazy initialization of agents"""
    if agents[pattern] is None:
        if pattern == "react":
            agents[pattern] = create_react_agent()
        elif pattern == "plan_execute":
            agents[pattern] = create_plan_execute_agent()
        elif pattern == "reflection":
            agents[pattern] = create_reflection_agent()
        elif pattern == "multi_agent":
            agents[pattern] = create_multi_agent_system()
    return agents[pattern]


# Request/Response models
class AgentRequest(BaseModel):
    query: str = Field(..., description="User query for the agent")
    pattern: Literal["react", "plan_execute", "reflection", "multi_agent"] = Field(
        ..., description="Agent pattern to use"
    )
    max_iterations: Optional[int] = Field(default=3, description="Maximum iterations for the agent")
    thread_id: Optional[str] = Field(default=None, description="Thread ID for conversation continuity")
    stream: Optional[bool] = Field(default=False, description="Enable streaming response")


class AgentResponse(BaseModel):
    pattern: str
    query: str
    result: str
    metadata: Dict[str, Any]
    timestamp: str
    thread_id: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    agents_loaded: list[str]


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Kubernetes health check endpoint"""
    loaded = [pattern for pattern, agent in agents.items() if agent is not None]
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        agents_loaded=loaded
    )


@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness check"""
    # Verify at least one agent can be initialized
    try:
        test_agent = get_agent("react")
        return {"status": "ready", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/agent/invoke", response_model=AgentResponse)
async def invoke_agent(request: AgentRequest):
    """
    Invoke an agent with the specified pattern
    
    Patterns:
    - react: Reasoning + Action loop
    - plan_execute: Strategic planning then execution
    - reflection: Self-critique and refinement
    - multi_agent: Collaborative specialist agents
    """
    start_time = datetime.now()
    
    try:
        # Get agent
        agent = get_agent(request.pattern)
        
        # Prepare state based on pattern
        thread_id = request.thread_id or f"{request.pattern}-{start_time.timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}
        
        if request.pattern == "react":
            state = {
                "messages": [HumanMessage(content=request.query)],
                "iteration": 0,
                "max_iterations": request.max_iterations
            }
        elif request.pattern == "plan_execute":
            state = {
                "messages": [HumanMessage(content=request.query)],
                "plan": [],
                "completed_steps": [],
                "current_step": 0,
                "results": {}
            }
        elif request.pattern == "reflection":
            state = {
                "messages": [HumanMessage(content=request.query)],
                "draft": "",
                "critique": "",
                "iteration": 0,
                "max_iterations": request.max_iterations,
                "quality_score": 0.0
            }
        else:  # multi_agent
            state = {
                "messages": [HumanMessage(content=request.query)],
                "next_agent": "supervisor",
                "completed_agents": [],
                "findings": {},
                "confidence": 0.0
            }
        
        # Invoke agent
        logger.info(f"Invoking {request.pattern} agent for query: {request.query[:50]}...")
        result = agent.invoke(state, config)
        
        # Extract final response
        final_message = result["messages"][-1].content
        
        # Build metadata
        metadata = {
            "iterations": result.get("iteration", 0),
            "plan": result.get("plan", []),
            "quality_score": result.get("quality_score", 0),
            "completed_agents": result.get("completed_agents", []),
            "confidence": result.get("confidence", 0),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }
        
        # Update metrics
        REQUEST_COUNT.labels(pattern=request.pattern, status="success").inc()
        REQUEST_DURATION.labels(pattern=request.pattern).observe(metadata["processing_time"])
        
        return AgentResponse(
            pattern=request.pattern,
            query=request.query,
            result=final_message,
            metadata=metadata,
            timestamp=datetime.now().isoformat(),
            thread_id=thread_id
        )
        
    except Exception as e:
        logger.error(f"Error invoking {request.pattern} agent: {e}", exc_info=True)
        REQUEST_COUNT.labels(pattern=request.pattern, status="error").inc()
        AGENT_ERRORS.labels(pattern=request.pattern, error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/stream")
async def stream_agent(request: AgentRequest):
    """
    Stream agent responses as they're generated
    Useful for real-time user feedback
    """
    if not request.stream:
        raise HTTPException(status_code=400, detail="Streaming not enabled in request")
    
    async def generate_stream():
        try:
            agent = get_agent(request.pattern)
            thread_id = request.thread_id or f"{request.pattern}-stream-{datetime.now().timestamp()}"
            config = {"configurable": {"thread_id": thread_id}}
            
            # Prepare state (simplified for streaming)
            state = {"messages": [HumanMessage(content=request.query)]}
            if request.pattern == "react":
                state.update({"iteration": 0, "max_iterations": request.max_iterations})
            
            # Stream events
            async for event in agent.astream_events(state, config, version="v1"):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield f"data: {json.dumps({'content': chunk.content})}\n\n"
                        await asyncio.sleep(0.01)  # Small delay for smoother streaming
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "AI Agent Blueprint",
        "version": "1.0.0",
        "patterns": ["react", "plan_execute", "reflection", "multi_agent"],
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "metrics": "/metrics",
            "invoke": "/agent/invoke",
            "stream": "/agent/stream"
        }
    }


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Agent Blueprint API")
    # Pre-warm one agent for faster first requests
    get_agent("react")
    logger.info("React agent pre-loaded")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Agent Blueprint API")


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
