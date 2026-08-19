import asyncio
from database import SessionLocal
from ring.provider import RingCameraProvider
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic valid receive-only SDP offer for WHEP
DUMMY_SDP_OFFER = """v=0
o=- 4611731400430051336 2 IN IP4 127.0.0.1
s=-
t=0 0
a=extmap-allow-mixed
a=msid-semantic: WMS
m=video 9 UDP/TLS/RTP/SAVPF 96 97 98 99 100 101 102 122 127 121 125 107 108 109 124 120 119 114 115 116
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:dummy
a=ice-pwd:dummy
a=fingerprint:sha-256 00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00
a=setup:actpass
a=mid:0
a=extmap:14 urn:ietf:params:rtp-hdrext:sdes:rtp-stream-id
a=extmap:13 urn:ietf:params:rtp-hdrext:sdes:repaired-rtp-stream-id
a=sendonly
a=rtcp-mux
a=rtpmap:96 VP8/90000
a=rtpmap:97 rtx/90000
a=fmtp:97 apt=96
"""

async def test_whep():
    db = SessionLocal()
    try:
        provider = RingCameraProvider(db)
        logger.info("Fetching devices to find TS RING 01...")
        devices = await provider.get_devices()
        
        target_device = next((d for d in devices if d.name == "TS RING 01"), None)
        if not target_device:
            logger.error("Could not find TS RING 01")
            return
            
        logger.info(f"Found TS RING 01 with ID: {target_device.id}")
        logger.info("Attempting WHEP Session...")
        
        result = await provider.start_live_stream(target_device.id, DUMMY_SDP_OFFER)
        
        logger.info(f"WHEP Session Result: {result}")
        
        if result["status"] == "success":
            session_url = result.get("session_url")
            logger.info(f"Successfully started stream! Session URL: {session_url}")
            logger.info("Stopping stream...")
            stop_result = await provider.stop_live_stream(session_url)
            logger.info(f"Stop Result: {stop_result}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_whep())
