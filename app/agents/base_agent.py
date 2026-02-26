import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

from openai import AsyncOpenAI

from app.config import Settings, get_logger, get_settings

logger = get_logger(__name__)

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all agents in the system."""
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_model
        self.max_tokens = self.settings.openai_max_tokens
        self.temperature = self.settings.openai_temperature
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging and identification."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining the agent's role and behavior."""
        pass
    
    @abstractmethod
    def build_user_prompt(self, input_data: InputT) -> str:
        """Build the user prompt from input data."""
        pass
    
    @abstractmethod
    def parse_response(self, response: str) -> OutputT:
        """Parse the LLM response into the expected output type."""
        pass
    
    async def execute(self, input_data: InputT) -> OutputT:
        """Execute the agent's task."""
        logger.info(f"Agent '{self.name}' starting execution")
        
        try:
            user_prompt = self.build_user_prompt(input_data)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logger.debug(f"Agent '{self.name}' raw response: {raw_response}")
            
            result = self.parse_response(raw_response)
            logger.info(f"Agent '{self.name}' completed successfully")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Agent '{self.name}' failed to parse JSON response: {e}")
            raise ValueError(f"Failed to parse agent response as JSON: {e}")
        except Exception as e:
            logger.error(f"Agent '{self.name}' execution failed: {e}")
            raise
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text, handling potential markdown code blocks."""
        text = text.strip()
        
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)
        
        return json.loads(text)
