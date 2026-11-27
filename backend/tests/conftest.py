"""Test setup: a throwaway SQLite database, the mock analyzer (no YOLO / PyTorch), and a temp working directory so
uploads and app.db never land in the repo. Set before anything imports the app."""
import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
_tmp = tempfile.mkdtemp(prefix="stocksnap-test-")
os.environ["STOCKSNAP_DATABASE_URL"] = f"sqlite:///{Path(_tmp, 'test.db').as_posix()}"
os.environ["STOCKSNAP_ANALYZER"] = "mock"
os.environ.setdefault("STOCKSNAP_MAX_UPLOAD_MB", "1")
os.chdir(_tmp)
sys.path.insert(0, str(BACKEND))
