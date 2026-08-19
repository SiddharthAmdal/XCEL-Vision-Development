from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from .models import Camera, CameraEvent

class CameraProvider(ABC):
    """
    Provider-independent interface for camera operations.
    """
    
    @abstractmethod
    async def get_devices(self, force_refresh: bool = False) -> List[Camera]:
        """Fetch all cameras available to the provider."""
        pass

    @abstractmethod
    async def get_device(self, external_id: str) -> Optional[Camera]:
        """Fetch a specific camera's details."""
        pass

    @abstractmethod
    async def get_capabilities(self, external_id: str) -> Dict[str, Any]:
        """Fetch capabilities of a specific camera."""
        pass

    @abstractmethod
    async def start_live_stream(self, external_id: str, sdp_offer: str) -> dict:
        """
        Initiate a live stream session with the camera.
        Should return a dict containing at minimum {'status': 'success', 'sdp_answer': '...', 'session_id': '...'}
        """
        pass

    @abstractmethod
    async def stop_live_stream(self, external_id: str, session_id: str) -> dict:
        """Stop an active live stream session."""
        pass

    @abstractmethod
    async def get_events(self, external_id: str, **kwargs) -> List[CameraEvent]:
        """Retrieve historical events for a specific camera."""
        pass

    @abstractmethod
    async def get_media(self, external_id: str, event_id: str) -> dict:
        """
        Retrieve media associated with a specific event.
        Returns a dict containing media URLs or stream information.
        """
        pass
