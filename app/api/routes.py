import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_logger, get_settings
from app.schemas.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorResponse,
    HealthResponse,
)
from app.services.orchestrator import TroubleshootingOrchestrator, get_orchestrator

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the API and its dependencies.",
    tags=["Health"]
)
async def health_check(
    orchestrator: Annotated[TroubleshootingOrchestrator, Depends(get_orchestrator)]
) -> HealthResponse:
    """Return the health status of the application."""
    settings = get_settings()
    
    return HealthResponse(
        status="healthy" if orchestrator.is_ready else "degraded",
        version=settings.app_version,
        openai_configured=bool(settings.openai_api_key),
        vector_store_ready=orchestrator.retriever.is_ready
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Analyze Kubernetes Issue",
    description="""
    Analyze a Kubernetes pod issue using multi-agent AI analysis.
    
    The system will:
    1. Analyze pod logs and describe output for error patterns
    2. Validate the deployment YAML for misconfigurations
    3. Retrieve relevant Kubernetes documentation
    4. Synthesize findings to determine root cause and provide fix steps
    
    Returns a comprehensive analysis with:
    - Error category classification
    - Root cause identification
    - Step-by-step fix instructions
    - Suggested kubectl commands
    """,
    tags=["Analysis"]
)
async def analyze_kubernetes_issue(
    request: AnalyzeRequest,
    orchestrator: Annotated[TroubleshootingOrchestrator, Depends(get_orchestrator)]
) -> AnalyzeResponse:
    """
    Analyze a Kubernetes issue and return troubleshooting recommendations.
    
    - **describe_output**: Output from `kubectl describe pod <pod-name>`
    - **pod_logs**: Logs from `kubectl logs <pod-name>`
    - **deployment_yaml**: The deployment YAML configuration
    """
    request_id = uuid.uuid4().hex[:12]
    logger.info(f"[{request_id}] Received analysis request")
    
    try:
        result = await orchestrator.analyze(request)
        logger.info(f"[{request_id}] Analysis completed successfully")
        return result
        
    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Validation Error",
                detail=str(e),
                request_id=request_id
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"[{request_id}] Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Analysis Failed",
                detail=str(e),
                request_id=request_id
            ).model_dump()
        )
