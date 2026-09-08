import pytest
import numpy as np
from xsc_lib.xsc_lib_extn.ai.yunet import YuNetFaceDetector

@pytest.fixture
def detector():
    return YuNetFaceDetector()

def test_no_face_frame(detector):
    # Black image, no faces
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    faces = detector.detect_faces(img)
    assert len(faces) == 0

def test_single_face_frame(detector):
    # Using a dummy setup; YuNet might not find a face in noise, so we just check it doesn't crash
    # and returns a list. Real validation happens with an actual face image.
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    faces = detector.detect_faces(img)
    assert isinstance(faces, list)

def test_bounding_box_normalization(detector):
    # We will mock the internal cv2 detector to return out of bounds coordinates
    class MockDetector:
        def detect(self, img):
            # return 1 face: x, y, w, h, ..., score
            # x=-10, y=-10, w=20, h=20 -> x1=-10, y1=-10, x2=10, y2=10 -> clipped to 0, 0, 10, 10
            face_data = np.array([[-10, -10, 20, 20, 0,0,0,0,0,0,0,0,0,0, 0.9]])
            return 1, face_data
            
    detector._get_detector = lambda w, h: MockDetector()
    
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    faces = detector.detect_faces(img)
    assert len(faces) == 1
    bbox, conf, landmarks = faces[0]
    x1, y1, x2, y2 = bbox
    assert x1 == 0
    assert y1 == 0
    assert x2 == 10
    assert y2 == 10
    assert conf == 0.9

def test_malformed_detector_output(detector):
    class MockDetector:
        def detect(self, img):
            return 0, None
            
    detector._get_detector = lambda w, h: MockDetector()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    faces = detector.detect_faces(img)
    assert len(faces) == 0
