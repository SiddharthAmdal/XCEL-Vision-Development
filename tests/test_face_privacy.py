import pytest
from ai.models import AIFrameResult, FaceDetection, FaceQuality

def test_face_privacy_no_embeddings():
    quality = FaceQuality(
        width=50, height=50, blur_score=100.0, brightness=100.0, meets_threshold=True
    )
    face = FaceDetection(
        face_id="random-uuid",
        track_id=1,
        bbox=(0,0,10,10),
        confidence=0.99,
        quality=quality,
        expression=None
    )
    
    face_dict = face.model_dump()
    
    # Assertions guaranteeing Phase 6.2 privacy constraints
    assert "embedding" not in face_dict
    assert "embeddings" not in face_dict
    assert "identity" not in face_dict
    assert "name" not in face_dict
    assert "recognition_state" not in face_dict
    assert "known" not in face_dict

def test_aiframeresult_structure():
    result = AIFrameResult(
        camera_id="cam1",
        timestamp="2023-01-01T00:00:00Z",
        frame_number=1,
        persons=0,
        detections=[],
        faces=[]
    )
    
    res_dict = result.model_dump()
    assert "faces" in res_dict
    assert "detections" in res_dict
    # Faces must not be nested inside detections natively at the schema level
    # since it's a separate top-level list
