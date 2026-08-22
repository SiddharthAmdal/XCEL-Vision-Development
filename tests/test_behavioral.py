import pytest
from datetime import datetime, timedelta
from ai.analytics.models import TrackHistory, BehavioralTemporalConfig
from ai.analytics.behavioral import BehavioralEngine

def test_prune_buffers():
    config = BehavioralTemporalConfig(window_seconds=5.0, max_observations=150)
    engine = BehavioralEngine(config=config)
    
    current_time = datetime.now()
    old_time = current_time - timedelta(seconds=10)
    recent_time = current_time - timedelta(seconds=2)
    
    track = TrackHistory(
        track_id=1,
        first_seen=old_time,
        last_seen=current_time,
        recent_centroids=[(old_time, (10, 10)), (recent_time, (20, 20))]
    )
    
    engine.prune_buffers(track, current_time)
    
    assert len(track.recent_centroids) == 1
    assert track.recent_centroids[0][1] == (20, 20)

def test_extract_cues_stationary():
    engine = BehavioralEngine()
    current_time = datetime.now()
    
    # Simulate stationary track
    centroids = []
    for i in range(10):
        t = current_time - timedelta(seconds=(10-i)*0.2)
        centroids.append((t, (50, 50)))
        
    track = TrackHistory(
        track_id=1,
        first_seen=centroids[0][0],
        last_seen=centroids[-1][0],
        recent_centroids=centroids,
        recent_face_visibility=[(c[0], True) for c in centroids],
        recent_expressions=[(c[0], "neutral") for c in centroids]
    )
    
    cues = engine.extract_cues(track)
    assert cues["movement_velocity"] == 0.0
    assert cues["movement_variability"] == 0.0
    assert cues["time_stationary"] > 1.5
    assert cues["expression_volatility"] == 0.0
    assert cues["neutral_happy_frequency"] == 1.0

def test_extract_cues_moving_nervous():
    engine = BehavioralEngine()
    current_time = datetime.now()
    
    # Simulate erratic track
    centroids = []
    positions = [(0,0), (100,0), (0,100), (100,100), (50,50), (150,0), (0,150), (50,150), (150,50), (100,100)]
    for i in range(10):
        t = current_time - timedelta(seconds=(10-i)*0.2)
        centroids.append((t, positions[i]))
        
    expressions = ["neutral", "fear", "surprise", "fear", "fear", "neutral", "surprise", "fear", "neutral", "surprise"]
        
    track = TrackHistory(
        track_id=1,
        first_seen=centroids[0][0],
        last_seen=centroids[-1][0],
        recent_centroids=centroids,
        recent_face_visibility=[(c[0], True) for c in centroids],
        recent_expressions=[(centroids[i][0], expressions[i]) for i in range(10)]
    )
    
    cues = engine.extract_cues(track)
    assert cues["movement_velocity"] > 50.0
    assert cues["movement_variability"] > 5.0
    assert cues["direction_change_frequency"] > 0.5
    assert cues["expression_volatility"] > 0.5
    assert cues["fear_surprise_frequency"] >= 0.5

def test_infer_indicators_insufficient():
    engine = BehavioralEngine()
    current_time = datetime.now()
    
    # Under 2 seconds
    centroids = [(current_time - timedelta(seconds=1.0), (0,0)), (current_time, (10,10))]
    track = TrackHistory(
        track_id=1,
        first_seen=centroids[0][0],
        last_seen=centroids[-1][0],
        recent_centroids=centroids
    )
    
    cues = engine.extract_cues(track)
    indicators = engine.infer_indicators(track, cues)
    
    assert indicators[0].state == "insufficient_evidence"

def test_infer_indicators_nervousness():
    engine = BehavioralEngine()
    current_time = datetime.now()
    
    # Over 2 seconds
    centroids = []
    positions = [(0,0), (100,0), (0,100), (100,100), (50,50), (150,0), (0,150), (50,150), (150,50), (100,100)]
    for i in range(10):
        t = current_time - timedelta(seconds=(10-i)*0.3) # 3 seconds total
        centroids.append((t, positions[i]))
        
    track = TrackHistory(
        track_id=1,
        first_seen=centroids[0][0],
        last_seen=centroids[-1][0],
        recent_centroids=centroids,
        recent_face_visibility=[(c[0], True) for c in centroids],
        recent_expressions=[(c[0], "fear") for c in centroids]
    )
    
    cues = engine.extract_cues(track)
    indicators = engine.infer_indicators(track, cues)
    
    nervousness = next(ind for ind in indicators if ind.state == "nervousness")
    assert nervousness.score > 0.6
    assert nervousness.confidence >= 0.5
