from pydantic import BaseModel
from typing import List, Tuple
from datetime import datetime

class Detection(BaseModel):
    track_id: int
    class_name: str
    confidence: float
    bounding_box: Tuple[int, int, int, int] # x1, y1, x2, y2

class AIFrameResult(BaseModel):
    camera_id: str
    timestamp: datetime
    frame_number: int
    persons: int
    detections: List[Detection]
