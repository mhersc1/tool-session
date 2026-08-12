# ports/inbound.py
from abc import ABC, abstractmethod
from domain.models import SessionContext

class GenerateDocumentUseCase(ABC):
    """Inbound port invoked by UI adapters."""
    @abstractmethod
    def execute(self, context: SessionContext, output_path: str) -> None:
        pass

    @abstractmethod
    def preload(self, prompt: str) -> SessionContext:
        pass