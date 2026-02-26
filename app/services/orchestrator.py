import asyncio
from typing import Optional

from app.agents.log_agent import LogAnalysisAgent, LogAnalysisInput
from app.agents.root_cause_agent import RootCauseAgent, RootCauseInput
from app.agents.yaml_agent import YAMLValidationAgent, YAMLValidationInput
from app.config import Settings, get_logger, get_settings
from app.rag.retriever import DocumentRetriever
from app.schemas.models import AnalyzeRequest, AnalyzeResponse

logger = get_logger(__name__)


class TroubleshootingOrchestrator:
    """Orchestrates the multi-agent troubleshooting workflow."""
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.log_agent = LogAnalysisAgent(settings)
        self.yaml_agent = YAMLValidationAgent(settings)
        self.root_cause_agent = RootCauseAgent(settings)
        self.retriever = DocumentRetriever(settings)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the orchestrator and its components."""
        if self._initialized:
            return
        
        logger.info("Initializing troubleshooting orchestrator")
        await self.retriever.initialize()
        self._initialized = True
        logger.info("Orchestrator initialized successfully")
    
    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Execute the full troubleshooting workflow.
        
        Flow:
        1. Log Analysis Agent analyzes describe output + logs
        2. YAML Validation Agent analyzes deployment YAML
        3. RAG retrieves relevant K8s documentation
        4. Root Cause Agent synthesizes all findings
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting troubleshooting analysis")
        
        log_input = LogAnalysisInput(
            describe_output=request.describe_output,
            pod_logs=request.pod_logs
        )
        yaml_input = YAMLValidationInput(
            deployment_yaml=request.deployment_yaml
        )
        
        log_result, yaml_result = await asyncio.gather(
            self.log_agent.execute(log_input),
            self.yaml_agent.execute(yaml_input)
        )
        
        logger.info(f"Log analysis complete: {log_result.error_category.value}")
        logger.info(f"YAML validation complete: {len(yaml_result.misconfigurations)} issues found")
        
        rag_query = self._build_rag_query(log_result, yaml_result)
        rag_context = await self.retriever.retrieve(rag_query)
        
        logger.info(f"Retrieved {len(rag_context)} documentation chunks")
        
        root_cause_input = RootCauseInput(
            log_analysis=log_result,
            yaml_validation=yaml_result,
            rag_context=rag_context
        )
        root_cause_result = await self.root_cause_agent.execute(root_cause_input)
        
        logger.info("Root cause analysis complete")
        
        overall_confidence = self._calculate_confidence(
            log_result.confidence,
            yaml_result.confidence,
            root_cause_result.confidence
        )
        
        response = AnalyzeResponse(
            error_category=log_result.error_category,
            root_cause=root_cause_result.root_cause,
            explanation=root_cause_result.explanation,
            fix_steps=root_cause_result.fix_steps,
            kubectl_commands=root_cause_result.kubectl_commands,
            log_analysis=log_result,
            yaml_validation=yaml_result,
            confidence=overall_confidence,
            rag_context_used=rag_context
        )
        
        logger.info(f"Analysis complete with confidence: {overall_confidence:.2f}")
        return response
    
    def _build_rag_query(self, log_result, yaml_result) -> str:
        """Build a query for RAG retrieval based on analysis results."""
        query_parts = [
            f"Kubernetes {log_result.error_category.value}",
            log_result.probable_cause
        ]
        
        for misc in yaml_result.misconfigurations[:2]:
            query_parts.append(misc.issue)
        
        return " ".join(query_parts)
    
    def _calculate_confidence(
        self,
        log_confidence: float,
        yaml_confidence: float,
        root_cause_confidence: float
    ) -> float:
        """Calculate aggregated confidence score."""
        weights = {
            "log": 0.3,
            "yaml": 0.2,
            "root_cause": 0.5
        }
        
        return (
            log_confidence * weights["log"] +
            yaml_confidence * weights["yaml"] +
            root_cause_confidence * weights["root_cause"]
        )
    
    @property
    def is_ready(self) -> bool:
        """Check if the orchestrator is ready to process requests."""
        return self._initialized


_orchestrator: Optional[TroubleshootingOrchestrator] = None


async def get_orchestrator() -> TroubleshootingOrchestrator:
    """Get or create the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TroubleshootingOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator
