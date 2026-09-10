# XCEL Vision / Ring Camera AI - Engineering Handbook

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Current System Capabilities](#2-current-system-capabilities)
3. [Privacy and Security Architecture](#3-privacy-and-security-architecture)
4. [OneApp Architecture](#4-oneapp-architecture)
5. [Detailed Module-by-Module Documentation](#5-detailed-module-by-module-documentation)
6. [End-to-End Application Flow](#6-end-to-end-application-flow)
7. [AI Pipeline Deep Dive](#7-ai-pipeline-deep-dive)
8. [Data Models](#8-data-models)
9. [API Documentation](#9-api-documentation)
10. [Face Enrollment Knowledge Transfer](#10-face-enrollment-knowledge-transfer)
11. [Frontend Architecture](#11-frontend-architecture)
12. [Coordinate Systems](#12-coordinate-systems)
13. [Session and State Management](#13-session-and-state-management)
14. [Databases and Persistence](#14-databases-and-persistence)
15. [AI Models and Dependencies](#15-ai-models-and-dependencies)
16. [Why These Technologies Were Chosen](#16-why-these-technologies-were-chosen)
17. [Architectural Decisions / ADR Summary](#17-architectural-decisions--adr-summary)
18. [Known Bugs / Historical Lessons](#18-known-bugs--historical-lessons)
19. [Testing Strategy](#19-testing-strategy)
20. [Real Hardware Verification](#20-real-hardware-verification)
21. [Performance Characteristics](#21-performance-characteristics)
22. [Configuration](#22-configuration)
23. [Installation and Setup](#23-installation-and-setup)
24. [Repository Structure](#24-repository-structure)
25. [Rules for Future Development](#25-rules-for-future-development)
26. [How to Safely Modify the AI Pipeline](#26-how-to-safely-modify-the-ai-pipeline)
27. [Common Failure Modes](#27-common-failure-modes)
28. [Future Roadmap](#28-future-roadmap)
29. [Migration to the Actual OneApp Repository](#29-migration-to-the-actual-oneapp-repository)
30. [Glossary](#30-glossary)
31. [Developer Quick Reference](#31-developer-quick-reference)

---

## 1. Project Overview

**XCEL Vision** (internally developed as Ring Camera AI) is a real-time, privacy-first video analytics and AI processing engine designed to ingest live WebRTC feeds from Ring cameras and perform advanced spatial, behavioral, and biometric analysis. 

The system bridges the gap between proprietary Ring hardware and custom enterprise AI by extracting raw video via Ring's WHEP (WebRTC HTTP Ingestion Protocol) and applying a heavily optimized, multi-stage machine learning pipeline.

### System Flow
The application consumes **Live WebRTC Video** and produces **Ephemeral Analytical Metadata** alongside **Optional Biometric Matches**.

```mermaid
graph TD
    A[Ring Camera] -->|WHEP/WebRTC| B[Ring Provider]
    B -->|Stream| C[React Frontend]
    C -->|Sampled Frames 10fps| D[/analyze-frame API]
    
    subgraph VideoAIPipeline
        D --> E[YOLOv8n Person Detection]
        E --> F[ByteTrack Anonymous Tracking]
        F --> G[YuNet Face Detection]
        G --> H[OpenCV Quality Gate]
        H --> I[FERPlus Expression Analysis]
        H --> J[ArcFace Recognition]
        
        F & I & J --> K[Analytics & Behavior Engines]
    end
    
    K --> L[AIFrameResult]
    L --> M[Frontend Dashboard Overlays]
```

---

## 2. Current System Capabilities

### Camera / Ring Integration
- **Ring Authentication & OAuth:** Connects securely to Ring APIs, managing token exchange and refresh.
- **Device Discovery:** Retrieves registered cameras.
- **Camera Abstraction:** Generalized camera interfaces allowing future non-Ring hardware.
- **WebRTC/WHEP Flow:** Negotiates SDP offers/answers directly with Ring servers.

### Person AI
- **YOLOv8n Detection:** Detects class `0` (person) with bounding boxes and confidence scores.
- **ByteTrack Tracking:** Assigns a persistent `track_id` across frames within a single session.
- **Spatial Tracking:** Calculates centroids and bounding boxes to maintain continuity.

### Face AI
- **YuNet Detection:** Lightweight ONNX face detection executing exclusively within YOLO person crops to optimize CPU.
- **Face/Person Association:** Links faces to tracking IDs via bounding box intersection (IoU).
- **Quality Gate:** Measures blur (Laplacian variance) and brightness. Drops low-quality faces before expensive processing.
- **Expression Analysis:** Uses FERPlus ONNX to classify 8 affective expressions (neutral, happiness, surprise, sadness, anger, disgust, fear, contempt).

### Temporal Analytics
- **Occupancy & Counting:** Uses virtual `CountingLine`s to monitor entry/exit events.
- **Dwell Time:** Tracks total visible duration of a `track_id` in a session.
- **Spatial Debounce:** Prevents jitter from repeatedly triggering crossing logic.

### Behavioral Intelligence
- **Affective Indicators:** Derives probabilistic indicators (nervousness, engagement, calmness) using temporal buffers of movement velocity, direction changes, expression volatility, and stationary time.
- **Disclaimer:** These are strictly visual/behavioral indicators, not psychological diagnoses.

### Advanced Video Intelligence
- **Activity Classification:** Categorizes track behavior into `MOVING`, `STATIONARY`, or `LOITERING` based on dwell and centroid displacement.
- **Proximity:** Detects when two track IDs remain close for sustained periods.
- **Motion Heatmaps:** Tracks global movement distribution across the frame grid.
- **Anomaly Detection:** Flags unexpected behavior (e.g. running or restricted zones).

### Face Recognition
The complete biometric pipeline uses ArcFace:
1. **Landmarks:** YuNet extracts 5-point facial landmarks.
2. **Alignment:** Affine transformation normalizes the face to 112x112.
3. **ArcFace Embedding:** Generates a 512-dimensional vector.
4. **Cosine Similarity:** Compares against the SQLite `faces.db` template repository.
5. **Temporal Cache:** Caches ONLY `MATCHED` results to prevent early bad-angle frames from poisoning the identity for the rest of the session.

---

## 3. Privacy and Security Architecture

XCEL Vision strictly enforces the boundary between **Anonymous Tracking** and **Biometric Recognition**.

- **Anonymous Tracking (ByteTrack):** `track_id` is an ephemeral integer bound to the WebRTC session. It resets to 1 on reconnect. It carries no PII.
- **Opt-In Recognition:** Face recognition is explicitly isolated behind a Quality Gate and a configuration flag. 
- **No Face Scraping:** Unknown faces are marked `UNKNOWN` and discarded. Embeddings are never stored unless actively enrolled via the explicit API.
- **No Embeddings in API:** The frontend receives the string identity name, never the 512D vector.
- **Data Persistence:** All temporal and behavioral tracking is strictly in-memory and dies when the `session_id` ends. Only `faces.db` (enrolled templates) and `ring_tokens.db` (auth) touch the disk.

**CRITICAL DEVELOPER RULE:** Do not cross-pollinate biometric identities into the base ByteTrack ID state. Anonymity by default is a hard requirement.

---

## 4. OneApp Architecture

The codebase has been refactored to align with the standard OneApp architectural pattern.

```text
xsc_lib/
├── xsc_lib_common/  # Contracts, abstract interfaces, domain models
├── xsc_lib_extn/    # Concrete external/technology implementations
└── xsc_lib_app/     # Application orchestration and business logic
```

- **`xsc_lib_common`**: Contains purely structural classes (e.g. `Detection`, `AIFrameResult`, `CameraProvider` interface). No logic, no external dependencies like OpenCV or YOLO.
- **`xsc_lib_extn`**: Contains the "How". e.g., `yunet.py`, `sqlite_template_repository.py`, `ring/client.py`. This is the only layer allowed to import heavy ML binaries or vendor APIs.
- **`xsc_lib_app`**: Contains the "What". The `VideoAIPipeline` and `SessionAnalyticsEngine` live here. They orchestrate the models through the interfaces defined in `common` and implemented in `extn`.

---

## 5. Detailed Module-by-Module Documentation

### `xsc_lib_app.ai.pipeline.VideoAIPipeline`
- **Purpose:** Central orchestrator for per-frame ML processing.
- **Dependencies:** YOLOv8, YuNet, OpenCV Quality, FERPlus, ArcFace, AnalyticsEngine.
- **Flow:** Takes a raw frame buffer, runs YOLO -> loops detections -> crops -> runs YuNet -> associates -> evaluates quality -> FERPlus -> ArcFace -> Analytics -> Returns `AIFrameResult`.

### `xsc_lib_app.analytics.engine.SessionAnalyticsEngine`
- **Purpose:** Maintains temporal state across frames.
- **State:** Tracks `active_tracks` by `track_id`. Calculates entries/exits across virtual lines. Delegates to `BehavioralEngine` and `ActivityAnalyticsEngine`.

### `xsc_lib_extn.ring.provider.RingCameraProvider`
- **Purpose:** Implements `xsc_lib_common.interfaces.CameraProvider` for Ring.
- **Responsibility:** Handles discovery, WHEP SDP negotiation, and token refreshing via `RingClient`.

### `xsc_lib_app.face.recognition.cache.TemporalRecognitionCache`
- **Purpose:** Prevents re-running ArcFace on recognized users.
- **Key Logic:** Only `MATCHED` statuses are inserted into the cache.

---

## 6. End-to-End Application Flow

1. **Startup:** `main.py` boots FastAPI and creates DB tables.
2. **Discovery:** Frontend hits `/api/v1/cameras`. Backend uses `RingCameraProvider` to fetch devices.
3. **WebRTC:** Frontend user clicks "Live". Frontend creates RTCPeerConnection and sends SDP Offer to `/cameras/{id}/live`.
4. **WHEP:** Backend forwards SDP to Ring, gets Answer, returns it. Stream starts rendering in browser `<video>`.
5. **Sampling:** Frontend draws `<video>` to hidden `<canvas>` at ~10fps, converts to JPEG, posts to `/analyze-frame`.
6. **AI Processing:** `VideoAIPipeline` processes the JPEG, maintains temporal state, and returns JSON.
7. **Overlay:** Frontend maps AI coordinates (640x480) up to the actual browser video size and renders bounding boxes and analytics dashboards.

---

## 7. AI Pipeline Deep Dive

The strict processing order in `VideoAIPipeline.process_frame`:

1. **YOLOv8n + ByteTrack:** Extracts person bounding boxes and persistent tracking IDs.
2. **Crop Padding:** Because YOLO often crops the top of heads, the bounding box is padded upwards by 25% to ensure full face capture.
3. **YuNet:** Runs *only* inside the padded person crops.
4. **IoU Association:** Maps global face coordinates back to the person bounding boxes.
5. **Quality Gate:** Faces failing Laplacian blur tests are aborted here.
6. **FERPlus:** Analyzes expression on the face crop.
7. **Cache Check:** If `track_id` is already matched in cache, skip biometric recognition.
8. **Alignment + ArcFace:** Normalizes face via 5-point landmarks, embeds, checks SQLite via Cosine Similarity.
9. **Analytics:** Updates behavioral and scene engines.

---

## 8. Data Models

- **`Detection`**: Bbox, confidence, `track_id`.
- **`FaceQuality`**: Blur score, brightness, `meets_threshold` boolean.
- **`FaceDetection`**: Bbox, landmarks, linked `track_id`, expression, recognition result.
- **`TrackHistory`**: Temporal log of centroids, expressions, visibility. Ephemeral.
- **`BehavioralCues` / `AffectiveIndicator`**: Derived scores (e.g. Nervousness). Ephemeral.
- **`AIFrameResult`**: Master return object sent to frontend per frame.
- **`FaceTemplate`**: Persistent SQLite record containing the raw 512D float array.

---

## 9. API Documentation

*(Mounted on `http://localhost:8000/api/v1`)*

- **GET `/cameras`**: Returns list of discovered Ring devices.
- **POST `/cameras/{camera_id}/live`**: Accepts SDP offer, initiates WHEP, returns SDP answer and `session_id`.
- **DELETE `/cameras/{camera_id}/live/{session_id}`**: Terminates WHEP and destroys backend AI state.
- **POST `/cameras/{camera_id}/analyze-frame`**: Accepts multipart/form-data JPEG frame. Returns `AIFrameResult`.
- **GET `/analytics/occupancy`**: Returns current tracking counts and entries/exits.
- **GET `/analytics/scene`**: Returns heatmaps and active anomalies.
- **POST `/faces/enroll`**: Expects multipart image and identity metadata. Extracts ArcFace embedding and saves to SQLite.

---

## 10. Face Enrollment Knowledge Transfer

To authorize a new identity for recognition:
1. Ensure `faces.db` exists (auto-created on startup).
2. Submit a high-quality, front-facing image to `/api/v1/faces/enroll`.
3. **The flow:** YuNet detects face -> Quality Gate verifies it is sharp -> ArcFace Aligner normalizes it -> ArcFace embeds it -> Template is stored in `faces.db`.
4. Subsequent live frames run Cosine Similarity against this template. 
5. The API response explicitly omits the 512D embedding vector for security.

---

## 11. Frontend Architecture

- **`App.tsx`**: Manages dashboard state, camera selection, and capabilities grid.
- **`LiveStream.tsx`**: The core component. Manages the `RTCPeerConnection`, the hidden canvas frame sampling loop (polling `/analyze-frame`), and houses the sub-components.
- **`PersonOverlay.tsx`**: Receives `AIFrameResult` and projects 640x480 coordinates onto the dynamic browser video dimensions using CSS transforms.
- **`AnalyticsDisplay.tsx`**: Renders the temporal data (heatmaps, occupancy, behavioral scores).

---

## 12. Coordinate Systems

- **Source Video:** Depends on Ring hardware (often 1080p).
- **AI Analysis Dimensions:** The frontend downsamples frames to `640x480` before sending to the backend to conserve bandwidth and CPU.
- **Bounding Box Projection:** 
  The frontend `<PersonOverlay>` calculates scaling factors:
  `scaleX = videoClientWidth / 640`
  `scaleY = videoClientHeight / 480`
  It then multiplies the backend bounding boxes by these factors to render overlays accurately over the fluid browser video.

---

## 13. Session and State Management

Everything hinges on the tuple: `(camera_id, session_id)`.

- **Ephemeral State:** YOLO Tracker instances, `TrackHistory`, `BehavioralEngine` buffers, `TemporalRecognitionCache`, and Heatmaps are bound to `session_id`.
- **Reconnections:** If WebRTC drops and reconnects, a *new* `session_id` is generated. All ephemeral state starts fresh. `track_id` starts over at 1.
- **Cleanup:** Frontend `onClose` calls the `DELETE /live` endpoint, which triggers `pipeline.cleanup_session()`.

---

## 14. Databases and Persistence

- **`ring_tokens.db`**: Stores encrypted OAuth refresh tokens. Essential for maintaining Ring connectivity without requiring frequent manual re-authentication.
- **`faces.db`**: Stores enrolled `FaceTemplate` vectors. Contains sensitive biometric data (though un-reconstructable into an image).

---

## 15. AI Models and Dependencies

| Component | Model / File | Purpose |
| :--- | :--- | :--- |
| Person Detection | `yolov8n.pt` | Fast, general-purpose bounding boxes. |
| Tracking | `bytetrack.yaml` | Cross-frame identity association. |
| Face Detection | `face_detection_yunet_2023mar.onnx` | 5-point landmarks, highly optimized ONNX. |
| Expression | `emotion-ferplus-8.onnx` | Classifies 8 emotional states. |
| Recognition | `arcface_w600k_r50.onnx` | Generates 512D biometric embeddings. |

*Note: All models must reside in the root `models/weights/` directory.*

---

## 16. Why These Technologies Were Chosen

- **ONNX over TensorFlow/DeepFace:** DeepFace pulls in massive TF dependencies and initializes slowly. We selected raw ONNX graphs (YuNet, ArcFace, FERPlus) executed via OpenCV DNN to achieve sub-50ms inference times on CPU, making 10fps real-time possible without GPUs.
- **YOLOv8 + ByteTrack:** Chosen because it provides extremely robust occlusion handling natively.
- **FastAPI:** Native async support pairs perfectly with network-heavy WebRTC signaling and AI inference blocking.
- **SQLite:** Deferring PostgreSQL allows developers to run this fully locally without Docker compose complexity during MVP/Phase 9.

---

## 17. Architectural Decisions / ADR Summary

- **Decision: Crop Padding for Faces:** YOLO often clips the top 10% of heads. We pad the crops by 25% upward to guarantee YuNet succeeds.
- **Decision: Cache only MATCHED results:** If a face is obscured on frame 1, it yields `UNKNOWN`. If we cache `UNKNOWN`, the person is locked out forever. Caching only `MATCHED` allows continuous retries until they look at the camera.
- **Decision: OneApp xsc_lib architecture:** Enforced strictly to ensure this codebase can be seamlessly transplanted into the wider enterprise OneApp monorepo.
- **Decision: Probabilistic Behavioral Indicators:** "Nervousness" is derived from velocity + expression volatility. It is structurally labeled an indicator, not a truth, to avoid AI hallucinations masking as fact.

---

## 18. Known Bugs / Historical Lessons

- **"0 Faces Detected" Bug:** Initially, YuNet failed entirely. Root cause: ByteTrack bounding boxes were too tight on faces. Solved by the aforementioned 25% crop padding.
- **Counting Line Not Triggering:** Fast-walking individuals jumped the line entirely between frames. Solved by increasing frontend sampling to ~10fps and using cross-product intersection logic (`intersect(prev, current, L1, L2)`) rather than checking bounding box sides.
- **UNKNOWN Poisoning:** Initial temporal cache locked people as `UNKNOWN` permanently based on their first low-confidence frame. Solved by refactoring `TemporalRecognitionCache.set()`.

---

## 19. Testing Strategy

Run tests using: `PYTHONPATH=. uv run pytest`

- **`tests/`:** Contains the canonical regression suite.
- Tests mock the Ring APIs (`test_mock_e2e.py`) to simulate WHEP SDP exchanges.
- AI pipeline tests verify correct state retention, quality gating, and cache isolation without needing a live stream.

---

## 20. Real Hardware Verification

To test against the physical `TS RING 01`:
1. Ensure `.env` has valid Ring OAuth credentials.
2. Start the backend and frontend.
3. Select `TS RING 01` in the dashboard and click "Start Live View".
4. **Verify Detection:** Walk into frame. Ensure a bounding box appears.
5. **Verify Line Crossing:** Walk past the center vertical axis. Check the "Entries" counter.
6. **Verify Recognition:** Look away (should show UNKNOWN), then look directly at camera. It should snap to your enrolled name and stay locked.

---

## 21. Performance Characteristics

- **Frame Processing:** The complete pipeline (YOLO -> YuNet -> ArcFace -> Analytics) executes in ~80-120ms on an Apple Silicon CPU.
- **Sampling Rate:** Frontend is hard-throttled to send max ~10 frames per second to avoid overwhelming the backend and saturating WebRTC bandwidth.
- **Memory:** ~800MB RAM steady state due to ONNX models residing in memory.

---

## 22. Configuration

Configuration is managed via `.env`.

```env
RING_CLIENT_ID=...
RING_CLIENT_SECRET=...
RING_HMAC_SECRET=...
BASE_URL=http://localhost:8000
RING_ENCRYPTION_KEY=... (Fernet key)
RING_DEVICE_CACHE_TTL_SECONDS=300
```
*Never commit the `.env` file or the `Config/app-credentials.csv`.*

---

## 23. Installation and Setup

1. **Python Environment:** Ensure Python 3.11+. 
   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```
2. **Models:** Ensure `yolov8n.pt` is in the root, and `.onnx` files are in `models/weights/`.
3. **Environment:** Copy `.env.example` to `.env` and populate.
4. **Backend:**
   ```bash
   PYTHONPATH=. uv run uvicorn main:app --reload --port 8000
   ```
5. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
6. Open `http://localhost:5173`.

---

## 24. Repository Structure

```text
ProjectRoot/
├── Config/                  # Ring credential mounts
├── SourcesOfTruth/          # Specs & original requirement docs
├── frontend/                # React/Vite dashboard
├── models/weights/          # ONNX AI Models
├── tests/                   # Canonical pytest suite
├── xsc_lib/                 # Migrated Application Core
│   ├── xsc_lib_app/         # Pipeline, Analytics, API Routers
│   ├── xsc_lib_common/      # Pydantic models, Abstract Interfaces
│   └── xsc_lib_extn/        # Ring Client, OpenCV AI Implementations, SQLite
├── junk/                    # Quarantined legacy dev scripts
├── faces.db                 # Biometric templates
└── main.py                  # Backend Entrypoint
```

---

## 25. Rules for Future Development

- **Architecture:** `xsc_lib_common` must NEVER import from `xsc_lib_extn` or `xsc_lib_app`. 
- **Dependencies:** Do not add heavy ML dependencies without rigorous justification. Use ONNX runtimes.
- **State:** Never cache `UNKNOWN` or `LOW_QUALITY` biometric statuses.
- **Privacy:** Never expose ArcFace embeddings (`list[float]`) through FastAPI responses.

---

## 26. How to Safely Modify the AI Pipeline

- **Change Face Quality Logic:** Modify `xsc_lib_extn/ai/opencv_quality.py`.
- **Change Behavioral Scoring:** Modify `xsc_lib_app/analytics/behavioral.py`.
- **Change API Endpoints:** Modify `xsc_lib_app/api/routers/*.py`.
- **Change Database:** Write a new implementation of `xsc_lib_common/interfaces/template_repository.py` and swap it in `pipeline.py`.

---

## 27. Common Failure Modes

- **Error:** `FileNotFoundError: YuNet model not found`
  - *Fix:* Ensure models are in `models/weights/`.
- **Error:** Backend Address Already in Use
  - *Fix:* `pkill uvicorn`
- **Error:** WHEP SDP Failure
  - *Fix:* Check Ring token expiration or WebRTC ICE stun server reachability.
- **Error:** Bounding boxes misaligned in frontend
  - *Fix:* Ensure CSS `transform: scale` in `PersonOverlay.tsx` is calculating against `640x480`.

---

## 28. Future Roadmap

- **Phase 10 (Future):** 
  - Migrate SQLite to PostgreSQL.
  - Implement RBAC (Role-Based Access Control).
  - Multi-tenancy isolation.
  - Asynchronous background workers for video summary extraction.

---

## 29. Migration to the Actual OneApp Repository

This repository represents the development verification environment. The `xsc_lib` directory is structurally ready to be dropped into the target OneApp monorepo.
During migration, `xsc_lib_app` routers will be registered onto the primary OneApp FastAPI instance, and `Config/` will be absorbed by the enterprise secrets manager.

---

## 30. Developer Quick Reference

- **Backend:** `PYTHONPATH=. uv run uvicorn main:app --reload`
- **Frontend:** `npm run dev`
- **Tests:** `PYTHONPATH=. uv run pytest`
- **Main AI Loop:** `xsc_lib_app/ai/pipeline.py`
- **Swagger Docs:** `http://localhost:8000/docs`
