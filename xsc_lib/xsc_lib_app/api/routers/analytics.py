from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from xsc_lib.xsc_lib_common import database
from xsc_lib.xsc_lib_app.api.dependencies import get_dev_account_id
from xsc_lib.xsc_lib_app.camera.service import CameraService
from xsc_lib.xsc_lib_common.models.analytics import (
    OccupancyResponse, PeopleAnalyticsResponse, EntryEvent, 
    DwellAnalyticsResponse, AdvancedSceneAnalyticsResponse
)
from datetime import datetime

# We import the global AI pipeline which holds the analytics engine
from xsc_lib.xsc_lib_app.api.routers.cameras import ai_pipeline

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

def get_camera_service(db: Session = Depends(database.get_db), account_id: str = Depends(get_dev_account_id)) -> CameraService:
    return CameraService(db, account_id)

async def verify_camera(camera_id: str, service: CameraService):
    cam = await service.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found or not authorized")

@router.get("/occupancy", response_model=OccupancyResponse)
async def get_occupancy(camera_id: str, session_id: str, service: CameraService = Depends(get_camera_service)):
    await verify_camera(camera_id, service)
    return ai_pipeline.analytics_engine.get_occupancy(camera_id, session_id)

@router.get("/people", response_model=PeopleAnalyticsResponse)
async def get_people(camera_id: str, session_id: str, service: CameraService = Depends(get_camera_service)):
    await verify_camera(camera_id, service)
    return ai_pipeline.analytics_engine.get_people(camera_id, session_id)

@router.get("/entries", response_model=List[EntryEvent])
async def get_entries(camera_id: str, session_id: str, service: CameraService = Depends(get_camera_service)):
    await verify_camera(camera_id, service)
    state = ai_pipeline.analytics_engine.get_state(camera_id, session_id)
    if state:
        return state.entry_events
    return []

@router.get("/dwell", response_model=DwellAnalyticsResponse)
async def get_dwell(camera_id: str, session_id: str, service: CameraService = Depends(get_camera_service)):
    await verify_camera(camera_id, service)
    return ai_pipeline.analytics_engine.get_dwell(camera_id, session_id)

@router.get("/scene", response_model=AdvancedSceneAnalyticsResponse)
async def get_scene_analytics(camera_id: str, session_id: str, service: CameraService = Depends(get_camera_service)):
    await verify_camera(camera_id, service)
    state = ai_pipeline.analytics_engine.get_state(camera_id, session_id)
    if not state:
        return AdvancedSceneAnalyticsResponse(
            camera_id=camera_id,
            session_id=session_id,
            timestamp=datetime.utcnow()
        )
        
    return ai_pipeline.analytics_engine.activity_engine.process_advanced_analytics(state, datetime.utcnow())
