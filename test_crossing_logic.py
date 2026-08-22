import logging
import sys
from datetime import datetime, timedelta
from ai.analytics.engine import SessionAnalyticsEngine, intersect, get_side, ccw
from ai.models import Detection

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

engine = SessionAnalyticsEngine()
camera_id = "test_cam"
session_id = "test_session"

# Start at X=200, Y=240, walk right to X=400
t0 = datetime.utcnow()

# Frame 1
print("--- Frame 1 ---")
det1 = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(150, 200, 250, 280)) # centroid: 200, 240
state = engine.process_detections(camera_id, session_id, [det1], t0)
track = state.active_tracks[1]
print(f"Track: current={track.current_centroid} prev={track.previous_centroid}")

# Frame 2
print("\n--- Frame 2 ---")
t1 = t0 + timedelta(milliseconds=400)
det2 = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(200, 200, 300, 280)) # centroid: 250, 240
state = engine.process_detections(camera_id, session_id, [det2], t1)
track = state.active_tracks[1]
print(f"Track: current={track.current_centroid} prev={track.previous_centroid}")

# Frame 3 (Crossing X=320)
print("\n--- Frame 3 ---")
t2 = t1 + timedelta(milliseconds=400)
det3 = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(300, 200, 400, 280)) # centroid: 350, 240
state = engine.process_detections(camera_id, session_id, [det3], t2)
track = state.active_tracks[1]
print(f"Track: current={track.current_centroid} prev={track.previous_centroid}")
print(f"Entries: {state.entries}, Exits: {state.exits}, Occupancy: {state.estimated_occupancy}")

# Check intersection manually
A = (250, 240)
B = (350, 240)
C = (320, 0)
D = (320, 480)
print("\nManual Intersect:")
print(f"ccw(A,C,D): {ccw(A,C,D)}")
print(f"ccw(B,C,D): {ccw(B,C,D)}")
print(f"ccw(A,B,C): {ccw(A,B,C)}")
print(f"ccw(A,B,D): {ccw(A,B,D)}")
print(f"intersect result: {intersect(A, B, C, D)}")
