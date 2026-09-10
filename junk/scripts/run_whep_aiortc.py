import asyncio
import logging
from xsc_lib.xsc_lib_common import database
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription
from xsc_lib.xsc_lib_common.database import SessionLocal
from xsc_lib.xsc_lib_extn.ring.provider import RingCameraProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_whep():
    db = next(database.get_db())
    try:
        # Fetch first claimed token to get account_id for test
        token = db.query(database.RingToken).filter_by(is_claimed=1).first()
        if not token:
            logger.error("No claimed token found.")
            return
            
        account_id = token.account_id
        provider = RingCameraProvider(db, account_id)
        
        logger.info("Fetching devices...")
        devices = await provider.get_devices()
        target = next((d for d in devices if d.name == "TS RING 02"), None)
        if not target:
            logger.error("Could not find TS RING 02")
            return
            
        logger.info(f"Target device found: {target.camera_id}")
        
        config = RTCConfiguration(
            iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        )
        pc = RTCPeerConnection(configuration=config)
        
        @pc.on("track")
        def on_track(track):
            logger.info(f"Track received! kind: {track.kind}")

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE connection state is {pc.iceConnectionState}")

        pc.addTransceiver("video", direction="recvonly")
        
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        # Wait for ICE gathering in aiortc
        logger.info("Waiting for ICE gathering to complete...")
        for _ in range(10):
            if pc.iceGatheringState == "complete":
                break
            await asyncio.sleep(0.5)
            
        sdp_offer = pc.localDescription.sdp
        logger.info(f"Generated SDP Offer Length: {len(sdp_offer)}")
        logger.info(f"Sending WHEP request...")
        
        response = await provider.client.post(
            f"/v1/devices/{target.camera_id}/media/streaming/whep/sessions",
            content=sdp_offer,
            headers={"Content-Type": "application/sdp"}
        )
        
        logger.info(f"HTTP Status: {response.status_code}")
        logger.info(f"Content-Type: {response.headers.get('content-type')}")
        logger.info(f"Location: {response.headers.get('Location')}")
        
        if response.status_code == 201:
            sdp_answer = response.text
            logger.info(f"Received SDP answer Length: {len(sdp_answer)}")
            
            answer = RTCSessionDescription(sdp=sdp_answer, type="answer")
            await pc.setRemoteDescription(answer)
            
            logger.info("Remote description set. Waiting 10s for media...")
            await asyncio.sleep(10)
            
            session_url = response.headers.get('Location')
            logger.info(f"Stopping WHEP session {session_url}...")
            stop_res = await provider.stop_live_stream(target.camera_id, session_url)
            logger.info(f"Stop result: {stop_res}")
        else:
            logger.error(f"Error Body: {response.text}")
            
        await pc.close()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_whep())
