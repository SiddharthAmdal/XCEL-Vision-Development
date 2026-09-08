import numpy as np
from abc import ABC, abstractmethod
from typing import List, Optional

from xsc_lib.xsc_lib_common.models.recognition import FaceRecognitionResult, RecognitionStatus
from xsc_lib.xsc_lib_common.interfaces.template_repository import FaceTemplateRepository

class FaceRecognizer(ABC):
    @abstractmethod
    def recognize(self, embedding: List[float]) -> FaceRecognitionResult:
        pass

class DefaultFaceRecognizer(FaceRecognizer):
    def __init__(self, repository: FaceTemplateRepository, threshold: float = 0.50):
        self.repository = repository
        self.threshold = threshold

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        arr1 = np.array(v1)
        arr2 = np.array(v2)
        return float(np.dot(arr1, arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2)))

    def recognize(self, embedding: List[float]) -> FaceRecognitionResult:
        templates = self.repository.get_active_templates()
        if not templates:
            return FaceRecognitionResult(status=RecognitionStatus.UNKNOWN)

        best_match = None
        best_similarity = -1.0

        for template in templates:
            sim = self._cosine_similarity(embedding, template.embedding)
            if sim > best_similarity:
                best_similarity = sim
                best_match = template

        if best_match and best_similarity >= self.threshold:
            person = self.repository.get_person(best_match.person_id)
            if person:
                return FaceRecognitionResult(
                    status=RecognitionStatus.MATCHED,
                    person_id=person.person_id,
                    display_name=person.name,
                    similarity=best_similarity,
                    confidence=best_similarity,
                    model_version=best_match.model_version
                )

        return FaceRecognitionResult(
            status=RecognitionStatus.UNKNOWN,
            similarity=best_similarity if best_similarity > 0 else None
        )
