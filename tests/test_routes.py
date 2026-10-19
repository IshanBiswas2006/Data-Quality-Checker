import io
import os
import pytest
from app import create_app
from app.services.session_store import SessionStore
from app.services.user_service import init_db, create_user

@pytest.fixture
def client(tmp_path):
    test_db = str(tmp_path / "test_routes.db")
    app = create_app()
    app.config["TESTING"] = True
    app.config["USERS_DB_PATH"] = test_db
    init_db(test_db)
    SessionStore.clear_all()
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["csrf_token"] = "test-csrf-token-12345"
        yield client

    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass

@pytest.fixture
def auth_client(client):
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Auth Tester",
        "email": "authtester@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    return client

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Data Quality Checker" in response.data
    assert b"Inspect and Clean Your Datasets" in response.data

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "healthy"

def test_faq_page(client):
    response = client.get("/faq")
    assert response.status_code == 200
    assert b"Frequently Asked Questions" in response.data
    assert b"What file formats and sizes are supported?" in response.data

def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"About Data Quality Checker" in response.data
    assert b"Technology Stack" in response.data

def test_upload_unauthenticated_blocks_and_redirects(client):
    # AJAX upload without login returns 401 with redirect to /login
    res_ajax = client.post("/upload", data={}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_ajax.status_code == 401
    json_data = res_ajax.get_json()
    assert not json_data["success"]
    assert "Authentication required" in json_data["error"]
    assert "/login" in json_data["redirect"]

    # Form upload without login redirects to /login
    res_form = client.post("/upload", data={})
    assert res_form.status_code == 302
    assert "/login" in res_form.headers["Location"]

def test_upload_missing_file(auth_client):
    response = auth_client.post("/upload", data={}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert response.status_code == 400
    data = response.get_json()
    assert not data["success"]

def test_upload_invalid_extension(auth_client):
    data = {"file": (io.BytesIO(b"content"), "file.txt")}
    response = auth_client.post("/upload", data=data, content_type="multipart/form-data", headers={"X-Requested-With": "XMLHttpRequest"})
    assert response.status_code == 400
    assert "Unsupported file extension" in response.get_json()["error"]

def test_upload_valid_csv_and_full_workflow(auth_client):
    csv_content = b"id,name,age,email\n1,Alice,25,alice@example.com\n2,Bob,,bob@example.com\n1,Alice,25,alice@example.com\n"
    data = {"file": (io.BytesIO(csv_content), "test_data.csv")}
    
    # 1. Upload
    upload_res = auth_client.post(
        "/upload",
        data=data,
        content_type="multipart/form-data",
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert upload_res.status_code == 200
    res_json = upload_res.get_json()
    assert res_json["success"] is True
    analysis_id = res_json["analysis_id"]
    
    # 2. View Results
    results_res = auth_client.get(f"/results/{analysis_id}")
    assert results_res.status_code == 200
    assert b"test_data.csv" in results_res.data
    assert b"Duplicate Rows" in results_res.data
    
    # 3. Clean: Remove duplicates
    clean_res = auth_client.post(
        f"/clean/{analysis_id}",
        json={"type": "remove_duplicates", "params": {}},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert clean_res.status_code == 200
    clean_json = clean_res.get_json()
    assert clean_json["success"] is True
    assert clean_json["comparison"]["delta"]["duplicates_removed"] == 1
    
    # 4. Clean: Fill missing age with 30
    fill_res = auth_client.post(
        f"/clean/{analysis_id}",
        json={"type": "fill_missing", "params": {"column": "age", "strategy": "constant", "value": "30"}},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert fill_res.status_code == 200
    fill_json = fill_res.get_json()
    assert fill_json["success"] is True
    
    # 5. Download Cleaned CSV
    dl_res = auth_client.get(f"/download/{analysis_id}")
    assert dl_res.status_code == 200
    assert dl_res.headers["Content-Type"].startswith("text/csv")
    assert b"Alice" in dl_res.data
    
    # 6. Reset Dataset
    reset_res = auth_client.post(f"/reset/{analysis_id}", headers={"X-Requested-With": "XMLHttpRequest"})
    assert reset_res.status_code == 200
    assert reset_res.get_json()["success"] is True

