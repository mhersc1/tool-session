# infrastructure/adapters/agents.py
import os
from typing import List

from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from diskcache import Cache

from application.ports.outbound import FormPreloadAgentPort
from domain.models import (
    GeneralData,
    SessionContext,
    SessionPurposeRow,
    SubtopicRow,
    TopicDetail,
    TransversalFocusRow,
)

SYSTEM_PROMPT = """Eres un asistente pedagógico especializado en el currículo peruano.
Tu tarea es generar el contenido completo de una sesión de aprendizaje para un docente,
a partir de los temas que te proporcione el usuario.

Debes completar todos los campos del formulario de sesión:
- proposito: Si el área seleccionada por el usuario es "Educación Cívica" el documento a considerar es el pce-civica.md, caso contrario considerar el documento pce-ccss.md.
  Ya teniendo seleccionado el documento, escoger al menos una fila con una competencia, sus capacidades 
  y desempeños los cuales tienen que estar alineados a los temas de la sesión y al nivel educativo especificados por el usuario. 
  Para la parte de desempeños, dar ejemplos claros y concisos tomando como referencia los desempeños y el nivel de grado definidos en el propio documento.
- enfoques: De acuerdo a lo especificado en el documento cneb.md escoger al menos dos enfoques transversales 
  que estén vinculadas a los temas de la sesión especificadas por el usuario, cuyas columnas sean: "Enfoque Transversal" y "Acciones Observables". 
  Para la parte de "Acciones Observables", dar ejemplos claros y concisos tomando como referencia los valores y actitudes definidos en el propio documento.
- temas: cada tema proporcionado por el usuario debe tener sus actividades de inicio, subtemas con resúmenes,
  cierre reflexivo y tarea de extensión.

Escribe todo el contenido en español, con lenguaje claro y apropiado para el nivel indicado.
Los resúmenes de subtemas pueden incluir viñetas cuando sea útil."""

####### Load main functions #######
load_dotenv()
cache = Cache(".cache_dir")

class GeneralDataSchema(BaseModel):
    colegio: str = Field(description="Nombre del colegio o institución educativa.")
    area: str = Field(description="Área curricular, por ejemplo Historia, Geografía o Economía.")
    nivel: str = Field(description="Nivel educativo: Primaria o Secundaria.")
    grado: str = Field(description="Grado escolar, por ejemplo 1º, 2º o 3º.")
    seccion: str = Field(description="Sección del aula, por ejemplo Única o A.")
    docente: str = Field(description="Nombre del docente responsable de la sesión.")
    mes: str = Field(description="Mes en que se dicta la sesión.")


class SessionPurposeRowSchema(BaseModel):
    competencia: str = Field(description="Competencias curriculares de la sesión.")
    capacidades: List[str] = Field(
        description="Capacidades asociadas a las competencias.",
        min_length=1)
    desempenos: List[str] = Field(
        description="Desempeños observables esperados del estudiante.",
        min_length=1)

class TransversalFocusRowSchema(BaseModel):
    enfoque: str = Field(description="Nombre del enfoque transversal.")
    acciones: str = Field(description="Acciones observables relacionadas con el enfoque y el tema.")


class SubtopicRowSchema(BaseModel):
    subtema: str = Field(description="Nombre del subtema dentro del tema principal.")
    resumen: str = Field(description="Resumen o desarrollo del subtema; puede usar viñetas.")


class TopicDetailSchema(BaseModel):
    titulo: str = Field(description="Título del tema de la sesión.")
    inicio: str = Field(description="Actividades de inicio o motivación de la sesión.")
    subtemas: List[SubtopicRowSchema] = Field(
        description="Lista de subtemas con su contenido resumido.",
        min_length=6,
        max_length=12
    )
    cierre: str = Field(
        description="Preguntas o actividades de cierre reflexivo.",
        default="¿Qué aprendimos?, ¿Cómo lo aprendimos?",
    )
    tarea: str = Field(description="Tarea o actividad de extensión para el hogar.")


class SessionContextSchema(BaseModel):
    datos_generales: GeneralDataSchema
    proposito: List[SessionPurposeRowSchema] = Field(min_length=1)
    enfoques: List[TransversalFocusRowSchema] = Field(min_length=2, max_length=3)
    temas: List[TopicDetailSchema] = Field(min_length=1, max_length=10)
    valor: str = Field(description="Valor educativo de la sesión.")


def _to_domain(schema: SessionContextSchema) -> SessionContext:
    sessionContext =  SessionContext(
        datos_generales=GeneralData(**schema.datos_generales.model_dump()),
        proposito=[
            SessionPurposeRow(**row.model_dump())
            for row in schema.proposito
        ],
        enfoques=[
            TransversalFocusRow(**row.model_dump())
            for row in schema.enfoques
        ],
        temas=[
            TopicDetail(
                titulo=tema.titulo,
                inicio=tema.inicio,
                subtemas=[
                    SubtopicRow(**sub.model_dump())
                    for sub in tema.subtemas
                ],
                cierre=tema.cierre,
                tarea=tema.tarea,
            )
            for tema in schema.temas
        ],
        valor = schema.valor
    )
    return sessionContext


class FormPreloadAgentAdapter(FormPreloadAgentPort):
    def __init__(
        self,
        model: str = "globant_dgx/GLM-4.6",#"gpt-4o-mini"
        client: OpenAI | None = None,
    ) -> None:
        api_base = "https://api.clients.globant.com"
        api_key = os.getenv("GEAI_API_KEY")
        if client is None and not api_key:
            raise ValueError(
                "OPENAI_API_KEY no está configurada. "
                "Define la variable de entorno antes de usar el agente."
            )
        self._client = client or OpenAI(api_key=api_key, base_url=api_base)
        self._model = model

    def preload(self, prompt: str) -> SessionContext:
        # Check disk cache first
        if prompt in cache:
            return cache[prompt]        
        completion = self._client.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format=SessionContextSchema,
        )

        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("El agente no devolvió un SessionContext válido.")
        result = _to_domain(parsed)

        # Store in disk cache (optionally set expire time in seconds)
        cache.set(prompt, result, expire=86400)  # Caches for 24 hours
        return result
