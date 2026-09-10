from abc import ABC, abstractmethod
import numpy as np
from typing import List

class FaceEmbeddingModel(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        pass

    @abstractmethod
    def generate_embedding(self, face_image: np.ndarray) -> List[float]:
        pass
