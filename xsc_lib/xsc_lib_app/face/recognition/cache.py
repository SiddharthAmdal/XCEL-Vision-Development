from typing import Dict, Optional
from xsc_lib.xsc_lib_common.models.recognition import FaceRecognitionResult, RecognitionStatus

class TemporalRecognitionCache:
    """
    Caches recognition results by (camera_id, session_id, track_id)
    to prevent expensive re-recognitions for the same track.
    """
    def __init__(self):
        # Dict[str, FaceRecognitionResult]
        # Key format: f"{camera_id}_{session_id}_{track_id}"
        self._cache: Dict[str, FaceRecognitionResult] = {}

    def get(self, camera_id: str, session_id: str, track_id: int) -> Optional[FaceRecognitionResult]:
        key = f"{camera_id}_{session_id}_{track_id}"
        return self._cache.get(key)

    def set(self, camera_id: str, session_id: str, track_id: int, result: FaceRecognitionResult) -> None:
        key = f"{camera_id}_{session_id}_{track_id}"
        # We only cache strong positive results (MATCHED). 
        # If it was UNKNOWN, NO_FACE, or LOW_QUALITY, we must try again on subsequent frames
        # as face angle, lighting, or distance may improve.
        if result.status == RecognitionStatus.MATCHED:
            self._cache[key] = result

    def clear_session(self, camera_id: str, session_id: str) -> None:
        prefix = f"{camera_id}_{session_id}_"
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._cache[k]
