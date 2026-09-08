from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RecognitionStatus(str, Enum):
    MATCHED = "MATCHED"
    UNKNOWN = "UNKNOWN"
    LOW_QUALITY = "LOW_QUALITY"
    NO_FACE = "NO_FACE"
    MULTIPLE_FACE = "MULTIPLE_FACE"

class FaceRecognitionResult(BaseModel):
    status: RecognitionStatus
    person_id: Optional[str] = None
    display_name: Optional[str] = None
    similarity: Optional[float] = None
    confidence: Optional[float] = None
    model_version: Optional[str] = None

class FaceTemplate(BaseModel):
    template_id: str
    person_id: str
    embedding: List[float]
    model_version: str
    quality_score: float
    created_at: datetime
    updated_at: datetime
    revoked_at: Optional[datetime] = None

class Person(BaseModel):
    person_id: str
    employee_id: Optional[str] = None
    name: str
    department: Optional[str] = None
    status: str
    consent_status: str
    templates: List[FaceTemplate] = []
