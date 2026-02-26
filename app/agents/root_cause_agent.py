from dataclasses import dataclass
from typing import List

from app.agents.base_agent import BaseAgent
from app.config import get_logger
from app.schemas.models import LogAnalysisResult, RootCauseResult, YAMLValidationResult

logger = get_logger(__name__)


@dataclass
class RootCauseInput:
    """Input data for the Root Cause Agent."""
    log_analysis: LogAnalysisResult
    yaml_validation: YAMLValidationResult
    rag_context: List[str]


class RootCauseAgent(BaseAgent[RootCauseInput, RootCauseResult]):
    """Agent responsible for synthesizing findings and determining root cause."""
    
    @property
    def name(self) -> str:
        return "RootCauseAgent"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert Kubernetes troubleshooting agent. Your task is to synthesize analysis from log analysis, YAML validation, and relevant documentation to determine the root cause of issues and provide actionable fix steps.

You will receive:
1. Log analysis results with error category and probable cause
2. YAML validation results with misconfigurations
3. Relevant Kubernetes documentation context

You must return a JSON response with the following structure:
{
    "root_cause": "<concise statement of the root cause>",
    "explanation": "<detailed explanation of why this is happening>",
    "fix_steps": [
        "<step 1>",
        "<step 2>",
        ...
    ],
    "kubectl_commands": [
        "<kubectl command 1>",
        "<kubectl command 2>",
        ...
    ],
    "confidence": <float between 0.0 and 1.0>
}

Guidelines:
1. Correlate findings from both log analysis and YAML validation
2. Prioritize issues by severity - address critical issues first
3. Provide specific, actionable fix steps
4. Include relevant kubectl commands that can help diagnose or fix the issue
5. Use the documentation context to ensure accuracy
6. If log analysis and YAML validation point to different issues, determine which is the primary cause
7. Calculate confidence based on:
   - Agreement between log and YAML analysis
   - Clarity of error indicators
   - Relevance of documentation context

Common kubectl commands to consider:
- kubectl get events --field-selector involvedObject.name=<pod>
- kubectl describe pod <pod>
- kubectl logs <pod> --previous
- kubectl rollout restart deployment/<name>
- kubectl apply -f <fixed-yaml>
- kubectl delete pod <pod> --grace-period=0 --force
- kubectl scale deployment/<name> --replicas=0 && kubectl scale deployment/<name> --replicas=<n>

Always respond with valid JSON only."""
    
    def build_user_prompt(self, input_data: RootCauseInput) -> str:
        log_analysis_str = f"""
Error Category: {input_data.log_analysis.error_category.value}
Probable Cause: {input_data.log_analysis.probable_cause}
Supporting Log Lines:
{chr(10).join('- ' + line for line in input_data.log_analysis.supporting_log_lines)}
Confidence: {input_data.log_analysis.confidence}
"""
        
        yaml_issues_str = ""
        for misc in input_data.yaml_validation.misconfigurations:
            yaml_issues_str += f"""
- Issue: {misc.issue}
  Severity: {misc.severity.value}
  Recommendation: {misc.recommendation}
  Field: {misc.field_path or 'N/A'}
"""
        
        if not yaml_issues_str:
            yaml_issues_str = "No misconfigurations found."
        
        rag_context_str = "\n\n".join(input_data.rag_context) if input_data.rag_context else "No relevant documentation found."
        
        return f"""Synthesize the following analysis results to determine the root cause and provide fix steps.

## Log Analysis Results:
{log_analysis_str}

## YAML Validation Results:
Valid YAML: {input_data.yaml_validation.is_valid}
Misconfigurations:
{yaml_issues_str}
Confidence: {input_data.yaml_validation.confidence}

## Relevant Kubernetes Documentation:
{rag_context_str}

Based on all the above information, determine the root cause and provide actionable fix steps with kubectl commands."""
    
    def parse_response(self, response: str) -> RootCauseResult:
        data = self._extract_json(response)
        
        return RootCauseResult(
            root_cause=data.get("root_cause", "Unable to determine root cause"),
            explanation=data.get("explanation", ""),
            fix_steps=data.get("fix_steps", []),
            kubectl_commands=data.get("kubectl_commands", []),
            confidence=float(data.get("confidence", 0.5))
        )
