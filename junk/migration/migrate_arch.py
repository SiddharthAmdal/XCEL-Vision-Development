import os
import shutil
import re

# Define the structure
BASE = "xsc_lib"
COMMON = f"{BASE}/xsc_lib_common"
EXTN = f"{BASE}/xsc_lib_extn"
APP = f"{BASE}/xsc_lib_app"

dirs_to_create = [
    f"{COMMON}/models",
    f"{COMMON}/interfaces",
    f"{COMMON}/api",
    f"{EXTN}/ring",
    f"{EXTN}/ai",
    f"{EXTN}/db",
    f"{APP}/ai",
    f"{APP}/analytics",
    f"{APP}/face",
    f"{APP}/face/recognition",
    f"{APP}/camera",
    f"{APP}/api/routers",
]

for d in dirs_to_create:
    os.makedirs(d, exist_ok=True)
    # create __init__.py recursively
    parts = d.split('/')
    curr = ""
    for p in parts:
        curr = f"{curr}/{p}" if curr else p
        init_path = f"{curr}/__init__.py"
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("")

# File moves
moves = [
    # Common
    ("config.py", f"{COMMON}/config.py"),
    ("database.py", f"{COMMON}/database.py"),
    ("ai/models.py", f"{COMMON}/models/ai.py"),
    ("ai/analytics/models.py", f"{COMMON}/models/analytics.py"),
    ("ai/face/quality.py", f"{COMMON}/models/face.py"),
    ("ai/face/recognition/models.py", f"{COMMON}/models/recognition.py"),
    ("camera/models.py", f"{COMMON}/models/camera.py"),
    ("ai/face/detector.py", f"{COMMON}/interfaces/face_detector.py"),
    ("ai/face/expression.py", f"{COMMON}/interfaces/face_expression.py"),
    ("camera/provider.py", f"{COMMON}/interfaces/camera_provider.py"),
    
    # Extn
    ("ring/client.py", f"{EXTN}/ring/client.py"),
    ("ring/models.py", f"{EXTN}/ring/models.py"),
    ("ring/oauth.py", f"{EXTN}/ring/oauth.py"),
    ("ring/provider.py", f"{EXTN}/ring/provider.py"),
    ("ring/webhook.py", f"{EXTN}/ring/webhook.py"),
    ("ai/face/yunet.py", f"{EXTN}/ai/yunet.py"),
    ("ai/face/ferplus_expression.py", f"{EXTN}/ai/ferplus_expression.py"),
    ("ai/face/opencv_quality.py", f"{EXTN}/ai/opencv_quality.py"),
    ("ai/face/recognition/aligner.py", f"{EXTN}/ai/arcface_aligner.py"),
    
    # App
    ("camera/service.py", f"{APP}/camera/service.py"),
    ("ai/pipeline.py", f"{APP}/ai/pipeline.py"),
    ("ai/analytics/engine.py", f"{APP}/analytics/engine.py"),
    ("ai/analytics/activity.py", f"{APP}/analytics/activity.py"),
    ("ai/analytics/behavioral.py", f"{APP}/analytics/behavioral.py"),
    ("ai/face/association.py", f"{APP}/face/association.py"),
    ("ai/face/recognition/cache.py", f"{APP}/face/recognition/cache.py"),
    ("ai/face/recognition/service.py", f"{APP}/face/recognition/service.py"),
    ("api/dependencies.py", f"{APP}/api/dependencies.py"),
    ("api/routers/analytics.py", f"{APP}/api/routers/analytics.py"),
    ("api/routers/behavior.py", f"{APP}/api/routers/behavior.py"),
    ("api/routers/cameras.py", f"{APP}/api/routers/cameras.py"),
    ("api/routers/recognition.py", f"{APP}/api/routers/recognition.py"),
    ("ring/router.py", f"{APP}/api/routers/ring.py"),
]

for src, dst in moves:
    if os.path.exists(src):
        os.rename(src, dst)

# Special splits:
# embedding.py -> common/interfaces/embedding_model.py AND extn/ai/arcface_embedding.py
with open("ai/face/recognition/embedding.py", "r") as f:
    content = f.read()

common_embedding = """from abc import ABC, abstractmethod
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
"""
with open(f"{COMMON}/interfaces/embedding_model.py", "w") as f:
    f.write(common_embedding)

extn_embedding = content.replace("class FaceEmbeddingModel(ABC):", "# FaceEmbeddingModel interface is in common")
extn_embedding = extn_embedding.replace(common_embedding, "") # rough
extn_embedding = "import cv2\nimport numpy as np\nimport os\nfrom typing import List\nfrom xsc_lib.xsc_lib_common.interfaces.embedding_model import FaceEmbeddingModel\n\n" + extn_embedding[extn_embedding.find("class ArcFaceEmbeddingModel"):]
with open(f"{EXTN}/ai/arcface_embedding.py", "w") as f:
    f.write(extn_embedding)

os.remove("ai/face/recognition/embedding.py")


# repository.py -> common/interfaces/template_repository.py AND extn/db/sqlite_template_repository.py
with open("ai/face/recognition/repository.py", "r") as f:
    content = f.read()

common_repo = """from abc import ABC, abstractmethod
from typing import List, Optional
from xsc_lib.xsc_lib_common.models.recognition import FaceTemplate, Person

class FaceTemplateRepository(ABC):
    @abstractmethod
    def get_person(self, person_id: str) -> Optional[Person]:
        pass

    @abstractmethod
    def create_person(self, person: Person) -> Person:
        pass

    @abstractmethod
    def get_active_templates(self) -> List[FaceTemplate]:
        pass

    @abstractmethod
    def add_template(self, template: FaceTemplate):
        pass
"""
with open(f"{COMMON}/interfaces/template_repository.py", "w") as f:
    f.write(common_repo)

extn_repo = "import sqlite3\nimport json\nimport uuid\nfrom typing import List, Optional\nfrom datetime import datetime\nfrom xsc_lib.xsc_lib_common.models.recognition import FaceTemplate, Person, ConsentStatus\nfrom xsc_lib.xsc_lib_common.interfaces.template_repository import FaceTemplateRepository\n\n" + content[content.find("class SQLiteFaceTemplateRepository"):]
with open(f"{EXTN}/db/sqlite_template_repository.py", "w") as f:
    f.write(extn_repo)

os.remove("ai/face/recognition/repository.py")


# Now, do global import replacements in Python files.
# Map old prefixes to new prefixes
import_replacements = [
    (r'from xsc_lib.xsc_lib_common.config import', r'from xsc_lib.xsc_lib_common.config import'),
    (r'from xsc_lib.xsc_lib_common import config', r'from xsc_lib.xsc_lib_common from xsc_lib.xsc_lib_common import config'),
    (r'from xsc_lib.xsc_lib_common.database import', r'from xsc_lib.xsc_lib_common.database import'),
    (r'from xsc_lib.xsc_lib_common import database', r'from xsc_lib.xsc_lib_common from xsc_lib.xsc_lib_common import database'),
    
    (r'from ai\.models import', r'from xsc_lib.xsc_lib_common.models.ai import'),
    (r'from ai\.analytics\.models import', r'from xsc_lib.xsc_lib_common.models.analytics import'),
    (r'from ai\.face\.quality import', r'from xsc_lib.xsc_lib_common.models.face import'),
    (r'from ai\.face\.recognition\.models import', r'from xsc_lib.xsc_lib_common.models.recognition import'),
    (r'from camera\.models import', r'from xsc_lib.xsc_lib_common.models.camera import'),
    (r'from ring\.models import', r'from xsc_lib.xsc_lib_extn.ring.models import'),
    
    (r'from ai\.face\.detector import', r'from xsc_lib.xsc_lib_common.interfaces.face_detector import'),
    (r'from ai\.face\.expression import', r'from xsc_lib.xsc_lib_common.interfaces.face_expression import'),
    (r'from camera\.provider import', r'from xsc_lib.xsc_lib_common.interfaces.camera_provider import'),
    (r'from ai\.face\.recognition\.embedding import FaceEmbeddingModel', r'from xsc_lib.xsc_lib_common.interfaces.embedding_model import FaceEmbeddingModel'),
    (r'from ai\.face\.recognition\.embedding import ArcFaceEmbeddingModel', r'from xsc_lib.xsc_lib_extn.ai.arcface_embedding import ArcFaceEmbeddingModel'),
    (r'from ai\.face\.recognition\.repository import FaceTemplateRepository', r'from xsc_lib.xsc_lib_common.interfaces.template_repository import FaceTemplateRepository'),
    (r'from ai\.face\.recognition\.repository import SQLiteFaceTemplateRepository', r'from xsc_lib.xsc_lib_extn.db.sqlite_template_repository import SQLiteFaceTemplateRepository'),
    
    (r'from ring\.client import', r'from xsc_lib.xsc_lib_extn.ring.client import'),
    (r'from ring\.oauth import', r'from xsc_lib.xsc_lib_extn.ring.oauth import'),
    (r'from ring\.provider import', r'from xsc_lib.xsc_lib_extn.ring.provider import'),
    (r'from ring\.webhook import', r'from xsc_lib.xsc_lib_extn.ring.webhook import'),
    (r'from ring\.router import', r'from xsc_lib.xsc_lib_app.api.routers.ring import'),
    
    (r'from ai\.face\.yunet import', r'from xsc_lib.xsc_lib_extn.ai.yunet import'),
    (r'from ai\.face\.ferplus_expression import', r'from xsc_lib.xsc_lib_extn.ai.ferplus_expression import'),
    (r'from ai\.face\.opencv_quality import', r'from xsc_lib.xsc_lib_extn.ai.opencv_quality import'),
    (r'from ai\.face\.recognition\.aligner import', r'from xsc_lib.xsc_lib_extn.ai.arcface_aligner import'),
    
    (r'from camera\.service import', r'from xsc_lib.xsc_lib_app.camera.service import'),
    (r'from ai\.pipeline import', r'from xsc_lib.xsc_lib_app.ai.pipeline import'),
    (r'from ai\.analytics\.engine import', r'from xsc_lib.xsc_lib_app.analytics.engine import'),
    (r'from ai\.analytics\.activity import', r'from xsc_lib.xsc_lib_app.analytics.activity import'),
    (r'from ai\.analytics\.behavioral import', r'from xsc_lib.xsc_lib_app.analytics.behavioral import'),
    (r'from ai\.face\.association import', r'from xsc_lib.xsc_lib_app.face.association import'),
    (r'from ai\.face\.recognition\.cache import', r'from xsc_lib.xsc_lib_app.face.recognition.cache import'),
    (r'from ai\.face\.recognition\.service import', r'from xsc_lib.xsc_lib_app.face.recognition.service import'),
    
    (r'from api\.dependencies import', r'from xsc_lib.xsc_lib_app.api.dependencies import'),
    (r'from api\.routers import', r'from xsc_lib.xsc_lib_app.api.routers import'),
    
    (r'from \.models import', r'from .models import'), # keep relative but maybe unsafe? Let's rely on explicit if needed
]

import_replacements_exact = [
    ("api.routers", "xsc_lib.xsc_lib_app.api.routers"),
    ("ring.router", "xsc_lib.xsc_lib_app.api.routers.ring"),
]

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    new_content = content
    for pattern, repl in import_replacements:
        new_content = re.sub(pattern, repl, new_content)
    
    # Also handle `from ring import ...` that wasn't caught
    new_content = re.sub(r'^from ring ', r'from xsc_lib.xsc_lib_extn.ring ', new_content, flags=re.MULTILINE)
    new_content = re.sub(r'^import ring\.', r'import xsc_lib.xsc_lib_extn.ring.', new_content, flags=re.MULTILINE)
    new_content = re.sub(r'^from api\.', r'from xsc_lib.xsc_lib_app.api.', new_content, flags=re.MULTILINE)
    new_content = re.sub(r'^from ai\.', r'from xsc_lib.xsc_lib_app.ai.', new_content, flags=re.MULTILINE)
    
    # Fix the ones that got mapped wrong by the greedy above
    new_content = new_content.replace("xsc_lib.xsc_lib_common.models.ai", "xsc_lib.xsc_lib_common.models.ai")
    new_content = new_content.replace("xsc_lib.xsc_lib_common.models.analytics", "xsc_lib.xsc_lib_common.models.analytics")
    new_content = new_content.replace("xsc_lib.xsc_lib_common.models.face", "xsc_lib.xsc_lib_common.models.face")
    new_content = new_content.replace("xsc_lib.xsc_lib_common.models.recognition", "xsc_lib.xsc_lib_common.models.recognition")
    new_content = new_content.replace("xsc_lib.xsc_lib_common.interfaces.face_detector", "xsc_lib.xsc_lib_common.interfaces.face_detector")
    new_content = new_content.replace("xsc_lib.xsc_lib_common.interfaces.face_expression", "xsc_lib.xsc_lib_common.interfaces.face_expression")
    new_content = new_content.replace("xsc_lib.xsc_lib_extn.ai.yunet", "xsc_lib.xsc_lib_extn.ai.yunet")
    new_content = new_content.replace("xsc_lib.xsc_lib_extn.ai.ferplus_expression", "xsc_lib.xsc_lib_extn.ai.ferplus_expression")
    new_content = new_content.replace("xsc_lib.xsc_lib_extn.ai.opencv_quality", "xsc_lib.xsc_lib_extn.ai.opencv_quality")
    new_content = new_content.replace("xsc_lib.xsc_lib_extn.ai.arcface_aligner", "xsc_lib.xsc_lib_extn.ai.arcface_aligner")
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)

py_files = []
for root, _, files in os.walk("."):
    if "node_modules" in root or ".git" in root or "__pycache__" in root or "venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            py_files.append(os.path.join(root, file))

for pf in py_files:
    process_file(pf)

# Remove old empty dirs
for d in ["ai/face/recognition", "ai/face", "ai/analytics", "ai", "camera", "ring", "api/routers", "api"]:
    if os.path.exists(d) and not os.listdir(d):
        os.rmdir(d)
