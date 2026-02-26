from typing import Dict

from app.agents.base_agent import BaseAgent
from app.config import get_logger
from app.schemas.models import ErrorCategory, LogAnalysisResult

logger = get_logger(__name__)


class LogAnalysisInput:
    """Input data for the Log Analysis Agent."""
    
    def __init__(self, describe_output: str, pod_logs: str):
        self.describe_output = describe_output
        self.pod_logs = pod_logs


class LogAnalysisAgent(BaseAgent[LogAnalysisInput, LogAnalysisResult]):
    """Agent responsible for analyzing Kubernetes pod logs and describe output."""
    
    @property
    def name(self) -> str:
        return "LogAnalysisAgent"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert Kubernetes log analysis agent. Your task is to analyze pod logs and kubectl describe output to identify errors and their probable causes.

You must analyze the provided information and return a JSON response with the following structure:
{
    "error_category": "<one of: ImagePullError, CrashLoopBackOff, OOMKilled, ResourceQuotaExceeded, ConfigurationError, NetworkError, VolumeError, PermissionError, ProbeFailure, SchedulingError, Unknown>",
    "probable_cause": "<concise description of the most likely cause>",
    "supporting_log_lines": ["<relevant log line 1>", "<relevant log line 2>", ...],
    "confidence": <float between 0.0 and 1.0>
}

Guidelines:
1. Focus on error patterns, stack traces, and warning messages
2. Look for common Kubernetes issues:
   - ImagePullBackOff / ErrImagePull: Image not found, registry auth issues
   - CrashLoopBackOff: Application crashes, missing dependencies, config errors
   - OOMKilled: Memory limit exceeded
   - Pending pods: Resource constraints, node selector issues
   - Probe failures: Liveness/readiness probe misconfigurations
3. Extract the most relevant log lines that support your analysis
4. Set confidence based on how clear the error indicators are
5. If multiple issues exist, focus on the primary/root issue

Always respond with valid JSON only."""
    
    def build_user_prompt(self, input_data: LogAnalysisInput) -> str:
        return f"""Analyze the following Kubernetes pod information and logs to identify the error and its cause.

## kubectl describe pod output:
```
{input_data.describe_output}
```

## Pod logs:
```
{input_data.pod_logs}
```

Provide your analysis as a JSON object."""
    
    def parse_response(self, response: str) -> LogAnalysisResult:
        data = self._extract_json(response)
        
        error_category = self._map_error_category(data.get("error_category", "Unknown"))
        
        return LogAnalysisResult(
            error_category=error_category,
            probable_cause=data.get("probable_cause", "Unable to determine cause"),
            supporting_log_lines=data.get("supporting_log_lines", []),
            confidence=float(data.get("confidence", 0.5))
        )
    
    def _map_error_category(self, category: str) -> ErrorCategory:
        """Map string category to ErrorCategory enum."""
        category_map: Dict[str, ErrorCategory] = {
            "ImagePullError": ErrorCategory.IMAGE_PULL,
            "ErrImagePull": ErrorCategory.IMAGE_PULL,
            "ImagePullBackOff": ErrorCategory.IMAGE_PULL,
            "CrashLoopBackOff": ErrorCategory.CRASH_LOOP,
            "OOMKilled": ErrorCategory.OOM_KILLED,
            "ResourceQuotaExceeded": ErrorCategory.RESOURCE_QUOTA,
            "ConfigurationError": ErrorCategory.CONFIG_ERROR,
            "NetworkError": ErrorCategory.NETWORK_ERROR,
            "VolumeError": ErrorCategory.VOLUME_ERROR,
            "PermissionError": ErrorCategory.PERMISSION_ERROR,
            "ProbeFailure": ErrorCategory.PROBE_FAILURE,
            "SchedulingError": ErrorCategory.SCHEDULING_ERROR,
        }
        return category_map.get(category, ErrorCategory.UNKNOWN)
