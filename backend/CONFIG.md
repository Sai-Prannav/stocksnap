# Configuration

What the running app actually uses. (An earlier version of this file described an "advanced" pipeline with SAM,
model ensembles and YOLOv8. That code is still in `app/services/` (advanced_image_analyzer, duplicate_resolver,
preprocessing_pipeline, model_manager, config/ai_config.py), but nothing in the API calls it.)

## Detection

The API (`POST /api/scans/`) runs **YOLO11** through `app/services/real_image_analyzer.py`:

| Setting | Value | Where |
|---|---|---|
| Model | `yolo11n.pt` (downloaded to `backend/weights/` by ultralytics on first run) | `RealImageAnalyzer.MODEL_NAME` |
| Image size | 1280 (small items on a shelf) | `analyze_image` |
| Confidence | model floor 0.10, counted at ≥ 0.25 | `analyze_image` |
| NMS IoU | 0.3 | `analyze_image` |

If YOLO11 cannot load (no `ultralytics`, no weights, no network on first run), the app falls back to the
`MockImageAnalyzer` and says so in the log.

## Environment variables

| Variable | Default | What it does |
|---|---|---|
| `STOCKSNAP_DATABASE_URL` | `sqlite:///./app.db` | SQLAlchemy URL of the database |
| `STOCKSNAP_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | comma-separated origins the browser may call the API from (the Vite dev server by default) |
| `STOCKSNAP_MAX_UPLOAD_MB` | `10` | largest shelf photo accepted (bigger: 413) |
| `STOCKSNAP_ANALYZER` | (unset: YOLO11) | `mock` uses the mock analyzer on purpose (tests, CI) |

Uploads must be JPEG, PNG or WebP, with a matching file extension (otherwise 415); an empty file is a 400.

## Tests

```
pip install -r requirements-dev.txt        # no ultralytics / PyTorch needed
pytest tests -q                            # API tests run on the mock analyzer and a throwaway database
```
