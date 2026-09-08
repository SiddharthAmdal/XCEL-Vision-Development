# Ring Camera AI — OneApp Architecture Migration Plan

## Overview
This document maps the entire current Ring Camera AI implementation to the OneApp `xsc_lib` architectural structure.
The migration reorganizes the project into three canonical layers:
1. `xsc_lib_common`: Shared abstractions, generic models, configurations, and interfaces.
2. `xsc_lib_extn`: External provider implementations (Ring API, YuNet, ArcFace, SQLite).
3. `xsc_lib_app`: Application orchestration, API routers, and domain-specific logic.

## 1. Common Layer (`xsc_lib_common`)
Contains functionality genuinely reusable and independent of application logic or external providers.

| Current Path | Target Path | Reason | Dependencies | Risk |
|--------------|-------------|--------|--------------|------|
| `config.py` | `xsc_lib/xsc_lib_common/config.py` | Shared configuration primitives. | pydantic_settings | Low |
| `database.py` | `xsc_lib/xsc_lib_common/database.py` | Database session factory & base class. | sqlalchemy | Low |
| `ai/models.py` | `xsc_lib/xsc_lib_common/models/ai.py` | Shared AI models (Detection, AIFrameResult). | pydantic | Low |
| `ai/analytics/models.py` | `xsc_lib/xsc_lib_common/models/analytics.py` | Domain-independent analytics DTOs. | pydantic | Low |
| `ai/face/quality.py` | `xsc_lib/xsc_lib_common/models/face.py` | Generic face quality models. | pydantic | Low |
| `ai/face/recognition/models.py` | `xsc_lib/xsc_lib_common/models/recognition.py` | Generic recognition domain models. | pydantic | Low |
| `camera/models.py` | `xsc_lib/xsc_lib_common/models/camera.py` | Generic camera models. | pydantic | Low |
| `ai/face/detector.py` | `xsc_lib/xsc_lib_common/interfaces/face_detector.py` | Interface for face detection. | numpy, models | Low |
| `ai/face/expression.py` | `xsc_lib/xsc_lib_common/interfaces/face_expression.py` | Interface for expression analysis. | numpy, models | Low |
| `ai/face/recognition/embedding.py` | `xsc_lib/xsc_lib_common/interfaces/embedding_model.py` (Base class extracted) | Interface for embeddings. | numpy | Low |
| `ai/face/recognition/repository.py` | `xsc_lib/xsc_lib_common/interfaces/template_repository.py` (Base class extracted) | Interface for template persistence. | models | Low |
| `camera/provider.py` | `xsc_lib/xsc_lib_common/interfaces/camera_provider.py` | Interface for camera streams/events. | models | Low |

## 2. Extension Layer (`xsc_lib_extn`)
Contains implementations of specific technologies or third-party providers.

| Current Path | Target Path | Reason | Dependencies | Risk |
|--------------|-------------|--------|--------------|------|
| `ring/client.py` | `xsc_lib/xsc_lib_extn/ring/client.py` | Ring API HTTP client. | httpx | Low |
| `ring/models.py` | `xsc_lib/xsc_lib_extn/ring/models.py` | Ring-specific payload models. | pydantic | Low |
| `ring/oauth.py` | `xsc_lib/xsc_lib_extn/ring/oauth.py` | Ring OAuth handling. | httpx | Low |
| `ring/provider.py` | `xsc_lib/xsc_lib_extn/ring/provider.py` | Implements CameraProvider for Ring. | ring client, common interfaces | Medium |
| `ring/webhook.py` | `xsc_lib/xsc_lib_extn/ring/webhook.py` | Ring webhook parsing. | fastapi, ring models | Low |
| `ai/face/yunet.py` | `xsc_lib/xsc_lib_extn/ai/yunet.py` | YuNet specific implementation. | cv2, common interfaces | Medium |
| `ai/face/ferplus_expression.py` | `xsc_lib/xsc_lib_extn/ai/ferplus_expression.py` | FERPlus specific implementation. | cv2, onnx, common interfaces | Medium |
| `ai/face/opencv_quality.py` | `xsc_lib/xsc_lib_extn/ai/opencv_quality.py` | OpenCV-based quality metrics. | cv2, common models | Low |
| `ai/face/recognition/aligner.py` | `xsc_lib/xsc_lib_extn/ai/arcface_aligner.py` | ArcFace specific affine alignment. | cv2, numpy | Low |
| `ai/face/recognition/embedding.py` | `xsc_lib/xsc_lib_extn/ai/arcface_embedding.py` (ArcFace implementation extracted) | ONNX-based ArcFace implementation. | cv2, numpy, common interfaces | Medium |
| `ai/face/recognition/repository.py` | `xsc_lib/xsc_lib_extn/db/sqlite_template_repository.py` (SQLite impl extracted) | SQLite DB specific implementation. | sqlalchemy, common interfaces | Medium |

## 3. Application Layer (`xsc_lib_app`)
Contains domain logic, orchestration, and API boundaries.

| Current Path | Target Path | Reason | Dependencies | Risk |
|--------------|-------------|--------|--------------|------|
| `camera/service.py` | `xsc_lib/xsc_lib_app/camera/service.py` | App-level camera orchestration. | common models, extn providers | Medium |
| `ai/pipeline.py` | `xsc_lib/xsc_lib_app/ai/pipeline.py` | Core AI stream orchestrator. | common models, all ai components | High |
| `ai/analytics/engine.py` | `xsc_lib/xsc_lib_app/analytics/engine.py` | Analytics orchestration engine. | common models, app analytics | High |
| `ai/analytics/activity.py` | `xsc_lib/xsc_lib_app/analytics/activity.py` | Advanced tracking heuristics. | common models | Medium |
| `ai/analytics/behavioral.py` | `xsc_lib/xsc_lib_app/analytics/behavioral.py` | Affective indicator calculations. | common models | Medium |
| `ai/face/association.py` | `xsc_lib/xsc_lib_app/face/association.py` | Person-to-face spatial linking. | common models | Low |
| `ai/face/recognition/cache.py` | `xsc_lib/xsc_lib_app/face/recognition/cache.py` | Temporal cache logic. | common models | Low |
| `ai/face/recognition/service.py` | `xsc_lib/xsc_lib_app/face/recognition/service.py` | Cosine similarity/matching orchestration. | common models, templates | Medium |
| `api/dependencies.py` | `xsc_lib/xsc_lib_app/api/dependencies.py` | FastAPI injection logic. | common db | Low |
| `api/routers/analytics.py` | `xsc_lib/xsc_lib_app/api/routers/analytics.py` | Analytics endpoints. | fastapi, app services | Medium |
| `api/routers/behavior.py` | `xsc_lib/xsc_lib_app/api/routers/behavior.py` | Behavior endpoints. | fastapi, app services | Medium |
| `api/routers/cameras.py` | `xsc_lib/xsc_lib_app/api/routers/cameras.py` | Core camera API. | fastapi, app services, pipeline | Medium |
| `api/routers/recognition.py` | `xsc_lib/xsc_lib_app/api/routers/recognition.py` | Enrollment/Identity API. | fastapi, app services | Medium |
| `ring/router.py` | `xsc_lib/xsc_lib_app/api/routers/ring.py` | Ring specific API endpoints (Webhooks/OAuth).| fastapi, extn ring provider | Medium |

## 4. Root Application Entrypoint
| Current Path | Target Path | Reason | Dependencies | Risk |
|--------------|-------------|--------|--------------|------|
| `main.py` | `main.py` | FastAPI application instantiation. | xsc_lib_app | Low |

## Refactoring Strategy & Imports Updates
1. Create directories: `xsc_lib/xsc_lib_common`, `xsc_lib/xsc_lib_extn`, `xsc_lib/xsc_lib_app` and sub-packages with `__init__.py`.
2. Move files systematically via `git mv` (or raw `mv`).
3. Splitting `embedding.py` and `repository.py` into interfaces vs concrete SQLite/ONNX classes.
4. Run global string replacements:
   - `from ai.models` -> `from xsc_lib.xsc_lib_common.models.ai`
   - `from ai.face.recognition.cache` -> `from xsc_lib.xsc_lib_app.face.recognition.cache`
   - `from api.dependencies` -> `from xsc_lib.xsc_lib_app.api.dependencies`
   - `from camera.service` -> `from xsc_lib.xsc_lib_app.camera.service`
   - `from ring.client` -> `from xsc_lib.xsc_lib_extn.ring.client`
   - ... and similarly for all migrated paths.
5. Update tests.
6. Verify locally.
