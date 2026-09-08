import asyncio
import time
import httpx
import logging
import os
from xsc_lib.xsc_lib_common.database import get_db, RingToken
from xsc_lib.xsc_lib_extn.ring.provider import RingCameraProvider
from xsc_lib.xsc_lib_app.ai.pipeline import VideoAIPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run():
    db = next(get_db())
    token = db.query(RingToken).filter_by(is_claimed=1).first()
    provider = RingCameraProvider(db, token.account_id)
    devices = await provider.get_devices()
    target = next((d for d in devices if d.name == "TS RING 01"), None)
    
    logger.info(f"Target Camera: {target.camera_id}")
    
    events = await provider.get_events(target.camera_id)
    if not events:
        logger.error("No events found.")
        return
        
    found_event = events[0]
    logger.info(f"Using newest event: {found_event.event_id}")
        
    logger.info("Fresh event found! Attempting to download MP4...")
    import datetime
    utc_ts = found_event.timestamp.replace(tzinfo=datetime.timezone.utc)
    ts_ms = int(utc_ts.timestamp() * 1000)
    
    vid_res = await provider.download_video(target.camera_id, timestamp=ts_ms)
    logger.info(f"Download response: {vid_res}")
    
    if vid_res.get("status") == "success":
        download_url = vid_res["download_url"]
        video_path = f"scratch_real_video_{found_event.event_id}.mp4"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Following redirect URL to fetch binary MP4...")
            vid_dl = await client.get(download_url)
            logger.info(f"HTTP GET -> {vid_dl.status_code}")
            if vid_dl.status_code == 200:
                with open(video_path, 'wb') as f:
                    f.write(vid_dl.content)
                logger.info(f"Saved real MP4 to {video_path}, size: {os.path.getsize(video_path)} bytes")
            else:
                logger.error(f"Failed to download bytes. Code {vid_dl.status_code}, body: {vid_dl.text}")
                return
                
        # Step 3: Run AI
        logger.info("Initializing AI Pipeline on real MP4...")
        pipeline = VideoAIPipeline(target_fps=5)
        
        frame_count = 0
        total_persons_detected = 0
        track_ids = set()
        
        for result in pipeline.process_video(target.camera_id, video_path):
            frame_count += 1
            if result.persons > 0:
                total_persons_detected = max(total_persons_detected, result.persons)
            
            logger.info(f"Frame {result.frame_number}: {result.persons} person(s) visible.")
            for det in result.detections:
                track_ids.add(det.track_id)
                logger.info(f"  Track {det.track_id} (Conf: {det.confidence:.2f}) Box: {det.bounding_box}")
                
        logger.info("--- AI EXECUTION SUMMARY ---")
        logger.info(f"Frames processed: {frame_count}")
        logger.info(f"Max visible persons in any frame: {total_persons_detected}")
        logger.info(f"Unique Track IDs: {track_ids}")
        logger.info("----------------------------")
                
        if os.path.exists(video_path):
            os.remove(video_path)
    else:
        logger.error("Media API returned an error or unsuccessful status.")
            
if __name__ == "__main__":
    asyncio.run(run())
