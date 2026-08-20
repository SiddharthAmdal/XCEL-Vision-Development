import os
import cv2
import numpy as np
from typing import Optional
from ai.face.expression import ExpressionAnalyzer
from ai.models import FacialExpression

class FERPlusExpressionAnalyzer(ExpressionAnalyzer):
    """
    Concrete implementation of ExpressionAnalyzer using the ONNX FER+ model.
    """
    
    # FER+ classes: neutral, happiness, surprise, sadness, anger, disgust, fear, contempt
    # We map them to the normalized FacialExpression labels.
    LABELS = [
        "neutral", 
        "happy", 
        "surprised", 
        "sad", 
        "angry", 
        "disgusted", 
        "fearful", 
        "contempt"
    ]
    
    def __init__(self, model_path: str = "ai/models/weights/emotion-ferplus-8.onnx"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"FER+ model not found at {model_path}")
            
        self.model_path = model_path
        self._net = cv2.dnn.readNetFromONNX(self.model_path)
        
    def analyze_expression(self, face_image: np.ndarray) -> Optional[FacialExpression]:
        """
        Analyzes the facial expression from a cropped face image.
        """
        if face_image is None or face_image.size == 0:
            return None
            
        # The FER+ model expects a 64x64 grayscale image
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64))
        
        # Create a 4D blob from the image (1, 1, 64, 64)
        blob = cv2.dnn.blobFromImage(resized, 1.0, (64, 64), (0, 0, 0), swapRB=False, crop=False)
        
        self._net.setInput(blob)
        out = self._net.forward()
        
        # Output is shape (1, 8). We apply softmax to get probabilities.
        scores = out[0]
        exp_scores = np.exp(scores - np.max(scores))
        probabilities = exp_scores / exp_scores.sum()
        
        best_class_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[best_class_idx])
        label = self.LABELS[best_class_idx]
        
        return FacialExpression(
            label=label,
            confidence=confidence
        )
