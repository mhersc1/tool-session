# app.py
from infrastructure.adapters.docx_generator import DocxTemplateGeneratorAdapter
from infrastructure.adapters.agents import FormPreloadAgentAdapter
from application.services import SessionDocumentService
from infrastructure.adapters.streamlit_ui import render_ui

def main():
    # 1. Instantiate the infrastructure driven adapter
    docx_adapter = DocxTemplateGeneratorAdapter()
    preload_agent = FormPreloadAgentAdapter()
    # 2. Inject it into the application use-case layer
    document_service = SessionDocumentService(
        doc_generator=docx_adapter, 
        template_path="plantilla_maestra.docx",
        preload_agent=preload_agent
    )
    
    # 3. Render the UI without preloading (user will trigger agent via button)
    render_ui(use_case=document_service, initial_context=None)

if __name__ == "__main__":
    main()