from abc import ABC, abstractmethod
from typing import List
import numpy as np
from ai.models import FacialExpression

class ExpressionAnalyzer(ABC):
    """
    Abstract interface for inferring visual facial expressions.
    """
    
    @abstractmethod
    def analyze_expression(self, face_image: np.ndarray) -> FacialExpression:
        """
        Infers the facial expression from a cropped face image.
        
        Args:
            face_image: numpy array (BGR format) of the cropped face.
            
        Returns:
            A FacialExpression model containing the label and confidence.
        """
        pass
