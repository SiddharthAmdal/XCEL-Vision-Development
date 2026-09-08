import httpx
import json

camera_id = "ava1.ring.device.3A3O2F43AXLFYFBY77FDT6RQ6TJE2D3FXK6IPDEUXQICP235MTBOGWTOGYE4JIN3WM2HJRVFJ3KH5SZSRNATIZJR5TDXTZRL"
session_id = "test_live_session"

url = f"http://localhost:8000/api/v1/cameras/{camera_id}/analyze-frame"
files = {'file': ('frame.jpg', open('/Users/Siddharth/Documents/My pics/Me/1BM23IS243.jpg', 'rb'), 'image/jpeg')}
data = {'session_id': session_id}

print("Submitting frame to AI pipeline...")
with httpx.Client() as client:
    response = client.post(url, headers={'Authorization': 'Bearer dev_token'}, files=files, data=data)

if response.status_code == 200:
    res = response.json()
    print("Pipeline Output:")
    print(json.dumps(res, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
