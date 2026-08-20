import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from main import app
from api.routers.cameras import get_camera_service
from camera.models import Camera
import numpy as np
import cv2

client = TestClient(app)

def create_dummy_jpeg():
    # Create a simple 640x480 red image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (0, 0, 255)
    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()

@pytest.fixture(autouse=True)
def mock_service():
    mock_svc = MagicMock()
    mock_cam = Camera(
        camera_id="ava1.ring.device.3A3O2F43AXLFYFBY77FDT6RQ6TJE2D3FXK6IPDEUXQICP235MTBOGWTOGYE4JIN3WM2HJRVFJ3KH5SZSRNATIZJR5TDXTZRL",
        provider="ring",
        external_id="mock_ext_id",
        name="Test Cam",
        status="online",
        capabilities={}
    )
    
    # We must mock get_camera to return the mock_cam or None
    async def get_camera_mock(camera_id):
        if camera_id == mock_cam.camera_id:
            return mock_cam
        return None
    mock_svc.get_camera = get_camera_mock
    
    # Mock stop_live_stream
    async def stop_live_stream_mock(camera_id, session_id):
        return {"status": "success"}
    mock_svc.stop_live_stream = stop_live_stream_mock

    app.dependency_overrides[get_camera_service] = lambda: mock_svc
    yield mock_svc
    app.dependency_overrides.clear()

def test_analyze_frame_missing_camera():
    dummy_jpeg = create_dummy_jpeg()
    response = client.post(
        "/api/v1/cameras/invalid-camera/analyze-frame",
        data={"session_id": "test_sess_1"},
        files={"file": ("frame.jpg", dummy_jpeg, "image/jpeg")},
        headers={"Authorization": "Bearer dev_token"}
    )
    assert response.status_code == 404

def test_analyze_frame_invalid_image_type():
    response = client.post(
        "/api/v1/cameras/ava1.ring.device.3A3O2F43AXLFYFBY77FDT6RQ6TJE2D3FXK6IPDEUXQICP235MTBOGWTOGYE4JIN3WM2HJRVFJ3KH5SZSRNATIZJR5TDXTZRL/analyze-frame",
        data={"session_id": "test_sess_2"},
        files={"file": ("frame.txt", b"not an image", "text/plain")},
        headers={"Authorization": "Bearer dev_token"}
    )
    assert response.status_code == 415

def test_analyze_frame_success():
    dummy_jpeg = create_dummy_jpeg()
    camera_id = "ava1.ring.device.3A3O2F43AXLFYFBY77FDT6RQ6TJE2D3FXK6IPDEUXQICP235MTBOGWTOGYE4JIN3WM2HJRVFJ3KH5SZSRNATIZJR5TDXTZRL"
    response = client.post(
        f"/api/v1/cameras/{camera_id}/analyze-frame",
        data={"session_id": "test_sess_3"},
        files={"file": ("frame.jpg", dummy_jpeg, "image/jpeg")},
        headers={"Authorization": "Bearer dev_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == camera_id
    assert "persons" in data
    assert "detections" in data
    
    # Cleanup session
    response2 = client.delete(
        f"/api/v1/cameras/{camera_id}/live/fake_whep_session?ai_session_id=test_sess_3", 
        headers={"Authorization": "Bearer dev_token"}
    )
    assert response2.status_code == 200
