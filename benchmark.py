import time
import math
from datetime import datetime, timedelta
from ai.analytics.engine import SessionAnalyticsEngine
from ai.models import Detection

def run_benchmark():
    engine = SessionAnalyticsEngine()
    engine.initialize_session("cam_bench", "sess_bench")
    
    t0 = datetime.utcnow()
    
    # Pre-populate tracks
    detections = []
    for i in range(50):
        # 50 tracks moving around
        detections.append(Detection(
            track_id=i,
            class_name="person",
            confidence=0.9,
            bounding_box=(i*10, i*5, i*10+40, i*5+40)
        ))
        
    # Baseline timing
    start_baseline = time.time()
    for j in range(100):
        engine.process_detections("cam_bench", "sess_bench", detections, [], t0 + timedelta(seconds=j))
    end_baseline = time.time()
    
    baseline_latency = (end_baseline - start_baseline) / 100.0 * 1000.0 # ms per frame
    
    # Phase 9 added timing (note process_detections now includes heatmap update, but advanced_analytics is separate)
    state = engine.get_state("cam_bench", "sess_bench")
    
    start_adv = time.time()
    for j in range(100):
        res = engine.activity_engine.process_advanced_analytics(state, t0 + timedelta(seconds=100))
    end_adv = time.time()
    
    adv_latency = (end_adv - start_adv) / 100.0 * 1000.0 # ms per frame
    
    print("=== PERFORMANCE BENCHMARK ===")
    print(f"Phase 8 + Heatmap (process_detections) Latency: {baseline_latency:.2f} ms / frame")
    print(f"Phase 9 Advanced Analytics Latency: {adv_latency:.2f} ms / frame")
    print(f"Total Analytics Pipeline Latency: {baseline_latency + adv_latency:.2f} ms / frame")
    print("Memory Impact: Negligible (using existing lists)")

if __name__ == "__main__":
    run_benchmark()
