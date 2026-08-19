import logging
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .models import XcelCamera
from .client import RingClient
import database
from config import settings

logger = logging.getLogger(__name__)

class RingCameraProvider:
    """
    Abstracts Ring API specifics and returns normalized XCEL objects.
    """
    def __init__(self, db: Session, account_id: str):
        if not account_id:
            raise ValueError("account_id is required to initialize RingCameraProvider")
        self.db = db
        self.account_id = account_id
        self.client = RingClient(db, account_id)

    async def get_devices(self, force_refresh: bool = False) -> List[XcelCamera]:
        """
        Fetches devices from Ring, caching them locally per-account to avoid rate limits.
        """
        ttl_seconds = settings.RING_DEVICE_CACHE_TTL_SECONDS
        cutoff = datetime.utcnow() - timedelta(seconds=ttl_seconds)
        
        # Check cache if not forcing refresh
        if not force_refresh:
            cached_records = self.db.query(database.RingDeviceCache).filter_by(account_id=self.account_id).filter(database.RingDeviceCache.last_synced_at >= cutoff).all()
            if cached_records:
                logger.info(f"Returning {len(cached_records)} cached devices for account {self.account_id}")
                return [
                    XcelCamera(
                        id=record.device_id,
                        provider="ring",
                        provider_device_id=record.device_id,
                        name=record.metadata_json.get("attributes", {}).get("name", "Unknown Camera"),
                        location=record.metadata_json.get("attributes", {}).get("location_id"),
                        status=record.status,
                        capabilities=record.capabilities_json,
                        metadata=record.metadata_json
                    )
                    for record in cached_records
                ]

        logger.info(f"Fetching devices from Ring API for account {self.account_id}...")
        response = await self.client.get("/v1/devices?include=status,capabilities")
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch devices: {response.status_code}")
            return []
            
        data = response.json()
        devices = data.get("data", [])
        
        # Upsert cache
        active_device_ids = set()
        normalized_cameras = []
        
        for device in devices:
            device_id = device.get("id")
            attrs = device.get("attributes", {})
            capabilities = attrs.get("capabilities", {})
            status = attrs.get("status", "unknown")
            active_device_ids.add(device_id)
            
            # Upsert
            cache_rec = self.db.query(database.RingDeviceCache).filter_by(account_id=self.account_id, device_id=device_id).first()
            if not cache_rec:
                cache_rec = database.RingDeviceCache(account_id=self.account_id, device_id=device_id)
                self.db.add(cache_rec)
            
            cache_rec.metadata_json = device
            cache_rec.capabilities_json = capabilities
            cache_rec.status = status
            cache_rec.last_synced_at = datetime.utcnow()
            
            cam = XcelCamera(
                id=device_id,
                provider="ring",
                provider_device_id=device_id,
                name=attrs.get("name", "Unknown Camera"),
                location=attrs.get("location_id"),
                status=status,
                capabilities=capabilities,
                metadata=device
            )
            normalized_cameras.append(cam)
            
        # Cleanup stale devices that disappeared from Ring for this account
        stale_records = self.db.query(database.RingDeviceCache).filter_by(account_id=self.account_id).all()
        for stale in stale_records:
            if stale.device_id not in active_device_ids:
                logger.info(f"Device {stale.device_id} removed from Ring, deactivating cache.")
                self.db.delete(stale)
                
        self.db.commit()
        return normalized_cameras
        
    async def generate_capability_report(self):
        devices = await self.get_devices()
        
        if not devices:
            return {"status": "error", "message": "No devices found or API call failed"}
            
        verified_capabilities = set()
        for device in devices:
            for cap, val in device.capabilities.items():
                if val:
                    verified_capabilities.add(cap)
                
        return {
            "status": "success",
            "total_cameras_discovered": len(devices),
            "verified_capabilities": list(verified_capabilities),
            "cameras": [
                {
                    "name": cam.name,
                    "status": cam.status,
                    "capabilities": cam.capabilities
                } for cam in devices
            ]
        }

    async def start_live_stream(self, device_id: str, sdp_offer: str) -> dict:
        response = await self.client.post(
            f"/v1/devices/{device_id}/media/streaming/whep/sessions",
            content=sdp_offer,
            headers={"Content-Type": "application/sdp"}
        )
        if response.status_code == 201:
            return {
                "status": "success",
                "session_url": response.headers.get("Location"),
                "sdp_answer": response.text
            }
        else:
            return {
                "status": "error",
                "code": response.status_code,
                "message": response.text
            }

    async def stop_live_stream(self, session_url: str) -> dict:
        if session_url.startswith("http"):
            path = session_url.replace("https://api.amazonvision.com", "")
        else:
            path = session_url
            
        response = await self.client.delete(path)
        if response.status_code in (200, 204):
            return {"status": "success"}
        else:
            return {"status": "error", "code": response.status_code}
            
    async def download_image(self, device_id: str, timestamp=None, end_timestamp=None) -> dict:
        payload = {}
        if timestamp is not None:
            payload["type"] = "at_timestamp"
            payload["timestamp"] = timestamp
            
        response = await self.client.post(
            f"/v1/devices/{device_id}/media/image/download",
            json=payload,
            follow_redirects=False
        )
        if response.status_code == 303:
            return {"status": "success", "download_url": response.headers.get("Location")}
        return {"status": "error", "code": response.status_code, "message": response.text}

    async def download_video(self, device_id: str, timestamp, duration: int = 30) -> dict:
        payload = {
            "timestamp": timestamp,
            "duration": duration
        }
            
        response = await self.client.post(
            f"/v1/devices/{device_id}/media/video/download",
            json=payload,
            follow_redirects=False
        )
        if response.status_code == 303:
            return {"status": "success", "download_url": response.headers.get("Location")}
        return {"status": "error", "code": response.status_code, "message": response.text}

    async def get_event_history(self, device_id: str, event_types: str = None, page_key: str = None) -> dict:
        """
        Retrieves event history for a device, handling cursor pagination.
        Will fetch up to 5 pages automatically.
        """
        params = {}
        if event_types:
            params['event_types'] = event_types
        if page_key:
            params['page[key]'] = page_key
            
        all_events = []
        path = f"/v1/history/devices/{device_id}/events"
        
        pages_fetched = 0
        max_pages = 5
        
        while path and pages_fetched < max_pages:
            response = await self.client.get(path, params=params if pages_fetched == 0 else {})
            
            if response.status_code != 200:
                if pages_fetched == 0:
                    return {"status": "error", "code": response.status_code, "message": response.text}
                else:
                    logger.warning(f"Failed to fetch paginated page {pages_fetched}. Returning collected events.")
                    break
                    
            data = response.json()
            events = data.get("data", [])
            all_events.extend(events)
            
            # Check for next page
            links = data.get("links", {})
            next_url = links.get("next")
            
            if next_url:
                if next_url.startswith("http"):
                    path = next_url.replace(self.client.base_url, "")
                else:
                    path = next_url
                pages_fetched += 1
            else:
                break
                
        return {"status": "success", "events": all_events}
