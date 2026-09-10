from abc import ABC, abstractmethod
import numpy as np
from xsc_lib.xsc_lib_common.models.ai import FaceQuality

class FaceQualityAnalyzer(ABC):
    """
    Abstract interface for assessing face quality.
    """
    
    @abstractmethod
    def analyze_quality(self, face_image: np.ndarray) -> FaceQuality:
        """
        Analyzes the quality of a cropped face image.
        
        Args:
            face_image: numpy array (BGR format) of the cropped face.
            
        Returns:
            A FaceQuality model containing width, height, blur_score, brightness,
            and whether it meets the threshold for further processing.
        """
        pass
