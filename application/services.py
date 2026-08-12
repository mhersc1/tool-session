# application/services.py
from application.ports.inbound import GenerateDocumentUseCase
from application.ports.outbound import DocumentGeneratorPort
from application.ports.outbound import FormPreloadAgentPort
from domain.models import SessionContext

class SessionDocumentService(GenerateDocumentUseCase):
    def __init__(self, doc_generator: DocumentGeneratorPort, template_path: str, preload_agent: FormPreloadAgentPort):
        self.doc_generator = doc_generator
        self.template_path = template_path
        self.preload_agent = preload_agent

    def execute(self, context: SessionContext, output_path: str) -> None:
        # Core application logic / validation
        self.doc_generator.generate(context, self.template_path, output_path)

    def preload(self, prompt: str) -> SessionContext:
        return self.preload_agent.preload(prompt)