from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime



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
