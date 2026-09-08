import asyncio
import time
from xsc_lib.xsc_lib_common.database import get_db, RingToken
from xsc_lib.xsc_lib_extn.ring.provider import RingCameraProvider

async def run():
    db = next(get_db())
    token = db.query(RingToken).filter_by(is_claimed=1).first()
    provider = RingCameraProvider(db, token.account_id)
    devices = await provider.get_devices()
    target = next((d for d in devices if d.name == "TS RING 01"), None)
    
    events = await provider.get_events(target.camera_id)
    print(f"Total events: {len(events)}")
    for e in events:
        age = time.time() - e.timestamp.timestamp()
        print(f"ID: {e.event_id}, TS: {e.timestamp}, Age: {age:.1f}s")
        
if __name__ == "__main__":
    asyncio.run(run())
