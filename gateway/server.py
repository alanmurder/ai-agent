"""Web API Server - FastAPI application with cluster support."""

import os
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from gateway.router import GatewayRouter
from gateway.types import Message, ChannelType
from core.logging import setup_logging, get_logger
from core.health import get_health_checker, set_instance_info, HealthStatus
from core.metrics import get_metrics, MetricNames
from core.concurrency import init_concurrency_infrastructure, close_concurrency_infrastructure
from config import get_settings

# Setup logging
setup_logging(level="INFO", format_type="json")

logger = get_logger("web.server")
settings = get_settings()
metrics = get_metrics()

# Instance info from environment
POD_NAME = os.environ.get("POD_NAME", "unknown")
POD_NAMESPACE = os.environ.get("POD_NAMESPACE", "default")
CLUSTER_NAME = os.environ.get("CLUSTER_NAME", "local")

# Create FastAPI app
app = FastAPI(
    title="AI Agent API",
    description="AI Agent with evolution capabilities",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.gateway.web.cors_origins if hasattr(settings.gateway.web, 'cors_origins') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gateway router
gateway_router: Optional[GatewayRouter] = None


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    user_id: Optional[str] = "default"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    content: str
    session_id: str
    user_id: str
    model_used: Optional[str] = None
    timestamp: str


class SkillListResponse(BaseModel):
    """Skill list response model."""
    skills: list[dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    details: dict[str, Any]


@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    global gateway_router

    # Set instance info for health checker
    set_instance_info(POD_NAME, CLUSTER_NAME)

    # Initialize concurrency infrastructure (Redis, Postgres pools)
    await init_concurrency_infrastructure()

    gateway_router = GatewayRouter()
    await gateway_router.initialize()

    logger.info(
        "web_server_started",
        port=settings.gateway.web.port,
        pod_name=POD_NAME,
        cluster_name=CLUSTER_NAME,
    )

    metrics.increment("server_started")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await close_concurrency_infrastructure()

    logger.info(
        "web_server_shutdown",
        pod_name=POD_NAME,
    )

    metrics.increment("server_shutdown")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Full health check endpoint."""
    health_checker = get_health_checker()
    health = await health_checker.check_all()

    return HealthResponse(
        status=health.status.value,
        details={
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "latency_ms": c.latency_ms,
                }
                for c in health.components
            ],
            "uptime_seconds": health.uptime_seconds,
            "instance_id": health.instance_id,
            "cluster_info": health.cluster_info,
            "version": health.version,
        },
    )


@app.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    health_checker = get_health_checker()
    is_alive = await health_checker.check_live()

    if is_alive:
        return {"status": "alive", "pod": POD_NAME}

    raise HTTPException(status_code=503, detail="Not alive")


@app.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    health_checker = get_health_checker()
    is_ready, issues = await health_checker.check_ready()

    if is_ready:
        return {"status": "ready", "pod": POD_NAME}

    raise HTTPException(
        status_code=503,
        detail={"status": "not_ready", "issues": issues},
    )


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return metrics.export_prometheus()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint."""
    if not gateway_router:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Create message
    message = Message.from_web(
        user_id=request.user_id or "default",
        content=request.message,
    )

    try:
        # Route to agent
        output = await gateway_router.route_message(message)

        return ChatResponse(
            content=output.content,
            session_id=output.session_id,
            user_id=output.user_id,
            model_used=output.model_used,
            timestamp=output.timestamp.isoformat(),
        )

    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket chat endpoint."""
    await websocket.accept()

    user_id = "default"
    session_id: Optional[str] = None

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            message_content = data.get("message", "")
            user_id = data.get("user_id", "default")
            session_id = data.get("session_id")

            # Create message
            message = Message.from_web(
                user_id=user_id,
                content=message_content,
            )

            # Stream response
            if gateway_router:
                async for chunk in await gateway_router.stream_message(message):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk,
                    })

                # Send completion signal
                await websocket.send_json({
                    "type": "complete",
                    "session_id": session_id or message.id,
                })

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", user_id=user_id)

    except Exception as e:
        logger.error("websocket_error", error=str(e))
        await websocket.close()


@app.get("/api/skills", response_model=SkillListResponse)
async def list_skills(category: Optional[str] = None):
    """List available skills."""
    if not gateway_router or not gateway_router.agent_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")

    skills = await gateway_router.agent_engine.skill_manager.discover_skills(category)

    skill_list = []

    for skill in skills:
        skill_list.append({
            "name": skill.name,
            "version": skill.config.version,
            "category": skill.category.value,
            "description": skill.config.description,
            "enabled": skill.config.enabled,
        })

    return SkillListResponse(skills=skill_list)


@app.post("/api/memory")
async def update_memory(
    user_id: str,
    key: str,
    value: Any,
):
    """Update user memory."""
    if not gateway_router or not gateway_router.agent_engine:
        raise HTTPException(status_code=503, detail="Service not initialized")

    await gateway_router.agent_engine.memory_manager.update_memory(
        user_id=user_id,
        key=key,
        value=value,
    )

    return {"status": "success", "key": key}


def run_server():
    """Run the web server."""
    import uvicorn

    uvicorn.run(
        "gateway.server:app",
        host=settings.gateway.web.host,
        port=settings.gateway.web.port,
        reload=True,
    )


if __name__ == "__main__":
    run_server()