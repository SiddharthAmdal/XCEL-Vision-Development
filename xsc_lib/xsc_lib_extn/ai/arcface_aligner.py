from abc import ABC, abstractmethod
import numpy as np
import cv2
from typing import List, Tuple

class FaceAligner(ABC):
    @abstractmethod
    def align(self, image: np.ndarray, landmarks: List[Tuple[int, int]]) -> np.ndarray:
        """
        Aligns a face image based on 5 landmarks (right_eye, left_eye, nose, right_mouth, left_mouth).
        """
        pass

class ArcFaceAligner(FaceAligner):
    """
    Standard Face Aligner for ArcFace models.
    Produces an aligned 112x112 face crop.
    """
    def __init__(self, output_size: Tuple[int, int] = (112, 112)):
        self.output_size = output_size
        
        # Standard ArcFace reference points for 112x112
        self.reference_landmarks = np.array([
            [38.2946, 51.6963],   # Right eye (viewer's left)
            [73.5318, 51.5014],   # Left eye (viewer's right)
            [56.0252, 71.7366],   # Nose
            [41.5493, 92.3655],   # Right mouth
            [70.7299, 92.2041]    # Left mouth
        ], dtype=np.float32)

    def align(self, image: np.ndarray, landmarks: List[Tuple[int, int]]) -> np.ndarray:
        if not landmarks or len(landmarks) != 5:
            # Fallback if no landmarks available, just resize
            return cv2.resize(image, self.output_size)
            
        src_points = np.array(landmarks, dtype=np.float32)
        
        # Estimate affine transform
        tform, _ = cv2.estimateAffinePartial2D(src_points, self.reference_landmarks, method=cv2.LMEDS)
        
        if tform is None:
            return cv2.resize(image, self.output_size)
            
        # Apply affine transform
        aligned_face = cv2.warpAffine(
            image, 
            tform, 
            self.output_size, 
            borderValue=0.0
        )
        return aligned_face
