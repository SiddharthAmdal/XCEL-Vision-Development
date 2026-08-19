import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database
from ring.provider import RingCameraProvider
from ring.client import RingClient, RateLimitException

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    database.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_device_caching(test_db):
    """
    Verify that get_devices uses the local database cache and only hits the API when forced or stale.
    """
    token = database.RingToken(
        account_id="acc_cache",
        access_token="valid",
        refresh_token="valid",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        is_claimed=1
    )
    test_db.add(token)
    test_db.commit()
    
    provider = RingCameraProvider(test_db, account_id="acc_cache")
    
    async def mock_get(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {
                    "id": "cam_1",
                    "attributes": {
                        "name": "Front Door",
                        "status": "online",
                        "capabilities": {"video": True}
                    }
                }
            ]
        }
        return mock_resp

    with patch.object(provider.client, 'get', side_effect=mock_get) as mock_get_method:
        # First call should hit API
        devices = await provider.get_devices()
        assert len(devices) == 1
        assert mock_get_method.call_count == 1
        
        # Second call should hit cache
        devices2 = await provider.get_devices()
        assert len(devices2) == 1
        assert mock_get_method.call_count == 1 # still 1
        
        # Force refresh should hit API
        devices3 = await provider.get_devices(force_refresh=True)
        assert len(devices3) == 1
        assert mock_get_method.call_count == 2

@pytest.mark.asyncio
async def test_pagination(test_db):
    """
    Verify that get_event_history paginates up to 5 pages.
    """
    provider = RingCameraProvider(test_db, account_id="acc_pag")
    
    page_count = 0
    async def mock_get(path, **kwargs):
        nonlocal page_count
        page_count += 1
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        
        # Return next link for first 3 pages
        links = {}
        if page_count < 3:
            links["next"] = f"https://api.amazonvision.com/v1/history/devices/cam_1/events?page[key]=page{page_count+1}"
            
        mock_resp.json.return_value = {
            "data": [{"id": f"event_{page_count}"}],
            "links": links
        }
        return mock_resp

    with patch.object(provider.client, 'get', side_effect=mock_get):
        res = await provider.get_event_history("cam_1")
        assert res["status"] == "success"
        assert len(res["events"]) == 3
        assert page_count == 3
