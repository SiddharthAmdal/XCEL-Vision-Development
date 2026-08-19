from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import database
from .models import Camera, CameraEvent
from .provider import CameraProvider
from ring.provider import RingCameraProvider

class CameraService:
    """
    Service layer to manage camera operations decoupled from REST controllers.
    """
    def __init__(self, db: Session, account_id: str):
        self.db = db
        self.account_id = account_id
        # For MVP, we directly resolve to RingCameraProvider.
        # Future architecture can resolve based on account mapping or provider flags.
        self._provider = RingCameraProvider(db=self.db, account_id=self.account_id)

    @property
    def provider(self) -> CameraProvider:
        return self._provider

    async def get_cameras(self) -> List[Camera]:
        return await self.provider.get_devices()

    async def get_camera(self, camera_id: str) -> Optional[Camera]:
        return await self.provider.get_device(external_id=camera_id)

    async def get_capabilities(self, camera_id: str) -> Dict[str, Any]:
        return await self.provider.get_capabilities(external_id=camera_id)

    async def start_live_stream(self, camera_id: str, sdp_offer: str) -> dict:
        return await self.provider.start_live_stream(external_id=camera_id, sdp_offer=sdp_offer)

    async def stop_live_stream(self, camera_id: str, session_id: str) -> dict:
        return await self.provider.stop_live_stream(external_id=camera_id, session_id=session_id)

    async def get_events(self, camera_id: str, **kwargs) -> List[CameraEvent]:
        return await self.provider.get_events(external_id=camera_id, **kwargs)
