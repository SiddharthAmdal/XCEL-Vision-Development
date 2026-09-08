from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class Camera(BaseModel):
    camera_id: str
    provider: str
    external_id: str
    name: str
    location: Optional[str] = None
    status: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    last_event: Optional[Dict[str, Any]] = None

class CameraEvent(BaseModel):
    event_id: str
    provider: str
    camera_id: str
    event_type: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=datetime.utcnow)
