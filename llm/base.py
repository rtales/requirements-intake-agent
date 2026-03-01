from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResult:
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_estimate: float = 0.0

class LLMProvider(ABC):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str, *, max_tokens: int, temperature: float) -> LLMResult:
        raise NotImplementedError
