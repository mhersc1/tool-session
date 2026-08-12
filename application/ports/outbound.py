# ports/outbound.py
from abc import ABC, abstractmethod
from domain.models import SessionContext

class DocumentGeneratorPort(ABC):
    """Outbound port to handle final file creation."""
    @abstractmethod
    def generate(self, context: SessionContext, template_path: str, output_path: str) -> None:
        pass

class FormPreloadAgentPort(ABC):
    """Outbound port to call an agent that fills the session form."""

    @abstractmethod
    def preload(self, prompt: str) -> SessionContext:
        pass