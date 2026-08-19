from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

# XCEL Normalized Event Model
class XcelEvent(BaseModel):
    event_id: str
    provider: str = "ring"
    camera_id: str
    event_type: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=datetime.utcnow)

# XCEL Normalized Camera Model
class XcelCamera(BaseModel):
    id: str
    provider: str = "ring"
    provider_device_id: str
    name: str
    location: Optional[str] = None
    status: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Ring-specific Models (for internal use)
class RingDevice(BaseModel):
    id: str
    name: str
    location_id: Optional[str] = None
    status: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)

class RingWebhookPayload(BaseModel):
    event_id: str
    device_id: str
    event_type: str
    created_at: str
    # Depending on the actual Ring payload, this can be expanded
    details: Dict[str, Any] = Field(default_factory=dict)
