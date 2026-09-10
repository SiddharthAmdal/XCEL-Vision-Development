import pytest
from xsc_lib.xsc_lib_app.face.recognition.cache import TemporalRecognitionCache
from xsc_lib.xsc_lib_common.models.recognition import FaceRecognitionResult, RecognitionStatus

def test_matched_is_cached():
    cache = TemporalRecognitionCache()
    res = FaceRecognitionResult(status=RecognitionStatus.MATCHED, person_id="user123")
    cache.set("cam1", "sess1", 1, res)
    cached = cache.get("cam1", "sess1", 1)
    assert cached is not None
    assert cached.status == RecognitionStatus.MATCHED
    assert cached.person_id == "user123"

def test_unknown_is_not_cached():
    cache = TemporalRecognitionCache()
    res = FaceRecognitionResult(status=RecognitionStatus.UNKNOWN)
    cache.set("cam1", "sess1", 1, res)
    assert cache.get("cam1", "sess1", 1) is None

def test_low_quality_is_not_cached():
    cache = TemporalRecognitionCache()
    res = FaceRecognitionResult(status=RecognitionStatus.LOW_QUALITY)
    cache.set("cam1", "sess1", 1, res)
    assert cache.get("cam1", "sess1", 1) is None

def test_unknown_followed_by_matched():
    cache = TemporalRecognitionCache()
    # UNKNOWN attempt 1
    cache.set("cam1", "sess1", 1, FaceRecognitionResult(status=RecognitionStatus.UNKNOWN))
    assert cache.get("cam1", "sess1", 1) is None
    
    # UNKNOWN attempt 2
    cache.set("cam1", "sess1", 1, FaceRecognitionResult(status=RecognitionStatus.UNKNOWN))
    assert cache.get("cam1", "sess1", 1) is None
    
    # MATCHED attempt 3
    matched_res = FaceRecognitionResult(status=RecognitionStatus.MATCHED, person_id="user123")
    cache.set("cam1", "sess1", 1, matched_res)
    assert cache.get("cam1", "sess1", 1) is not None
    assert cache.get("cam1", "sess1", 1).status == RecognitionStatus.MATCHED

def test_matched_remains_cached():
    cache = TemporalRecognitionCache()
    matched_res = FaceRecognitionResult(status=RecognitionStatus.MATCHED, person_id="user123")
    cache.set("cam1", "sess1", 1, matched_res)
    
    for _ in range(5):
        cached = cache.get("cam1", "sess1", 1)
        assert cached is not None
        assert cached.status == RecognitionStatus.MATCHED

def test_session_isolation():
    cache = TemporalRecognitionCache()
    matched_res = FaceRecognitionResult(status=RecognitionStatus.MATCHED, person_id="user123")
    cache.set("cam1", "sess1", 1, matched_res)
    
    assert cache.get("cam1", "sess2", 1) is None
    assert cache.get("cam2", "sess1", 1) is None
