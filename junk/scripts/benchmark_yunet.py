import time
import os
import cv2
import psutil

print("--- Evaluating Lightweight ONNX (YuNet) ---")
yunet_path = "/tmp/face_detection_yunet_2023mar.onnx"
img_path = "/tmp/lena.jpg"
img = cv2.imread(img_path)

if os.path.exists(yunet_path) and img is not None:
    start_startup = time.time()
    h, w = img.shape[:2]
    yunet = cv2.FaceDetectorYN.create(yunet_path, "", (w, h), score_threshold=0.5)
    end_startup = time.time()
    
    print(f"YuNet Startup Time: {end_startup - start_startup:.4f}s")
    
    # Warmup
    yunet.setInputSize((w, h))
    yunet.detect(img)
    
    runs = 100
    start_det = time.time()
    for _ in range(runs):
        yunet.detect(img)
    end_det = time.time()
    det_latency = ((end_det - start_det) / runs) * 1000
    print(f"YuNet Avg Latency: {det_latency:.2f}ms")
    
    mem_info = psutil.Process(os.getpid()).memory_info()
    print(f"Memory Usage: {mem_info.rss / (1024 * 1024):.2f} MB")
else:
    print("Files missing or image load failed.")
