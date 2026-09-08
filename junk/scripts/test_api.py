import requests
import cv2

image_path = "/Users/Siddharth/.gemini/antigravity-ide/brain/da602d0b-ef44-4675-8ccf-4cb9cafdcd69/video_player_overlay_1787224095004.png"
frame = cv2.imread(image_path)
h_orig, w_orig = frame.shape[:2]
new_w = 640
new_h = int((h_orig / w_orig) * 640)
frame = cv2.resize(frame, (new_w, new_h))
cv2.imwrite('/tmp/test_api.jpg', frame)

with open('/tmp/test_api.jpg', 'rb') as f:
    files = {'file': ('test_api.jpg', f, 'image/jpeg')}
    data = {'session_id': 'test_session'}
    headers = {'Authorization': 'Bearer test-token'}
    response = requests.post('http://localhost:8000/api/v1/cameras/TS_RING_01/analyze-frame', files=files, data=data, headers=headers)

print(f"Status: {response.status_code}")
try:
    import json
    parsed = response.json()
    print("Persons:", parsed.get("persons"))
    print("Faces Length:", len(parsed.get("faces", [])))
    print("Faces Data:", json.dumps(parsed.get("faces", []), indent=2))
except Exception as e:
    print("Failed to decode JSON:", e)
