from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np

class FaceDetector(ABC):
    """
    Abstract interface for face detection.
    Must not depend on YOLO, ByteTrack, or Camera implementations.
    """
    
    @abstractmethod
    def detect_faces(self, image: np.ndarray) -> List[Tuple[Tuple[int, int, int, int], float, Optional[np.ndarray]]]:
        """
        Detects faces in the provided BGR image array.
        
        Args:
            image: numpy array (BGR format) representing the image or cropped region.
            
        Returns:
            A list of tuples: (bounding_box (x1,y1,x2,y2), confidence, landmarks)
        """
        pass
