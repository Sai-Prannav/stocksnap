"""The API the app actually serves (stores, products, scans, timeline), through FastAPI's TestClient."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.routers import scans

client = TestClient(app)


def png(size=(64, 48)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 120, 40)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def store_and_product():
    s = client.post("/api/stores/", json={"name": "  Corner Store  ", "location": "Atlanta"})
    p = client.post("/api/products/", json={"name": "Soda can", "sku": f"SKU-{s.json()['id']}"})
    assert s.status_code == 200 and p.status_code == 201, (s.text, p.text)
    return s.json(), p.json()


def test_root_and_cors():
    assert client.get("/").json() == {"message": "StockSnap API is running"}
    ok = client.options("/api/stores/", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options("/api/stores/", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in bad.headers            # no longer "*"


def test_store_crud_and_validation(store_and_product):
    store, _ = store_and_product
    assert store["name"] == "Corner Store"                              # trimmed
    assert client.get(f"/api/stores/{store['id']}").json()["location"] == "Atlanta"
    up = client.put(f"/api/stores/{store['id']}", json={"location": "Marietta"})
    assert up.status_code == 200 and up.json()["location"] == "Marietta"
    assert client.post("/api/stores/", json={"name": "   "}).status_code == 422
    assert client.get("/api/stores/99999").status_code == 404
    assert any(s["id"] == store["id"] for s in client.get("/api/stores/").json())
    gone = client.post("/api/stores/", json={"name": "Temp"}).json()
    assert client.delete(f"/api/stores/{gone['id']}").status_code == 204
    assert client.get(f"/api/stores/{gone['id']}").status_code == 404


def test_product_crud(store_and_product):
    _, product = store_and_product
    assert client.get(f"/api/products/{product['id']}").json()["name"] == "Soda can"
    assert client.put(f"/api/products/{product['id']}", json={"name": "Soda can 12oz"}).json()["name"] == "Soda can 12oz"
    assert client.get("/api/products/99999").status_code == 404
    assert client.delete(f"/api/products/{product['id']}").status_code == 204


def test_a_scan_is_analyzed_stored_and_annotated(store_and_product):
    store, product = store_and_product
    r = client.post("/api/scans/", data={"store_id": store["id"], "product_id": product["id"]},
                    files={"image": ("shelf.png", png(), "image/png")})
    assert r.status_code == 200, r.text
    scan = r.json()
    assert 1 <= scan["count"] <= 30 and 0.75 <= scan["confidence"] <= 0.98      # the mock analyzer's ranges
    assert len(scan["detections"]) == scan["count"]
    assert client.get(f"/api/scans/{scan['id']}").status_code == 200
    ann = client.get(f"/api/scans/{scan['id']}/annotated")
    assert ann.status_code == 200 and ann.json()["annotated_image_path"].startswith("uploads/annotated/annotated_")
    assert any(s["id"] == scan["id"] for s in client.get("/api/scans/").json())
    assert client.get("/api/scans/99999").status_code == 404
    assert client.get("/api/scans/99999/annotated").status_code == 404


@pytest.mark.parametrize("name,mime,body,status", [
    ("notes.txt", "text/plain", b"hello", 415),                      # not an image
    ("shelf.png", "image/jpeg", None, 415),                          # type and extension disagree
    ("shelf.exe", "image/png", None, 415),
    ("empty.png", "image/png", b"", 400),
    ("huge.png", "image/png", b"\x89PNG" + b"0" * (1024 * 1024 + 10), 413),   # over STOCKSNAP_MAX_UPLOAD_MB (1 in tests)
])
def test_uploads_are_checked_before_anything_is_saved(store_and_product, name, mime, body, status):
    store, product = store_and_product
    r = client.post("/api/scans/", data={"store_id": store["id"], "product_id": product["id"]},
                    files={"image": (name, png() if body is None else body, mime)})
    assert r.status_code == status, r.text


def test_timeline_reports_the_scans(store_and_product):
    store, product = store_and_product
    client.post("/api/scans/", data={"store_id": store["id"], "product_id": product["id"]}, files={"image": ("a.jpg", png(), "image/jpeg")})
    pts = client.post("/api/timeline/data", json={"store_id": store["id"], "product_id": product["id"]})
    assert pts.status_code == 200 and pts.json() and pts.json()[0]["scan_count"] >= 1
    assert client.get("/api/timeline/stats").status_code == 200
    assert client.get("/api/timeline/summary").status_code == 200


def test_the_analyzer_switch(monkeypatch):
    monkeypatch.setenv("STOCKSNAP_ANALYZER", "mock")
    assert type(scans._make_analyzer()).__name__ == "MockImageAnalyzer"
    monkeypatch.delenv("STOCKSNAP_ANALYZER")
    # without ultralytics (CI), or if YOLO cannot load, the app still starts on the mock
    assert type(scans._make_analyzer()).__name__ in {"MockImageAnalyzer", "RealImageAnalyzer"}
