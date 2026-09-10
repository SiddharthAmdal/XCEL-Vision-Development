# Repository Cleanup Plan

This plan details the cleanup of the Ring Camera AI repository to ensure it contains only files and directories necessary for installation, runtime, and continued development testing, while safely quarantining obsolete and scratch files into `junk/`.

## 1. Complete Repository Audit

| Path | Classification | Why | Referenced By | Runtime Required? | Proposed Action |
| --- | --- | --- | --- | --- | --- |
| `.DS_Store` | REDUNDANT | OS X metadata | None | No | Move to `junk/obsolete/` |
| `.env` | RUNTIME_REQUIRED | Environment configuration | `main.py`, config loaders | Yes | Keep |
| `.env.example` | DEVELOPMENT_REQUIRED | Template for `.env` | Developers | No (but standard) | Keep |
| `.gitignore` | DEVELOPMENT_REQUIRED | Git ignore rules | Git | No | Keep |
| `.pytest_cache/` | REDUNDANT | Generated cache | Pytest | No | Remove |
| `.venv/` | DEVELOPMENT_REQUIRED | Virtual environment | Developer / Runner | No (but local dev standard) | Keep |
| `Config/` | RUNTIME_REQUIRED | Credentials for Ring API | `ring.client` | Yes | Keep |
| `SourcesOfTruth/` | DOCUMENTATION | Architecture documents | None | No | Move to `junk/documentation/` |
| `__pycache__/` | REDUNDANT | Python cache | Python | No | Remove |
| `ai/` | MIGRATION_ONLY | Old architecture dir | None | No | Move to `junk/obsolete/ai/` |
| `api/` | MIGRATION_ONLY | Old architecture dir | None | No | Move to `junk/obsolete/api/` |
| `architecture_migration_plan.md` | MIGRATION_ONLY | Migration doc | None | No | Move to `junk/migration/` |
| `benchmark.py` | SCRATCH | Benchmarking utility | None | No | Move to `junk/benchmarks/` |
| `camera/` | MIGRATION_ONLY | Old architecture dir | None | No | Move to `junk/obsolete/camera/` |
| `faces.db` | RUNTIME_REQUIRED | SQLite DB for templates | `xsc_lib_extn.db` | Yes | Keep |
| `fix_imports.py` | MIGRATION_ONLY | Migration script | None | No | Move to `junk/migration/` |
| `frontend/` | RUNTIME_REQUIRED | UI application | Web browsers | Yes | Keep |
| `main.py` | RUNTIME_REQUIRED | App entrypoint | Uvicorn | Yes | Keep |
| `migrate_arch.py` | MIGRATION_ONLY | Migration script | None | No | Move to `junk/migration/` |
| `requirements.txt` | RUNTIME_REQUIRED | Dependency manifest | Developers / CI | Yes | Keep |
| `ring/` | MIGRATION_ONLY | Old architecture dir | None | No | Move to `junk/obsolete/ring/` |
| `ring_tokens.db` | RUNTIME_REQUIRED | Ring API tokens DB | `ring.client` | Yes | Keep |
| `scratch_video_test.mp4` | SCRATCH | Test video | None | No | Move to `junk/scratch/` |
| `scripts/` | DEVELOPMENT_REQUIRED | Various scripts | Developers | No | Move to `junk/scripts/` |
| `testBoxMath.ts` | SCRATCH | Random test file | None | No | Move to `junk/scratch/` |
| `test_crossing_logic.py` | SCRATCH | One-off test | None | No | Move to `junk/tests/` |
| `test_recognition.py` | SCRATCH | One-off test | None | No | Move to `junk/tests/` |
| `tests/` | DEVELOPMENT_REQUIRED | Canonical test suite | Pytest | No (but project standard) | Keep |
| `verify_live.py` | SCRATCH | Verification utility | None | No | Move to `junk/verification/` |
| `xsc_lib/` | RUNTIME_REQUIRED | Main codebase | Everything | Yes | Keep |
| `yolov8n.pt` | RUNTIME_REQUIRED | Model weights | `pipeline.py` | Yes | Keep |

## 2. Proposed Changes

We will execute the following terminal commands to move files to their designated `junk/` subdirectories:

1. Create `junk/` subdirectories: `junk/obsolete/`, `junk/documentation/`, `junk/migration/`, `junk/benchmarks/`, `junk/scratch/`, `junk/scripts/`, `junk/tests/`, `junk/verification/`.
2. Move old architecture folders: `ai`, `api`, `camera`, `ring` into `junk/obsolete/`.
3. Move `SourcesOfTruth/` to `junk/documentation/`.
4. Move migration scripts and plans to `junk/migration/`.
5. Move scratch files, test scripts, and benchmarks to their respective `junk/` folders.
6. Move the `scripts/` directory to `junk/scripts/`.
7. Remove the redundant `__pycache__` and `.pytest_cache` directories.
