import time
import os
import psutil
import cv2
from xsc_lib.xsc_lib_app.ai.pipeline import VideoAIPipeline

pipeline = VideoAIPipeline()

img = cv2.imread("/tmp/lena.jpg")
if img is None:
    print("Could not load image.")
    exit(1)

_, img_encoded = cv2.imencode('.jpg', img)
img_bytes = img_encoded.tobytes()

print("--- Benchmarking Concrete AI Pipeline (Phase 6.2) ---")
start_init = time.time()
res = pipeline.process_frame("bench_cam", "bench_session", img_bytes)
end_init = time.time()
print(f"Cold Initialization + Warmup Time: {end_init - start_init:.4f}s")
print(f"Persons detected in warmup: {res.persons}, Faces detected: {len(res.faces)}")

runs = 50
latencies = []
start_total = time.time()
for _ in range(runs):
    t0 = time.time()
    pipeline.process_frame("bench_cam", "bench_session", img_bytes)
    t1 = time.time()
    latencies.append((t1 - t0) * 1000)
    
end_total = time.time()
avg_latency = ((end_total - start_total) / runs) * 1000

latencies.sort()
p95 = latencies[int(0.95 * len(latencies))]

print(f"Average Pipeline Latency: {avg_latency:.2f}ms")
print(f"P95 Pipeline Latency: {p95:.2f}ms")

mem_info = psutil.Process(os.getpid()).memory_info()
print(f"Pipeline Memory Usage: {mem_info.rss / (1024 * 1024):.2f} MB")
