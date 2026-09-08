from pydantic import BaseModel
from typing import List, Tuple, Optional, Any
from datetime import datetime

class Detection(BaseModel):
    track_id: int
    class_name: str
    confidence: float
    bounding_box: Tuple[int, int, int, int] # x1, y1, x2, y2

class FaceQuality(BaseModel):
    width: int
    height: int
    blur_score: float
    brightness: float
    pose: Optional[str] = None
    occlusion: Optional[str] = None
    meets_threshold: bool

class FacialExpression(BaseModel):
    label: str
    confidence: float

class FaceDetection(BaseModel):
    face_id: str
    track_id: Optional[int]
    bbox: Tuple[int, int, int, int]
    landmarks: Optional[List[Tuple[int, int]]] = None
    confidence: float
    quality: FaceQuality
    expression: Optional[FacialExpression] = None
    recognition: Optional[Any] = None # Will be populated with FaceRecognitionResult in the pipeline

class AIFrameResult(BaseModel):
    camera_id: str
    timestamp: datetime
    frame_number: int
    persons: int
    detections: List[Detection]
    faces: List[FaceDetection] = []
