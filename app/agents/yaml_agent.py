from typing import Any, Dict, List

import yaml

from app.agents.base_agent import BaseAgent
from app.config import get_logger
from app.schemas.models import Misconfiguration, Severity, YAMLValidationResult

logger = get_logger(__name__)


class YAMLValidationInput:
    """Input data for the YAML Validation Agent."""
    
    def __init__(self, deployment_yaml: str):
        self.deployment_yaml = deployment_yaml
        self.parsed_yaml: Dict[str, Any] | None = None
        self.parse_error: str | None = None
        
        try:
            self.parsed_yaml = yaml.safe_load(deployment_yaml)
        except yaml.YAMLError as e:
            self.parse_error = str(e)


class YAMLValidationAgent(BaseAgent[YAMLValidationInput, YAMLValidationResult]):
    """Agent responsible for validating Kubernetes deployment YAML configurations."""
    
    @property
    def name(self) -> str:
        return "YAMLValidationAgent"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert Kubernetes YAML configuration validator. Your task is to analyze deployment YAML files and identify misconfigurations, best practice violations, and potential issues.

You must return a JSON response with the following structure:
{
    "is_valid": <boolean - true if YAML is syntactically valid>,
    "misconfigurations": [
        {
            "issue": "<description of the issue>",
            "severity": "<one of: critical, high, medium, low, info>",
            "recommendation": "<how to fix the issue>",
            "field_path": "<path to the field, e.g., spec.containers[0].resources>"
        }
    ],
    "confidence": <float between 0.0 and 1.0>
}

Check for these common issues:
1. **Critical Issues:**
   - Missing resource limits/requests
   - Running as root without necessity
   - Privileged containers
   - Missing security context
   - Invalid image references

2. **High Severity:**
   - Missing liveness/readiness probes
   - No pod disruption budget considerations
   - Hardcoded secrets in env vars
   - Missing namespace specification

3. **Medium Severity:**
   - No resource quotas
   - Missing labels/annotations
   - Deprecated API versions
   - Suboptimal replica counts

4. **Low/Info:**
   - Missing comments/documentation
   - Non-standard naming conventions
   - Optional best practices

Always respond with valid JSON only."""
    
    def build_user_prompt(self, input_data: YAMLValidationInput) -> str:
        if input_data.parse_error:
            return f"""The following YAML failed to parse with error: {input_data.parse_error}

Original YAML:
```yaml
{input_data.deployment_yaml}
```

Identify the syntax error and any other issues you can detect from the raw YAML."""
        
        return f"""Analyze the following Kubernetes deployment YAML for misconfigurations and best practice violations.

```yaml
{input_data.deployment_yaml}
```

Provide your analysis as a JSON object."""
    
    def parse_response(self, response: str) -> YAMLValidationResult:
        data = self._extract_json(response)
        
        misconfigurations: List[Misconfiguration] = []
        for item in data.get("misconfigurations", []):
            severity = self._map_severity(item.get("severity", "medium"))
            misconfigurations.append(
                Misconfiguration(
                    issue=item.get("issue", "Unknown issue"),
                    severity=severity,
                    recommendation=item.get("recommendation", "Review configuration"),
                    field_path=item.get("field_path")
                )
            )
        
        return YAMLValidationResult(
            is_valid=data.get("is_valid", True),
            misconfigurations=misconfigurations,
            confidence=float(data.get("confidence", 0.5))
        )
    
    def _map_severity(self, severity: str) -> Severity:
        """Map string severity to Severity enum."""
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
        }
        return severity_map.get(severity.lower(), Severity.MEDIUM)
