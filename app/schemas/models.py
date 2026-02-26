from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    """Categories of Kubernetes errors."""
    IMAGE_PULL = "ImagePullError"
    CRASH_LOOP = "CrashLoopBackOff"
    OOM_KILLED = "OOMKilled"
    RESOURCE_QUOTA = "ResourceQuotaExceeded"
    CONFIG_ERROR = "ConfigurationError"
    NETWORK_ERROR = "NetworkError"
    VOLUME_ERROR = "VolumeError"
    PERMISSION_ERROR = "PermissionError"
    PROBE_FAILURE = "ProbeFailure"
    SCHEDULING_ERROR = "SchedulingError"
    UNKNOWN = "Unknown"


class Severity(str, Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Request Models
class AnalyzeRequest(BaseModel):
    """Request model for the /analyze endpoint."""
    describe_output: str = Field(
        ...,
        description="Output from 'kubectl describe pod' command",
        min_length=1
    )
    pod_logs: str = Field(
        ...,
        description="Pod logs from 'kubectl logs' command",
        min_length=1
    )
    deployment_yaml: str = Field(
        ...,
        description="Deployment YAML configuration",
        min_length=1
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "describe_output": "Name: my-pod\nNamespace: default\nStatus: CrashLoopBackOff...",
                    "pod_logs": "Error: connection refused to database...",
                    "deployment_yaml": "apiVersion: apps/v1\nkind: Deployment..."
                }
            ]
        }
    }


# Agent Output Models
class LogAnalysisResult(BaseModel):
    """Output from the Log Analysis Agent."""
    error_category: ErrorCategory = Field(
        ...,
        description="Categorized error type"
    )
    probable_cause: str = Field(
        ...,
        description="Most likely cause of the error"
    )
    supporting_log_lines: List[str] = Field(
        default_factory=list,
        description="Relevant log lines supporting the analysis"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )


class Misconfiguration(BaseModel):
    """A single misconfiguration found in YAML."""
    issue: str = Field(
        ...,
        description="Description of the misconfiguration"
    )
    severity: Severity = Field(
        ...,
        description="Severity level of the issue"
    )
    recommendation: str = Field(
        ...,
        description="Recommended fix for the issue"
    )
    field_path: Optional[str] = Field(
        default=None,
        description="Path to the misconfigured field in YAML"
    )


class YAMLValidationResult(BaseModel):
    """Output from the YAML Validation Agent."""
    is_valid: bool = Field(
        ...,
        description="Whether the YAML is syntactically valid"
    )
    misconfigurations: List[Misconfiguration] = Field(
        default_factory=list,
        description="List of found misconfigurations"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )


class RootCauseResult(BaseModel):
    """Output from the Root Cause Agent."""
    root_cause: str = Field(
        ...,
        description="Identified root cause of the issue"
    )
    explanation: str = Field(
        ...,
        description="Detailed explanation of the root cause"
    )
    fix_steps: List[str] = Field(
        ...,
        description="Step-by-step instructions to fix the issue"
    )
    kubectl_commands: List[str] = Field(
        default_factory=list,
        description="Suggested kubectl commands to apply the fix"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Aggregated confidence score"
    )


# Response Models
class AnalyzeResponse(BaseModel):
    """Complete response from the /analyze endpoint."""
    error_category: ErrorCategory = Field(
        ...,
        description="Categorized error type"
    )
    root_cause: str = Field(
        ...,
        description="Identified root cause"
    )
    explanation: str = Field(
        ...,
        description="Detailed explanation"
    )
    fix_steps: List[str] = Field(
        ...,
        description="Steps to fix the issue"
    )
    kubectl_commands: List[str] = Field(
        ...,
        description="Suggested kubectl commands"
    )
    log_analysis: LogAnalysisResult = Field(
        ...,
        description="Detailed log analysis results"
    )
    yaml_validation: YAMLValidationResult = Field(
        ...,
        description="YAML validation results"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score"
    )
    rag_context_used: List[str] = Field(
        default_factory=list,
        description="RAG documentation chunks used for analysis"
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(default="healthy")
    version: str
    openai_configured: bool
    vector_store_ready: bool


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")
