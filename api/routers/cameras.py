from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

import database
from api.dependencies import get_dev_account_id
from camera.service import CameraService
from camera.models import Camera, CameraEvent

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])

def get_camera_service(db: Session = Depends(database.get_db), account_id: str = Depends(get_dev_account_id)) -> CameraService:
    return CameraService(db, account_id)

class LiveStreamRequest(BaseModel):
    sdp_offer: str

@router.get("", response_model=List[Camera])
async def list_cameras(service: CameraService = Depends(get_camera_service)):
    return await service.get_cameras()

@router.get("/{camera_id}", response_model=Camera)
async def get_camera(camera_id: str, service: CameraService = Depends(get_camera_service)):
    cam = await service.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam

@router.get("/{camera_id}/capabilities", response_model=Dict[str, Any])
async def get_capabilities(camera_id: str, service: CameraService = Depends(get_camera_service)):
    caps = await service.get_capabilities(camera_id)
    if not caps:
        # Check if camera actually exists
        cam = await service.get_camera(camera_id)
        if not cam:
            raise HTTPException(status_code=404, detail="Camera not found")
    return caps

@router.post("/{camera_id}/live")
async def start_live_stream(camera_id: str, request: LiveStreamRequest, service: CameraService = Depends(get_camera_service)):
    if not request.sdp_offer:
        raise HTTPException(status_code=400, detail="sdp_offer is required")
        
    cam = await service.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    res = await service.start_live_stream(camera_id, request.sdp_offer)
    if res.get("status") == "success":
        return res
    else:
        raise HTTPException(status_code=res.get("code", 500), detail=res.get("message", "Failed to start live stream"))

@router.delete("/{camera_id}/live/{session_id:path}")
async def stop_live_stream(camera_id: str, session_id: str, service: CameraService = Depends(get_camera_service)):
    # session_id might contain slashes if it's passed as a full URL path (like in Ring).
    # Using {session_id:path} allows capturing it correctly.
    cam = await service.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    res = await service.stop_live_stream(camera_id, session_id)
    if res.get("status") == "success":
        return {"status": "success"}
    else:
        raise HTTPException(status_code=res.get("code", 500), detail="Failed to stop live stream")

@router.get("/{camera_id}/events", response_model=List[CameraEvent])
async def get_events(camera_id: str, service: CameraService = Depends(get_camera_service)):
    cam = await service.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    events = await service.get_events(camera_id)
    return events
