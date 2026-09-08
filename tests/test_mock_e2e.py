import pytest
import asyncio
from unittest.mock import patch, MagicMock
from xsc_lib.xsc_lib_extn.ring.provider import RingCameraProvider

@pytest.mark.asyncio
async def test_get_devices():
    mock_db = MagicMock()
    provider = RingCameraProvider(mock_db, "mock_account")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": "cam_1",
                "attributes": {
                    "name": "Test Cam 1",
                    "status": "online",
                    "capabilities": {
                        "motion_detection": True,
                        "video": {"codecs": ["h264"]}
                    }
                }
            }
        ]
    }
    
    with patch("xsc_lib.xsc_lib_extn.ring.client.RingClient.get", return_value=mock_response):
        devices = await provider.get_devices(force_refresh=True)
        assert len(devices) == 1
        assert devices[0].name == "Test Cam 1"
        assert devices[0].capabilities["motion_detection"] is True

@pytest.mark.asyncio
async def test_start_live_stream():
    mock_db = MagicMock()
    provider = RingCameraProvider(mock_db, "mock_account")
    
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.headers = {"Location": "https://api.amazonvision.com/v1/sessions/123"}
    mock_response.text = "v=0\no=- 0 0 IN IP4 127.0.0.1\n..."
    
    with patch("xsc_lib.xsc_lib_extn.ring.client.RingClient.post", return_value=mock_response):
        result = await provider.start_live_stream("cam_1", "v=0\n...")
        assert result["status"] == "success"
        assert result["session_url"] == "https://api.amazonvision.com/v1/sessions/123"

@pytest.mark.asyncio
async def test_download_image():
    mock_db = MagicMock()
    provider = RingCameraProvider(mock_db, "mock_account")
    
    mock_response = MagicMock()
    mock_response.status_code = 303
    mock_response.headers = {"Location": "https://media.api.amazonvision.com/download"}
    
    with patch("xsc_lib.xsc_lib_extn.ring.client.RingClient.post", return_value=mock_response):
        result = await provider.download_image("cam_1", timestamp="2026-08-20T00:00:00Z")
        assert result["status"] == "success"
        assert result["download_url"] == "https://media.api.amazonvision.com/download"
