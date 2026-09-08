import cv2
import numpy as np
import uuid
from ultralytics import YOLO
from xsc_lib.xsc_lib_extn.ai.yunet import YuNetFaceDetector
from xsc_lib.xsc_lib_extn.ai.opencv_quality import OpenCVFaceQualityAnalyzer

print("=== Starting Diagnostic ===")
image_path = "/Users/Siddharth/.gemini/antigravity-ide/brain/da602d0b-ef44-4675-8ccf-4cb9cafdcd69/video_player_overlay_1787224095004.png"
frame = cv2.imread(image_path)
if frame is None:
    print("Could not load image.")
    exit(1)

# Resize to match the 640 width canvas used by the frontend
h_orig, w_orig = frame.shape[:2]
new_w = 640
new_h = int((h_orig / w_orig) * 640)
frame = cv2.resize(frame, (new_w, new_h))

h_frame, w_frame = frame.shape[:2]
print(f"Loaded frame: {w_frame}x{h_frame}")

model = YOLO("yolov8n.pt")
face_detector = YuNetFaceDetector()
quality_analyzer = OpenCVFaceQualityAnalyzer()

results = model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[0], verbose=False)

detections = []
for result in results:
    boxes = result.boxes
    if boxes is not None and boxes.id is not None:
        for box, track_id, conf in zip(boxes.xyxy, boxes.id, boxes.conf):
            x1, y1, x2, y2 = box.tolist()
            detections.append({
                'track_id': int(track_id.item()),
                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                'conf': float(conf.item())
            })

print(f"YOLO detected {len(detections)} persons.")

global_faces = []
for idx, det in enumerate(detections):
    px1, py1, px2, py2 = det['bbox']
    pad_w = int((px2 - px1) * 0.1)
    pad_h = int((py2 - py1) * 0.1)
    
    cx1 = max(0, px1 - pad_w)
    cy1 = max(0, py1 - pad_h)
    cx2 = min(w_frame, px2 + pad_w)
    cy2 = min(h_frame, py2 + pad_h)
    
    print(f"\n--- Person {idx+1} (Track {det['track_id']}) ---")
    print(f"Bounding Box: {px1},{py1} to {px2},{py2}")
    print(f"Crop Box: {cx1},{cy1} to {cx2},{cy2} (Size: {cx2-cx1}x{cy2-cy1})")
    
    crop = frame[cy1:cy2, cx1:cx2]
    
    local_faces = face_detector.detect_faces(crop)
    print(f"YuNet detected {len(local_faces)} faces in crop.")
    
    for local_box, conf in local_faces:
        lx1, ly1, lx2, ly2 = local_box
        gx1 = cx1 + lx1
        gy1 = cy1 + ly1
        gx2 = cx1 + lx2
        gy2 = cy1 + ly2
        print(f"  Face {conf:.3f}: Local {local_box} -> Global {gx1},{gy1} to {gx2},{gy2}")
        global_faces.append(((gx1, gy1, gx2, gy2), conf))

print("\n--- Global Faces Deduplication ---")
unique_faces = []
def compute_iou(boxA, boxB):
    xA, yA = max(boxA[0], boxB[0]), max(boxA[1], boxB[1])
    xB, yB = min(boxA[2], boxB[2]), min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0: return 0.0
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea)

for g_face, g_conf in global_faces:
    is_dup = False
    for u_face, _ in unique_faces:
        if compute_iou(g_face, u_face) > 0.5:
            is_dup = True
            break
    if not is_dup:
        unique_faces.append((g_face, g_conf))
print(f"Unique faces after deduplication: {len(unique_faces)}")

print("\n--- Quality Analysis ---")
for idx, (box, conf) in enumerate(unique_faces):
    fx1, fy1, fx2, fy2 = box
    face_crop = frame[fy1:fy2, fx1:fx2]
    quality = quality_analyzer.analyze_quality(face_crop)
    print(f"Face {idx+1} Quality:")
    print(f"  Width: {quality.width} (min {quality_analyzer.min_width})")
    print(f"  Height: {quality.height} (min {quality_analyzer.min_height})")
    print(f"  Blur: {quality.blur_score:.2f} (min {quality_analyzer.min_blur})")
    print(f"  Brightness: {quality.brightness:.2f} (min {quality_analyzer.min_brightness})")
    print(f"  Meets Threshold: {quality.meets_threshold}")
