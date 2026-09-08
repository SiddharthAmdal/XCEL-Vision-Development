from abc import ABC, abstractmethod
from typing import List, Optional
from xsc_lib.xsc_lib_common.models.recognition import FaceTemplate, Person

class FaceTemplateRepository(ABC):
    @abstractmethod
    def get_person(self, person_id: str) -> Optional[Person]:
        pass

    @abstractmethod
    def save_person(self, person: Person) -> None:
        pass

    @abstractmethod
    def get_active_templates(self) -> List[FaceTemplate]:
        pass

    @abstractmethod
    def save_template(self, template: FaceTemplate) -> None:
        pass
