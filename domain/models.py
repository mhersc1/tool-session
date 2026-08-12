# domain/models.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class GeneralData:
    colegio: str
    area: str
    nivel: str
    grado: str
    seccion: str
    docente: str
    mes: str

@dataclass
class SessionPurposeRow:
    competencia: str
    capacidades: List[str]
    desempenos: List[str]

@dataclass
class TransversalFocusRow:
    enfoque: str
    acciones: str

@dataclass
class SubtopicRow:
    subtema: str
    resumen: str

@dataclass
class TopicDetail:
    titulo: str
    inicio: str
    subtemas: List[SubtopicRow]
    cierre: str
    tarea: str

@dataclass
class SessionContext:
    datos_generales: GeneralData
    proposito: List[SessionPurposeRow]
    enfoques: List[TransversalFocusRow]
    temas: List[TopicDetail]
    valor: str