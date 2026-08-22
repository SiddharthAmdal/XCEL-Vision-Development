from fastapi import APIRouter, HTTPException
from typing import Optional
from ai.analytics.models import BehavioralResponse, TrackBehavior
from api.routers.cameras import ai_pipeline
from datetime import datetime

router = APIRouter(prefix="/api/v1/behavior", tags=["behavior"])

@router.get("", response_model=BehavioralResponse)
async def get_behavioral_indicators(
    camera_id: str,
    session_id: str,
    track_id: Optional[int] = None
):
    state = ai_pipeline.analytics_engine.get_state(camera_id, session_id)
    if not state:
        return BehavioralResponse(
            camera_id=camera_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            tracks=[]
        )
        
    now = datetime.utcnow()
    track_behaviors = []
    for tid, track in state.active_tracks.items():
        if track_id is not None and tid != track_id:
            continue
            
        is_active = (now - track.last_seen).total_seconds() < 2.0
        track_behaviors.append(TrackBehavior(
            track_id=tid,
            indicators=track.affective_indicators,
            is_active=is_active
        ))
        
    return BehavioralResponse(
        camera_id=camera_id,
        session_id=session_id,
        timestamp=datetime.utcnow(),
        tracks=track_behaviors
    )
