import cv2
import numpy as np
from ai.face.quality import FaceQualityAnalyzer
from ai.models import FaceQuality

class OpenCVFaceQualityAnalyzer(FaceQualityAnalyzer):
    """
    Analyzes face quality using basic deterministic OpenCV heuristics.
    """
    
    def __init__(self, min_width: int = 40, min_height: int = 40, min_blur: float = 100.0, min_brightness: float = 50.0):
        self.min_width = min_width
        self.min_height = min_height
        self.min_blur = min_blur
        self.min_brightness = min_brightness
        
    def analyze_quality(self, face_image: np.ndarray) -> FaceQuality:
        """
        Analyzes the quality of a cropped face image.
        """
        if face_image is None or face_image.size == 0:
            return FaceQuality(
                width=0, height=0, blur_score=0.0, brightness=0.0,
                pose=None, occlusion=None, meets_threshold=False
            )
            
        h, w = face_image.shape[:2]
        
        # Calculate blur score using Laplacian variance
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        
        # Calculate brightness (average pixel intensity in grayscale)
        brightness = float(np.mean(gray))
        
        # Determine if it meets the overall threshold
        size_sufficient = (w >= self.min_width and h >= self.min_height)
        sharp_enough = blur_score >= self.min_blur
        bright_enough = brightness >= self.min_brightness
        
        meets_threshold = bool(size_sufficient and sharp_enough and bright_enough)
        
        return FaceQuality(
            width=w,
            height=h,
            blur_score=blur_score,
            brightness=brightness,
            pose=None,       # Deferred: Unsupported in this phase
            occlusion=None,  # Deferred: Unsupported in this phase
            meets_threshold=meets_threshold
        )
