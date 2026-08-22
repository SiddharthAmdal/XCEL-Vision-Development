import pytest
from datetime import datetime, timedelta
from ai.analytics.engine import SessionAnalyticsEngine
from ai.models import Detection

def test_activity_state_moving_and_stationary():
    engine = SessionAnalyticsEngine()
    engine.initialize_session("cam1", "sess1")
    
    t0 = datetime.utcnow()
    # Person at x=100
    det = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(80, 80, 120, 120)) # centroid: (100, 100)
    engine.process_detections("cam1", "sess1", [det], [], t0)
    
    # Needs to be > 2 seconds for non-INSUFFICIENT_EVIDENCE
    t1 = t0 + timedelta(seconds=3)
    det.bounding_box = (82, 82, 122, 122) # centroid: (102, 102) - moved 2 pixels
    engine.process_detections("cam1", "sess1", [det], [], t1)
    
    state = engine.get_state("cam1", "sess1")
    res = engine.activity_engine.process_advanced_analytics(state, t1)
    
    assert len(res.activities) == 1
    # max_spread = 2, threshold = 50.0. Should be STATIONARY or LOITERING if duration > 15s. duration is 3s.
    assert res.activities[0].state == "STATIONARY"
    
    # Now make it move a lot
    t2 = t1 + timedelta(seconds=1)
    det.bounding_box = (200, 200, 240, 240) # centroid (220, 220) - moved 120 pixels
    engine.process_detections("cam1", "sess1", [det], [], t2)
    
    res = engine.activity_engine.process_advanced_analytics(state, t2)
    assert res.activities[0].state == "MOVING"

def test_activity_state_loitering():
    engine = SessionAnalyticsEngine()
    engine.initialize_session("cam1", "sess1")
    
    t0 = datetime.utcnow()
    det = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(80, 80, 120, 120))
    engine.process_detections("cam1", "sess1", [det], [], t0)
    
    # Advance time beyond loitering threshold (15s) with minimal movement
    t1 = t0 + timedelta(seconds=16)
    det.bounding_box = (85, 85, 125, 125)
    engine.process_detections("cam1", "sess1", [det], [], t1)
    
    state = engine.get_state("cam1", "sess1")
    res = engine.activity_engine.process_advanced_analytics(state, t1)
    
    assert res.activities[0].state == "LOITERING"

def test_proximity_interaction():
    engine = SessionAnalyticsEngine()
    engine.initialize_session("cam1", "sess1")
    
    t0 = datetime.utcnow()
    det1 = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(100, 100, 140, 140)) # centroid 120, 120
    det2 = Detection(track_id=2, class_name="person", confidence=0.9, bounding_box=(150, 150, 190, 190)) # centroid 170, 170
    
    # distance = sqrt(50^2 + 50^2) = 70.7. threshold = 80. So they are in PROXIMITY.
    engine.process_detections("cam1", "sess1", [det1, det2], [], t0)
    
    # Fast forward 6 seconds (threshold = 5s) to trigger SUSTAINED_PROXIMITY
    t1 = t0 + timedelta(seconds=6)
    engine.process_detections("cam1", "sess1", [det1, det2], [], t1)
    
    state = engine.get_state("cam1", "sess1")
    res = engine.activity_engine.process_advanced_analytics(state, t1)
    
    assert len(res.interactions) == 1
    assert res.interactions[0].state == "SUSTAINED_PROXIMITY"
    assert res.interactions[0].track_a == 1
    assert res.interactions[0].track_b == 2

def test_heatmap_accumulation():
    engine = SessionAnalyticsEngine()
    engine.initialize_session("cam1", "sess1")
    
    t0 = datetime.utcnow()
    # Centroid at 320, 240 (center). Grid is 16x12. cell_w=40, cell_h=40. Grid x=8, y=6.
    det = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(300, 220, 340, 260))
    engine.process_detections("cam1", "sess1", [det], [], t0)
    
    state = engine.get_state("cam1", "sess1")
    assert state.heatmap_cells[6][8] == 1.0
    
    # Process again, it accumulates
    t1 = t0 + timedelta(seconds=1)
    engine.process_detections("cam1", "sess1", [det], [], t1)
    
    # Max is now 2.0. Normalized max is 1.0. 
    res = engine.activity_engine.process_advanced_analytics(state, t1)
    
    # Since 2.0 is max, 2.0/max = 1.0 in normalized
    assert res.heatmap.cells[6][8] == 1.0
    # Empty cell is 0
    assert res.heatmap.cells[0][0] == 0.0

def test_anomaly_detection():
    engine = SessionAnalyticsEngine()
    engine.initialize_session("cam1", "sess1")
    
    # Create extreme accumulation in one cell
    t0 = datetime.utcnow()
    det = Detection(track_id=1, class_name="person", confidence=0.9, bounding_box=(300, 220, 340, 260))
    for i in range(150): # Threshold is 100.0
        engine.process_detections("cam1", "sess1", [det], [], t0 + timedelta(seconds=i*0.1))
        
    state = engine.get_state("cam1", "sess1")
    res = engine.activity_engine.process_advanced_analytics(state, t0 + timedelta(seconds=15))
    
    assert len(res.anomalies) == 1
    assert res.anomalies[0].type == "MOTION_ANOMALY"
