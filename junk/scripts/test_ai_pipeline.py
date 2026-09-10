import asyncio
import logging
import time
import httpx
from xsc_lib.xsc_lib_common.database import get_db, RingToken
from xsc_lib.xsc_lib_extn.ring.provider import RingCameraProvider
from xsc_lib.xsc_lib_app.ai.pipeline import VideoAIPipeline
import os
from xsc_lib.xsc_lib_app.api.routers.cameras import analyze_frame
import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_ai_pipeline():
    db = next(get_db())
    try:
        token = db.query(RingToken).filter_by(is_claimed=1).first()
        if not token:
            logger.error("No claimed token found.")
            return
            
        provider = RingCameraProvider(db, token.account_id)
        
        devices = await provider.get_devices()
        target = next((d for d in devices if d.name == "TS RING 01"), None)
        if not target:
            logger.error("Could not find TS RING 01")
            return
            
        history_res = await provider.get_events(target.camera_id)
        if not history_res:
            logger.error("No events found to download media from.")
            return
            
        # Try first event's timestamp, fallback if needed
        target_event = history_res[0]
        timestamp_ms = int(time.time() * 1000) - 60000 # recent timestamp
        
        video_path = "scratch_video_test.mp4"
        
        logger.info("Initializing AI Pipeline...")
        pipeline = VideoAIPipeline(target_fps=5)
        
        logger.info("Running AI Pipeline...")
        for result in pipeline.process_video(target.camera_id, video_path):
            logger.info(f"Frame {result.frame_number}: {result.persons} person(s) visible.")
            for det in result.detections:
                logger.info(f"  Track {det.track_id} (Conf: {det.confidence:.2f}) Box: {det.bounding_box}")
                
        logger.info("Finished running AI pipeline.")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_ai_pipeline())
