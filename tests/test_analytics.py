import pytest
from datetime import datetime, timedelta
from ai.analytics.engine import SessionAnalyticsEngine
from ai.analytics.models import CountingLine
from ai.models import Detection

def test_session_isolation():
    engine = SessionAnalyticsEngine()
    engine.initialize_session("cam1", "sess1")
    engine.initialize_session("cam1", "sess2")
    
    dt = datetime.utcnow()
    
    det1 = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(100, 100, 200, 200))
    engine.process_detections("cam1", "sess1", [det1], dt)
    
    state1 = engine.get_state("cam1", "sess1")
    state2 = engine.get_state("cam1", "sess2")
    
    assert state1.visible_people == 1
    assert state2.visible_people == 0

def test_line_crossing_and_debounce():
    engine = SessionAnalyticsEngine()
    # Define vertical line at x=300, crossing left to right is ENTRY
    line = CountingLine(id="L1", start_point=(300, 0), end_point=(300, 500), direction="left_to_right")
    engine.initialize_session("cam1", "sess1", lines=[line])
    
    t0 = datetime.utcnow()
    # Person at x=200 (left)
    det = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(180, 200, 220, 240)) # centroid: (200, 220)
    engine.process_detections("cam1", "sess1", [det], t0)
    state = engine.get_state("cam1", "sess1")
    assert state.entries == 0
    assert state.estimated_occupancy == 0
    
    # Person at x=250 (left) - no crossing
    t1 = t0 + timedelta(seconds=1)
    det.bounding_box = (230, 200, 270, 240) # centroid (250, 220)
    engine.process_detections("cam1", "sess1", [det], t1)
    assert state.entries == 0
    
    # Person crosses to x=350 (right) -> ENTRY
    t2 = t1 + timedelta(seconds=1)
    det.bounding_box = (330, 200, 370, 240) # centroid (350, 220)
    engine.process_detections("cam1", "sess1", [det], t2)
    assert state.entries == 1
    assert state.estimated_occupancy == 1
    
    # Debounce: Person moves slightly right to x=360 -> NO new ENTRY
    t3 = t2 + timedelta(seconds=1)
    det.bounding_box = (340, 200, 380, 240) # centroid (360, 220)
    engine.process_detections("cam1", "sess1", [det], t3)
    assert state.entries == 1
    
    # Person crosses back to x=250 (left) -> EXIT
    t4 = t3 + timedelta(seconds=1)
    det.bounding_box = (230, 200, 270, 240) # centroid (250, 220)
    engine.process_detections("cam1", "sess1", [det], t4)
    assert state.exits == 1
    assert state.estimated_occupancy == 0

def test_occupancy_independence():
    engine = SessionAnalyticsEngine()
    line = CountingLine(id="L1", start_point=(300, 0), end_point=(300, 500), direction="left_to_right")
    engine.initialize_session("cam1", "sess1", lines=[line])
    
    t0 = datetime.utcnow()
    # Person appears inside zone (x=400) without crossing
    det = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(380, 200, 420, 240)) # centroid: (400, 220)
    engine.process_detections("cam1", "sess1", [det], t0)
    
    state = engine.get_state("cam1", "sess1")
    assert state.visible_people == 1
    assert state.entries == 0
    assert state.estimated_occupancy == 0
    
    # Track disappears
    # Since we keep active_tracks until timeout, simulate timeout or just verify visible_people
    # By passing empty detections, current_track_ids is empty, so visible_people becomes 0
    engine.process_detections("cam1", "sess1", [], t0 + timedelta(seconds=1))
    assert state.visible_people == 0
    assert state.estimated_occupancy == 0 # unchanged
    
def test_dwell_time():
    engine = SessionAnalyticsEngine()
    engine.initialize_session("cam1", "sess1", lines=[])
    
    t0 = datetime.utcnow()
    det = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(180, 200, 220, 240))
    engine.process_detections("cam1", "sess1", [det], t0)
    
    t1 = t0 + timedelta(seconds=10)
    engine.process_detections("cam1", "sess1", [det], t1)
    
    state = engine.get_state("cam1", "sess1")
    assert state.active_tracks[1].total_visible_duration == 10.0
