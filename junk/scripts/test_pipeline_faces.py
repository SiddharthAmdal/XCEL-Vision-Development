import cv2
import json
from xsc_lib.xsc_lib_app.ai.pipeline import VideoAIPipeline

pipeline = VideoAIPipeline()

image_path = "/Users/Siddharth/.gemini/antigravity-ide/brain/da602d0b-ef44-4675-8ccf-4cb9cafdcd69/video_player_overlay_1787224095004.png"
frame = cv2.imread(image_path)
h_orig, w_orig = frame.shape[:2]
new_w = 640
new_h = int((h_orig / w_orig) * 640)
frame = cv2.resize(frame, (new_w, new_h))

_, img_encoded = cv2.imencode('.jpg', frame)
img_bytes = img_encoded.tobytes()

res = pipeline.process_frame("test_cam", "test_session", img_bytes)

print(f"Persons: {res.persons}")
print(f"Faces: {len(res.faces)}")
for face in res.faces:
    print(f"Face Box: {face.bbox}")
    print(f"Quality: meets_threshold={face.quality.meets_threshold}")
    print(f"Expression: {face.expression}")
