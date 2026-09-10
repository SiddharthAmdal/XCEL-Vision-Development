import pytest
from datetime import datetime
from xsc_lib.xsc_lib_common.models.camera import Camera, CameraEvent
from xsc_lib.xsc_lib_common.interfaces.camera_provider import CameraProvider
from xsc_lib.xsc_lib_extn.ring.provider import RingCameraProvider
from unittest.mock import MagicMock

def test_camera_model_normalization():
    # Test valid normalization and required fields
    camera = Camera(
        camera_id="cam_123",
        provider="ring",
        external_id="ring_456",
        name="Front Door",
        location="porch",
        status="online",
        capabilities={"motion": True, "video": True}
    )
    
    assert camera.camera_id == "cam_123"
    assert camera.provider == "ring"
    assert camera.external_id == "ring_456"
    assert camera.name == "Front Door"
    assert camera.location == "porch"
    assert camera.status == "online"
    assert camera.capabilities["motion"] is True
    assert camera.last_event is None

def test_camera_event_model():
    # Test event model, received_at, and provider-independent types
    now = datetime.utcnow()
    event = CameraEvent(
        event_id="evt_001",
        provider="ring",
        camera_id="cam_123",
        event_type="MOTION",
        timestamp=now,
        metadata={"raw_data": "some_value"}
    )
    
    assert event.event_id == "evt_001"
    assert event.provider == "ring"
    assert event.camera_id == "cam_123"
    assert event.event_type == "MOTION"
    assert event.timestamp == now
    assert event.metadata["raw_data"] == "some_value"
    assert event.received_at is not None
    # Verify received_at is populated automatically if omitted (which pydantic does with default_factory)

def test_ring_provider_satisfies_interface():
    # Verify RingCameraProvider is a subclass of CameraProvider
    assert issubclass(RingCameraProvider, CameraProvider)
    
    mock_db = MagicMock()
    provider = RingCameraProvider(mock_db, account_id="acc_1")
    assert isinstance(provider, CameraProvider)

@pytest.mark.asyncio
async def test_no_ring_structures_leak():
    # Ensure provider methods return generic objects, not Ring structures
    mock_db = MagicMock()
    provider = RingCameraProvider(mock_db, account_id="acc_1")
    
    # Mock the db query to return empty cache so it hits the API
    mock_db.query.return_value.filter_by.return_value.filter.return_value.all.return_value = []
    
    # Mock the internal client response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": "ring_cam_1",
                "attributes": {
                    "name": "Backyard",
                    "status": "offline",
                    "capabilities": {"motion_detection": True}
                }
            }
        ]
    }
    
    from unittest.mock import patch
    with patch("xsc_lib.xsc_lib_extn.ring.client.RingClient.get", return_value=mock_response):
        devices = await provider.get_devices(force_refresh=True)
        assert len(devices) == 1
        cam = devices[0]
        # Should be the generic Camera model
        assert isinstance(cam, Camera)
        assert cam.camera_id == "ring_cam_1"
        assert cam.provider == "ring"
        assert cam.name == "Backyard"
        
        # Test get_device
        single_cam = await provider.get_device("ring_cam_1")
        assert isinstance(single_cam, Camera)
        assert single_cam.camera_id == "ring_cam_1"
        
        # Test get_capabilities
        caps = await provider.get_capabilities("ring_cam_1")
        assert isinstance(caps, dict)
        assert caps.get("motion_detection") is True
