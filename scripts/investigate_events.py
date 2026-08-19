import asyncio
import logging
from database import get_db, RingToken
from ring.provider import RingCameraProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def investigate():
    db = next(get_db())
    token = db.query(RingToken).filter_by(is_claimed=1).first()
    provider = RingCameraProvider(db, token.account_id)
    
    devices = await provider.get_devices()
    target = next((d for d in devices if d.name == "TS RING 01"), None)
    
    events = await provider.get_events(target.camera_id)
    for i, e in enumerate(events[:5]):
        logger.info(f"Event {i}: ID={e.event_id}, Timestamp={e.timestamp}")
        
    if events:
        target_event = events[0]
        ts = int(target_event.timestamp.timestamp() * 1000)
        logger.info(f"Trying to download media for latest event {target_event.event_id} at ts {ts}...")
        vid_res = await provider.download_video(target.camera_id, timestamp=ts)
        logger.info(f"Result: {vid_res}")

if __name__ == "__main__":
    asyncio.run(investigate())
