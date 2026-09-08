import time
import os
import cv2
import psutil
import numpy as np

print("--- Evaluating Lightweight ONNX Expression (FER+) ---")
onnx_path = "ai/models/weights/emotion-ferplus-8.onnx"
img_path = "/tmp/lena.jpg"
img = cv2.imread(img_path)

if os.path.exists(onnx_path) and img is not None:
    # Prepare dummy face crop
    face_crop = cv2.resize(img, (64, 64))
    face_gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    
    start_startup = time.time()
    net = cv2.dnn.readNetFromONNX(onnx_path)
    end_startup = time.time()
    
    print(f"Expression Model Size: {os.path.getsize(onnx_path) / (1024*1024):.2f} MB")
    print(f"Startup Time: {end_startup - start_startup:.4f}s")
    
    # Warmup
    blob = cv2.dnn.blobFromImage(face_gray, 1.0, (64, 64), (0, 0, 0), swapRB=False, crop=False)
    net.setInput(blob)
    net.forward()
    
    runs = 100
    latencies = []
    
    start_det = time.time()
    for _ in range(runs):
        t0 = time.time()
        net.setInput(blob)
        net.forward()
        t1 = time.time()
        latencies.append((t1 - t0) * 1000)
        
    end_det = time.time()
    
    avg_latency = sum(latencies) / runs
    latencies.sort()
    p50 = latencies[int(0.5 * len(latencies))]
    p95 = latencies[int(0.95 * len(latencies))]
    
    print(f"Avg Latency: {avg_latency:.2f}ms")
    print(f"P50 Latency: {p50:.2f}ms")
    print(f"P95 Latency: {p95:.2f}ms")
    
    mem_info = psutil.Process(os.getpid()).memory_info()
    print(f"Memory Usage: {mem_info.rss / (1024 * 1024):.2f} MB")
else:
    print("Files missing or image load failed.")
