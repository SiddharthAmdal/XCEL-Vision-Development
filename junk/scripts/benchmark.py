import time
import os
import cv2
import psutil
import json

results = {}

# 1. DeepFace Evaluation
print("--- Evaluating DeepFace ---")
start_startup = time.time()
try:
    from deepface import DeepFace
    deepface_available = True
except ImportError:
    deepface_available = False
    print("DeepFace not installed.")
end_startup = time.time()

if deepface_available:
    results["deepface"] = {"startup_time": end_startup - start_startup}
    print(f"DeepFace Startup Time: {results['deepface']['startup_time']:.2f}s")
    
    img_path = "/tmp/lena.jpg"
    
    print("Warmup DeepFace (downloads models if needed)...")
    try:
        DeepFace.extract_faces(img_path, detector_backend="retinaface", enforce_detection=False)
        DeepFace.analyze(img_path, actions=["emotion"], detector_backend="skip", enforce_detection=False)
        print("Warmup finished.")
        
        runs = 3
        
        start_det = time.time()
        for _ in range(runs):
            DeepFace.extract_faces(img_path, detector_backend="retinaface", enforce_detection=False)
        end_det = time.time()
        det_latency = ((end_det - start_det) / runs) * 1000
        results["deepface"]["retinaface_latency_ms"] = det_latency
        print(f"RetinaFace Avg Latency: {det_latency:.2f}ms")
        
        start_exp = time.time()
        for _ in range(runs):
            DeepFace.analyze(img_path, actions=["emotion"], detector_backend="skip", enforce_detection=False)
        end_exp = time.time()
        exp_latency = ((end_exp - start_exp) / runs) * 1000
        results["deepface"]["emotion_latency_ms"] = exp_latency
        print(f"Emotion Avg Latency: {exp_latency:.2f}ms")
        
        mem_info = psutil.Process(os.getpid()).memory_info()
        results["deepface"]["memory_mb"] = mem_info.rss / (1024 * 1024)
        print(f"Memory Usage: {results['deepface']['memory_mb']:.2f} MB")
        
    except Exception as e:
        print(f"Error evaluating DeepFace: {e}")

# 2. Lightweight ONNX Evaluation (YuNet)
print("\n--- Evaluating Lightweight ONNX (YuNet) ---")
yunet_path = "/tmp/face_detection_yunet_2023mar.onnx"
img = cv2.imread("/tmp/lena.jpg")

if os.path.exists(yunet_path) and img is not None:
    start_startup = time.time()
    h, w = img.shape[:2]
    yunet = cv2.FaceDetectorYN.create(yunet_path, "", (w, h), score_threshold=0.5)
    end_startup = time.time()
    
    results["yunet"] = {"startup_time": end_startup - start_startup}
    print(f"YuNet Startup Time: {results['yunet']['startup_time']:.4f}s")
    
    # Warmup
    yunet.setInputSize((w, h))
    yunet.detect(img)
    
    runs = 10
    start_det = time.time()
    for _ in range(runs):
        yunet.detect(img)
    end_det = time.time()
    det_latency = ((end_det - start_det) / runs) * 1000
    results["yunet"]["detection_latency_ms"] = det_latency
    print(f"YuNet Avg Latency: {det_latency:.2f}ms")
    
    mem_info = psutil.Process(os.getpid()).memory_info()
    results["yunet"]["memory_mb"] = mem_info.rss / (1024 * 1024)
    print(f"Memory Usage: {results['yunet']['memory_mb']:.2f} MB")

with open("/tmp/eval_results.json", "w") as f:
    json.dump(results, f, indent=2)
