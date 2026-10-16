import io
import pytest
from app import create_app
from app.services.session_store import SessionStore
from app.services.rate_limiter import SimpleRateLimiter
from app.services.export_service import ExportService
import pandas as pd

@pytest.fixture
def client():
    app = create_app(config_name="testing")
    app.config["TESTING"] = True
    SessionStore.clear_all()
    SimpleRateLimiter.reset()
    with app.test_client() as client:
        yield client

def test_security_headers_present(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Content-Security-Policy" in response.headers
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_404_page_status_and_template(client):
    response = client.get("/non-existent-page-12345")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data

def test_robots_txt(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert b"Disallow: /upload" in response.data
    assert b"Sitemap:" in response.data

def test_sitemap_xml(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.mimetype
    assert b"<loc>" in response.data
    assert b"/privacy" in response.data
    assert b"/terms" in response.data

def test_privacy_and_terms_pages(client):
    resp_priv = client.get("/privacy")
    assert resp_priv.status_code == 200
    assert b"Privacy Policy" in resp_priv.data

    resp_terms = client.get("/terms")
    assert resp_terms.status_code == 200
    assert b"Terms of Service" in resp_terms.data

def test_path_traversal_filename_sanitization(client):
    traversal_filename = "../../../etc/passwd.csv"
    csv_bytes = b"col1,col2\nval1,val2\n"
    data = {"file": (io.BytesIO(csv_bytes), traversal_filename)}
    
    response = client.post(
        "/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["success"] is True
    
    session = SessionStore.get_session(res_data["analysis_id"])
    assert session is not None
    # secure_filename strips path traversal sequences
    assert "/" not in session["original_filename"]
    assert ".." not in session["original_filename"]

def test_upload_rate_limiter(client):
    SimpleRateLimiter.reset()
    csv_bytes = b"col1,col2\nval1,val2\n"
    
    # Send up to limit
    for _ in range(40):
        data = {"file": (io.BytesIO(csv_bytes), "sample.csv")}
        res = client.post("/upload", data=data, content_type="multipart/form-data", headers={"X-Requested-With": "XMLHttpRequest"})
        assert res.status_code == 200
        
    # Next request should be rate-limited (429)
    data = {"file": (io.BytesIO(csv_bytes), "sample.csv")}
    res_blocked = client.post("/upload", data=data, content_type="multipart/form-data", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_blocked.status_code == 429
    assert "Rate limit exceeded" in res_blocked.get_json()["error"]
    assert "Retry-After" in res_blocked.headers

def test_formula_injection_sanitization():
    df = pd.DataFrame({"calc": ["=cmd|' /C calc'!A0", "+1+2", "@SUM(A1:B2)", "-5", "normal"]})
    sanitized = ExportService.sanitize_for_csv(df)
    assert sanitized.loc[0, "calc"].startswith("'=")
    assert sanitized.loc[2, "calc"].startswith("'@")
    assert sanitized.loc[4, "calc"] == "normal"
