import asyncio
import time
from database import get_db, RingToken
from ring.provider import RingCameraProvider

async def run():
    db = next(get_db())
    token = db.query(RingToken).filter_by(is_claimed=1).first()
    provider = RingCameraProvider(db, token.account_id)
    devices = await provider.get_devices()
    target = next((d for d in devices if d.name == "TS RING 01"), None)
    
    events = await provider.get_events(target.camera_id)
    if not events:
        print("No events")
        return
        
    e = events[0]
    ts = e.timestamp.timestamp()
    age = time.time() - ts
    print(f"Latest Event: {e.event_id}")
    print(f"Timestamp: {e.timestamp}")
    print(f"Age: {age:.1f} seconds")
    
    if age < 300:
        print("Fresh event found! Attempting download...")
        vid_res = await provider.download_video(target.camera_id, timestamp=int(ts * 1000))
        print(vid_res)
        
if __name__ == "__main__":
    asyncio.run(run())
