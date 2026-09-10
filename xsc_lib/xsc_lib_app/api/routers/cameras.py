from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from xsc_lib.xsc_lib_common import database
from xsc_lib.xsc_lib_app.api.dependencies import get_dev_account_id
from xsc_lib.xsc_lib_app.camera.service import CameraService
from xsc_lib.xsc_lib_common.models.camera import Camera, CameraEvent

from xsc_lib.xsc_lib_app.ai.pipeline import VideoAIPipeline
from xsc_lib.xsc_lib_common.models.ai import AIFrameResult

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])

# Global AI pipeline for live frame analysis
ai_pipeline = VideoAIPipeline()

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

@router.post("/{camera_id}/analyze-frame", response_model=AIFrameResult)
async def analyze_frame(
    camera_id: str,
    session_id: str = Form(...),
    file: UploadFile = File(...),
    service: CameraService = Depends(get_camera_service)
):
    # Verify camera exists (isolation)
    cam = await service.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=415, detail="Unsupported media type")
        
    frame_bytes = await file.read()
    if len(frame_bytes) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Frame size exceeds 2MB limit")
        
    try:
        # Run inference synchronously for MVP (bounded by frontend request pacing)
        result = ai_pipeline.process_frame(camera_id, session_id, frame_bytes)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{camera_id}/live/{session_id:path}")
async def stop_live_stream(camera_id: str, session_id: str, ai_session_id: str = None, service: CameraService = Depends(get_camera_service)):
    # session_id might contain slashes if it's passed as a full URL path (like in Ring).
    # Using {session_id:path} allows capturing it correctly.
    cam = await service.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    # Clean up AI session tracking state
    if ai_session_id:
        ai_pipeline.cleanup_session(camera_id, ai_session_id)
        
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
