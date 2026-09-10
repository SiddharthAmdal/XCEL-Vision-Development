import os
import cv2
import cv2
import numpy as np
from typing import List, Tuple, Optional
from xsc_lib.xsc_lib_common.interfaces.face_detector import FaceDetector

class YuNetFaceDetector(FaceDetector):
    """
    Concrete implementation of FaceDetector using OpenCV's YuNet ONNX model.
    """
    
    def __init__(self, model_path: str = "models/weights/face_detection_yunet_2023mar.onnx", score_threshold: float = 0.5):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YuNet model not found at {model_path}")
        
        self.model_path = model_path
        self.score_threshold = score_threshold
        # The detector is dynamically created in detect_faces since input size varies
        # But we can cache the object and just resize it for efficiency
        self._detector = None
        self._last_size = (0, 0)
        
    def _get_detector(self, w: int, h: int) -> cv2.FaceDetectorYN:
        if self._detector is None:
            self._detector = cv2.FaceDetectorYN.create(
                self.model_path, 
                "", 
                (w, h), 
                score_threshold=self.score_threshold
            )
            self._last_size = (w, h)
        elif self._last_size != (w, h):
            self._detector.setInputSize((w, h))
            self._last_size = (w, h)
            
        return self._detector

    def detect_faces(self, image: np.ndarray) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """
        Detects faces in the provided BGR image array.
        
        Args:
            image: numpy array (BGR format) representing the image or cropped region.
            
        Returns:
        Returns:
            A list of tuples containing:
            - bounding_box: (x1, y1, x2, y2) relative to the provided image.
            - confidence: float score between 0.0 and 1.0.
            - landmarks: Optional list of 5 (x, y) tuples.
        """
        h, w = image.shape[:2]
        detector = self._get_detector(w, h)
        
        # OpenCV YuNet detect returns: 
        # (status, faces)
        # where faces is a 2D array of shape (num_faces, 15)
        # 0-1: x, y of top-left corner
        # 2-3: width, height
        # 4-13: landmarks
        # 14: score
        _, faces = detector.detect(image)
        
        results = []
        if faces is not None:
            for face in faces:
                x, y, fw, fh = face[:4]
                score = face[-1]
                
                # Convert to x1, y1, x2, y2
                x1 = int(x)
                y1 = int(y)
                x2 = int(x + fw)
                y2 = int(y + fh)
                
                # Clip to image bounds just to be safe
                x1 = max(0, min(x1, w - 1))
                y1 = max(0, min(y1, h - 1))
                x2 = max(0, min(x2, w - 1))
                y2 = max(0, min(y2, h - 1))
                
                # Skip invalid boxes
                if x2 <= x1 or y2 <= y1:
                    continue
                    
                # Extract 5 landmarks (right eye, left eye, nose tip, right mouth corner, left mouth corner)
                landmarks = []
                for i in range(5):
                    lx = int(face[4 + i * 2])
                    ly = int(face[4 + i * 2 + 1])
                    landmarks.append((lx, ly))
                    
                results.append(((x1, y1, x2, y2), float(score), landmarks))
                
        return results
