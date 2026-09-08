import asyncio
import logging
import httpx
from xsc_lib.xsc_lib_common import database
from xsc_lib.xsc_lib_common.database import SessionLocal
from xsc_lib.xsc_lib_extn.ring.provider import RingCameraProvider
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_media_tests():
    db = next(database.get_db())
    try:
        # Retrieve the first claimed token to get an account_id for testing
        token = db.query(database.RingToken).filter_by(is_claimed=1).first()
        if not token:
            logger.error("No claimed token found in database. Please link an account first.")
            return
            
        account_id = token.account_id
        provider = RingCameraProvider(db, account_id)
        
        logger.info("Fetching devices...")
        devices = await provider.get_devices()
        
        # Test TS RING 01
        target = next((d for d in devices if d.name == "TS RING 01"), None)
        if not target:
            logger.error("Could not find TS RING 01")
            return
            
        logger.info(f"--- Phase 2: Testing Event History for {target.camera_id} ---")
        history_res = await provider.get_event_history(target.camera_id)
        
        if history_res.get("status") == "success":
            events = history_res.get("events", [])
            logger.info(f"Event History Success! Count: {len(events)}")
            for idx, event in enumerate(events[:3]):
                logger.info(f"Event {idx}: ID={event.get('id')}, Type={event.get('attributes', {}).get('event_type')}, Start={event.get('attributes', {}).get('start')}")
                
            if events:
                event = events[0]
                timestamp_ms = event.get('attributes', {}).get('start')
                
                logger.info(f"--- Phase 3: Testing Image Download at {timestamp_ms} ---")
                img_res = await provider.download_image(target.camera_id, timestamp=timestamp_ms)
                if img_res.get("status") == "success":
                    download_url = img_res["download_url"]
                    logger.info(f"Got Image 303 Redirect: {download_url[:60]}...")
                    
                    # Fetch binary data
                    async with httpx.AsyncClient() as client:
                        img_dl = await client.get(download_url)
                        logger.info(f"Image Download HTTP Status: {img_dl.status_code}")
                        logger.info(f"Image Content-Type: {img_dl.headers.get('content-type')}")
                        logger.info(f"Image Size: {len(img_dl.content)} bytes")
                else:
                    logger.warning(f"Image Download Failed: {img_res}")
                    
                logger.info(f"--- Phase 4: Testing Video Download at {timestamp_ms} ---")
                vid_res = await provider.download_video(target.camera_id, timestamp=timestamp_ms)
                if vid_res.get("status") == "success":
                    download_url = vid_res["download_url"]
                    logger.info(f"Got Video 303 Redirect: {download_url[:60]}...")
                    
                    # Fetch binary data
                    async with httpx.AsyncClient() as client:
                        vid_dl = await client.get(download_url)
                        logger.info(f"Video Download HTTP Status: {vid_dl.status_code}")
                        logger.info(f"Video Content-Type: {vid_dl.headers.get('content-type')}")
                        logger.info(f"Video Size: {len(vid_dl.content)} bytes")
                else:
                    logger.warning(f"Video Download Failed: {vid_res}")

            else:
                logger.info("No events available to test media downloads.")
                
                timestamp_ms = int(time.time() * 1000) - 300000
                
                logger.info(f"Attempting image download fallback at {timestamp_ms}")
                img_res = await provider.download_image(target.camera_id, timestamp=timestamp_ms)
                logger.info(f"Fallback Image response: {img_res}")
                
        else:
            logger.error(f"Event History API failed: {history_res}")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_media_tests())
