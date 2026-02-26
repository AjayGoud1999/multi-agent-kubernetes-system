from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings, setup_logging
from app.services.orchestrator import get_orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    settings = get_settings()
    logger = setup_logging(settings)
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    try:
        orchestrator = await get_orchestrator()
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        raise
    
    yield
    
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
# K8s AI Troubleshooter

A production-grade Multi-Agent Kubernetes Troubleshooting System that uses AI to analyze and diagnose Kubernetes issues.

## Features

- **Log Analysis Agent**: Analyzes pod logs and kubectl describe output to identify error patterns
- **YAML Validation Agent**: Validates deployment configurations for misconfigurations and best practices
- **Root Cause Agent**: Synthesizes findings from all agents to determine root cause
- **RAG Integration**: Retrieves relevant Kubernetes documentation for accurate recommendations

## Usage

Send a POST request to `/analyze` with:
- `describe_output`: Output from `kubectl describe pod`
- `pod_logs`: Pod logs from `kubectl logs`
- `deployment_yaml`: The deployment YAML configuration

The system will return a comprehensive analysis with error categorization, root cause, fix steps, and kubectl commands.
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router, prefix="/api/v1")
    
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint redirect to docs."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
