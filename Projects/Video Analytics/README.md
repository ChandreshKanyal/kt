# Video Analytics — AI CCTV analytics for bank branches

> Handover README. Anything marked **Unknown – ask Chandresh** is not stated in the files.

## 1. What this is

Two things live here:

1. **A design pack** for an AI CCTV analytics platform for **bank branches**: 13 security use cases, architecture, a
   7-phase execution plan and an MLOps blueprint (`doc1`–`doc4`), plus the client's requirement sheet and a camera survey.
2. **A working prototype ("Sentinel Analytics")** that started as UC-2 armed-guard alertness and now also covers guard
   face recognition, footfall counting and alert clips across several cameras. Code: `Surveillance/surveillance-alert-analytics-cv/`.

**Client:** the survey file is "BOB-AI based CCTV Solution-Survey" and lists four branches (Rabale, Juinagar, Khandeshwar/Panvel,
Vashi) with their Hikvision DVR models, channel counts, resolution (720p / 1024×768), 15 fps, H.264, 90–180 days retention.
Which bank "BOB" is, and the engagement stage (proposal / PoC / pilot): Unknown – ask Chandresh.

**Status:** design docs complete; a multi-camera prototype ("Sentinel Analytics": guard monitoring, guard face recognition, footfall, alert clips, login) exists in the repo (latest version Aug 2026); where it runs today: Unknown – ask Chandresh.

## 2. Folder contents

| Item | What it is |
|---|---|
| `AI Analyttics Anomaly Response.docx` | The client's 13 parameters and our feasibility answer for each (12 "Yes"; cash-threshold counting "No — visual proxy only"). **Start here.** |
| `BOB-AI based CCTV Solution-Survey.xls` | Camera/DVR survey of 4 pilot branches. |
| `doc1_cv_usecase_handbook.docx` | Per use case: risk, CV approach, primary + alternative models with pros/cons, implementation steps, camera/data requirements. |
| `doc2_architecture.docx` | 4-layer platform (ingestion → inference → decision logic → output); camera-to-use-case routing; shared models; edge + central hybrid; per-use-case FPS; alert severities SEV-1…4; tech stack; benchmarks; security/DPDP. |
| `doc3_execution_sop.docx` | 7 phases, ~26–32 weeks to a 3–5 branch pilot; tasks, owners, durations; model acceptance criteria; ongoing ops SOP; full tool list. |
| `doc4_mlops.docx` | MLOps: data intake, training, MLflow registry, Triton serving, storage, monitoring, 16-step build order. |
| `Surveillance/surveillance-alert-analytics-cv/` | The prototype (git repo). |
| `Surveillance/IMG_2865.MOV` | 2.8 GB video used to create training frames. Contains people — treat as personal data. |

## 3. The 13 use cases (from doc1 / doc2)

| UC | Use case | Main technique | Severity |
|---|---|---|---|
| 1 | Branch opening process / tailgating | YOLOv8 + DeepSORT, face recognition, shutter state | SEV-1 |
| 2 | Armed guard alertness & turnout | MediaPipe Pose, motion check, face recognition | SEV-3 |
| 3 | Footfall & occupancy | YOLOv8 + ByteTrack line counting | SEV-4 |
| 4 | Weapon detection at entry | Custom YOLOv8 | SEV-1 |
| 5 | Loitering | Tracking + dwell time | SEV-3 |
| 6 | Vault open/close by two authorised officers | ArcFace/InsightFace dual match | SEV-2 |
| 7 | Vault door left open | 2-class YOLOv8 open/closed | SEV-4 |
| 8 | Excess cash at cashier cabin | Cash-bundle detection (proxy only, cannot count) | — |
| 9 | Gold-loan SOP compliance | SlowFast action recognition | SEV-3 |
| 10 | Locker room SOP | Face recognition + tracking | SEV-2 |
| 11 | Illumination | OpenCV luminance (no ML) | SEV-4 |
| 12 | Cleanliness / fire hazard | Custom YOLOv8 | SEV-4 |
| 13 | Fire extinguisher placement | Custom YOLOv8 | SEV-4 |

Recommended deployment (doc2): an edge GPU box per branch (NVIDIA Jetson AGX Orin, or a small server with an RTX 3090) runs
inference; only alerts/snapshots/metadata go to a central server. Face recognition and biometrics need consent and
DPDP Act 2023 / RBI compliance (doc1, doc2 §9).

## 4. The prototype — "Sentinel Analytics" (guard monitoring and more)

**Repo:** `github.com/ChandreshKanyal/surveillance-alert-analytics-cv` (Chandresh's personal GitHub). Main branch last updated
**2026-08-03** ("Initial commit: surveillance analytics source code" + "Merge current local snapshot"), plus Chandresh's commit
on top (chunked uploads, Windows `start.ps1`/`stop.ps1`). There is also a branch **`shankars-edits`** (2026-02-24, from the old
February version); whether it is still needed: Unknown – ask Chandresh.

Started as UC-2 (guard alertness) and grew, by August 2026, into a multi-camera console:

| Feature | Where in the code |
|---|---|
| Sign-in with roles (admin / users), password change, admin user management, audit log | `api/routes_auth.py`, `routes_users.py`, `auth/` (JWT), `db/` (SQLite via SQLAlchemy async) |
| Several cameras at once (camera grid / console) | `core/pipeline_manager.py`, frontend `CameraGrid`, `CameraConsole`, `CameraFeed` |
| Guard detection + alertness (absent, slouching, sleeping, on phone, attention score, time on post) | `core/detector.py`, `pose_analyzer.py`, `attention_scorer.py`, `alert_manager.py`, `time_tracker.py` |
| **Guard face enrolment and recognition** (only the enrolled guard counts as "the guard") | `core/face_detector.py`, `face_recognizer.py` (facenet-pytorch), `api/routes_guards.py`, frontend `GuardEnrollment`, `GuardFacePanel` |
| **Footfall counting** across a gate line, guard excluded, 30-minute CSV | `core/footfall_counter.py` (DeepSORT tracking), frontend `FootfallPanel`, `PeopleCounter`, `CrowdTrend` |
| Alert **video clips** (5 s before / 5 s after), "guard left premises" after 60 s | `core/clip_recorder.py`, `api/routes_clips.py`, frontend `AlertReview` |
| Event and stats logs per day | `core/event_logger.py`, `api/routes_logs.py` |
| Session report and KPIs, luminance bar (lighting) | frontend `SessionReport`, `SessionKPIs`, `LuminanceBar` |
| Separate **weapon-detection demo** (YOLOv8; a bottle stands in for a weapon) | `weapon/detect.py`, `weapon/README.md` |

**Stack:** Python, FastAPI + Uvicorn (REST + WebSocket), SQLite (`sqlite+aiosqlite`), JWT (python-jose) + passlib, Ultralytics YOLO11m,
MediaPipe Pose, facenet-pytorch, deep-sort-realtime, OpenCV, PyTorch; React 19 + Vite + Zustand frontend. The built frontend is served
by the backend from `webapp/backend/static/` (one port, 8000).

### How it works (per camera)
```
source (webcam | RTSP | uploaded file) -> frame -> YOLO people (+ phones) with tracking
  -> which person is the guard: enrolled face match, custom guard model, or colour/position heuristic
  -> MediaPipe pose on the guard -> slouching / sleeping / on phone -> attention score
  -> alerts (3 s debounce, 30 s cooldown) -> clip saved around the alert -> event log
  -> footfall: people crossing the gate line (guard excluded) -> 30-min counts
  -> annotated frames + stats + alerts to the browser over a WebSocket (~15 fps)
```
Settings (thresholds, gate line, clip lengths, model paths, device) are in `webapp/backend/config.py`, overridable from `.env`.

### How to turn it on

**Linux server / GPU machine (the author's way):**
```
python3 -m venv venv && . venv/bin/activate        # inside the repo (venv/ is git-ignored)
pip install -r requirements.txt
pip install aiofiles python-multipart sqlalchemy aiosqlite "python-jose[cryptography]" "passlib[bcrypt]" facenet-pytorch deep-sort-realtime
cd webapp/frontend && npm install && cd ../..
export SENTINEL_SECRET_KEY='<long random secret>'  # signs login tokens; see Known issues
./start.sh                                         # builds the frontend, starts the backend on :8000, picks GPU if available
./stop.sh
```
Open http://<host>:8000 (or forward the port over SSH). The packages on the second `pip install` line are imported by the code
but **missing from `requirements.txt`**.

**Windows development (`start.ps1`):** expects a venv one level up (`..\venv`, i.e. `Surveillance\venv`) and Node.js; starts the
backend on :8000 and the Vite dev server on :5173 (open http://localhost:5173). Written for the February version; not yet tested
against the August version.

**First sign-in:** on first start the backend creates an admin account with a default password defined in
`webapp/backend/main.py`, flagged "must change password". Change it immediately.

**Models needed at run time:** `yolo11m.pt` (in the repo), `models/checkpoints/guard_model.pt` (custom guard model, in the repo).
`models/gate_segmenter/weights/best.pt` (gate detection for footfall) and `models/guard_profiles/` (enrolled faces) are referenced in
the config but **not in the repo**; without the gate model the fixed gate line from the config is used. Where the gate model is:
Unknown – ask Chandresh.

### How the custom guard model was trained
1. `data_annotation.py` saved one frame every 5 s from `IMG_2865.MOV`.
2. Frames were labelled in **Roboflow** (workspace `video-analytics-7d8j9`, project `my-first-project-b3kye`, v1, one class "Security Guard"); export is in `annotated_data/` (**labels only — the images are not in the folder**).
3. `src/split_dataset.py` → 80/20 split. `src/train.py` → YOLO11m, 100 epochs, 640 px, batch 32, AdamW, first 10 layers frozen.
4. Training ran on a Linux GPU machine (paths `/home/chandresh/...`). Which machine and the accuracy reached: Unknown – ask Chandresh.

## 5. Known issues / limitations

- **Security defaults in code:** a default admin password in `main.py` and a fallback JWT secret in `auth/jwt.py` used when
  `SENTINEL_SECRET_KEY` is not set. Always set `SENTINEL_SECRET_KEY` and change the admin password; better, remove the defaults.
- **`.env` is not git-ignored** in the current `.gitignore` (only `venv/` and `weapon/weapon_env/` are). Never `git add .` without checking.
- `requirements.txt` misses several imported packages (see above); `torch==2.2.0` may not match your CUDA version.
- CORS allows all origins; backend binds to 0.0.0.0. Put it behind HTTPS/VPN before exposing it.
- Guard model trained on one video (one scene, one guard) — expect poor generalisation; pose thresholds are hand-set, not validated.
- Face enrolment stores biometric data of guards — needs consent and DPDP handling before a real pilot.

## 6. Next improvements

From the design docs (doc3 roadmap): data collection per pilot branch (30–60 days of footage with consent), models for the
remaining use cases (vault, cash, gold loan, locker, cleanliness, extinguisher), TensorRT/Triton, alert engine (push/SMS/email),
central dashboard, mobile app, pilot at 3–5 branches with 2 weeks of human-reviewed alerts, then UAT.

Suggested for the prototype (from reading the code):
1. Complete `requirements.txt`; add `.env`, `uploads/`, `clips/`, `logs/`, `static/` to `.gitignore`.
2. Remove the hard-coded admin password and JWT fallback; require them from the environment.
3. Retrain the guard model on varied footage and record precision/recall; commit or document the gate model.
4. Test on the surveyed branches' real DVR streams (720p, 15 fps, H.264, Hikvision RTSP).
5. Decide what to keep from `shankars-edits`.

## 7. Older version

`Projects/Archive/Video-Analytics/` holds the first attempt (Streamlit + YOLOv8n + MediaPipe, repo
`ChandreshKanyal/Video-Analytics`, Feb 2026). Superseded by this prototype.

## 8. Questions for Chandresh

- Which bank is "BOB"? Stage of the engagement? Was the design pack sent to the client?
- Where are the training images, and which GPU machine was used? Who owns the Roboflow workspace?
- What accuracy did the custom guard model reach? Was the prototype demonstrated? Where does it run now?
- Where is the gate segmentation model (`models/gate_segmenter/`)? What should happen to the `shankars-edits` branch?
- Can `IMG_2865.MOV` be shared (people in it, consent)?
