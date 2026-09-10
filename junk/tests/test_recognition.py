import pytest
import numpy as np
import cv2
import os
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

from xsc_lib.xsc_lib_common.models.recognition import Person, FaceTemplate, RecognitionStatus
from xsc_lib.xsc_lib_extn.ai.arcface_aligner import ArcFaceAligner
from xsc_lib.xsc_lib_extn.ai.arcface_embedding import ArcFaceEmbeddingModel
from xsc_lib.xsc_lib_extn.db.sqlite_template_repository import SQLiteFaceTemplateRepository
from xsc_lib.xsc_lib_app.face.recognition.service import DefaultFaceRecognizer
from xsc_lib.xsc_lib_app.face.recognition.cache import TemporalRecognitionCache

from main import app

import tempfile

@pytest.fixture
def repo():
    # Use temporary file for SQLite
    fd, path = tempfile.mkstemp()
    os.close(fd)
    repo = SQLiteFaceTemplateRepository(db_path=path)
    yield repo
    os.remove(path)

@pytest.fixture
def recognizer(repo):
    return DefaultFaceRecognizer(repo, threshold=0.6)

def test_aligner_no_landmarks():
    aligner = ArcFaceAligner()
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    aligned = aligner.align(img, [])
    assert aligned.shape == (112, 112, 3)

def test_embedding_model_mock_fallback():
    model = ArcFaceEmbeddingModel(model_path="nonexistent.onnx")
    img = np.zeros((112, 112, 3), dtype=np.uint8)
    emb = model.generate_embedding(img)
    assert len(emb) == 512
    norm = np.linalg.norm(emb)
    assert np.isclose(norm, 1.0)

def test_repo_save_and_get(repo):
    person = Person(
        person_id="p1",
        name="Test User",
        status="ACTIVE",
        consent_status="GRANTED"
    )
    repo.save_person(person)
    
    fetched = repo.get_person("p1")
    assert fetched.name == "Test User"

def test_recognizer_unknown(recognizer):
    emb = np.random.normal(size=512)
    emb = (emb / np.linalg.norm(emb)).tolist()
    
    result = recognizer.recognize(emb)
    assert result.status == RecognitionStatus.UNKNOWN

def test_recognizer_match(repo, recognizer):
    person = Person(person_id="p1", name="John Doe", status="ACTIVE", consent_status="GRANTED")
    repo.save_person(person)
    
    emb = np.random.normal(size=512)
    emb = (emb / np.linalg.norm(emb)).tolist()
    
    template = FaceTemplate(
        template_id="t1",
        person_id="p1",
        embedding=emb,
        model_version="v1",
        quality_score=0.9,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    repo.save_template(template)
    
    # Exact same embedding should match 1.0
    result = recognizer.recognize(emb)
    assert result.status == RecognitionStatus.MATCHED
    assert result.person_id == "p1"
    assert result.display_name == "John Doe"
    assert np.isclose(result.similarity, 1.0)

def test_temporal_cache():
    cache = TemporalRecognitionCache()
    cache.set("cam1", "sess1", 42, FaceRecognitionResult(status=RecognitionStatus.MATCHED, person_id="p1", display_name="John Doe", similarity=0.95))
    
    res = cache.get("cam1", "sess1", 42)
    assert res is not None
    assert res.status == RecognitionStatus.MATCHED
    
    cache.clear_session("cam1", "sess1")
    assert cache.get("cam1", "sess1", 42) is None

# Needs to be imported inside test to avoid circular/unresolved references if not careful
from xsc_lib.xsc_lib_common.models.recognition import FaceRecognitionResult
