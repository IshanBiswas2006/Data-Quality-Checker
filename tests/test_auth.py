import os
import pytest
from app import create_app
from app.services.user_service import get_db, init_db, create_user
from app.services.session_store import SessionStore

@pytest.fixture
def client(tmp_path):
    test_db = str(tmp_path / "test_auth.db")
    app = create_app()
    app.config["TESTING"] = True
    app.config["USERS_DB_PATH"] = test_db
    init_db(test_db)
    SessionStore.clear_all()

    with app.test_client() as client:
        # Establish CSRF token in session
        with client.session_transaction() as sess:
            sess["csrf_token"] = "test-csrf-token-12345"
        yield client

    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass

def test_signup_page_render(client):
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"Create Account" in response.data
    assert b"Full Name" in response.data
    assert b"Email Address" in response.data

def test_login_page_render(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Welcome Back" in response.data
    assert b"Password" in response.data

def test_successful_signup_and_auto_login(client):
    data = {
        "csrf_token": "test-csrf-token-12345",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "avatar_color": "#24282E"
    }
    response = client.post("/signup", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome to Data Quality Checker, Jane Doe!" in response.data
    # Header should now show user profile, NOT login/signup, and NOT logout on home page
    assert b"Jane" in response.data
    assert b"headerLoginBtn" not in response.data
    assert b"headerSignupBtn" not in response.data
    assert b"headerLogoutBtn" not in response.data
    # Logout is available on /profile
    prof_res = client.get("/profile")
    assert b"profileLogoutBtn" in prof_res.data
    assert b"Log Out" in prof_res.data

def test_signup_validation_errors(client):
    # Passwords mismatch
    res1 = client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Alex",
        "email": "alex@example.com",
        "password": "password123",
        "confirm_password": "password999"
    })
    assert res1.status_code == 400
    assert b"Passwords do not match" in res1.data

    # Short password
    res2 = client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Alex",
        "email": "alex@example.com",
        "password": "short",
        "confirm_password": "short"
    })
    assert res2.status_code == 400
    assert b"at least 8 characters" in res2.data

    # Invalid email
    res3 = client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Alex",
        "email": "not-an-email",
        "password": "password123",
        "confirm_password": "password123"
    })
    assert res3.status_code == 400
    assert b"valid email address" in res3.data

    # Successful registration
    res4 = client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Alex Smith",
        "email": "alex@example.com",
        "password": "password123",
        "confirm_password": "password123"
    })
    assert res4.status_code == 302

    # Log out so unauthenticated visitor attempts duplicate registration
    client.get("/logout")

    # Duplicate email registration
    res5 = client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Alex Twin",
        "email": "alex@example.com",
        "password": "password123",
        "confirm_password": "password123"
    })
    assert res5.status_code == 400
    assert b"already exists" in res5.data

def test_successful_login(client):
    # Register user first
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Sarah Connor",
        "email": "sarah@skynet.com",
        "password": "CyberdynePassword1",
        "confirm_password": "CyberdynePassword1"
    })
    # Log out
    client.get("/logout")

    # Login
    response = client.post("/login", data={
        "csrf_token": "test-csrf-token-12345",
        "email": "sarah@skynet.com",
        "password": "CyberdynePassword1"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome back, Sarah Connor!" in response.data
    assert b"Sarah" in response.data
    assert b"headerLogoutBtn" not in response.data
    prof_res = client.get("/profile")
    assert b"profileLogoutBtn" in prof_res.data
    assert b"Log Out" in prof_res.data

def test_invalid_credentials_login(client):
    response = client.post("/login", data={
        "csrf_token": "test-csrf-token-12345",
        "email": "ghost@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert b"Invalid email or password" in response.data

def test_logout(client):
    # Sign up
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Bob Dylan",
        "email": "bob@example.com",
        "password": "BlowingInTheWind1",
        "confirm_password": "BlowingInTheWind1"
    })

    # Log out
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out successfully" in response.data
    # Login & Sign Up buttons must reappear
    assert b"headerLoginBtn" in response.data
    assert b"headerSignupBtn" in response.data
    assert b"headerLogoutBtn" not in response.data

def test_protected_profile_requires_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login?next=/profile" in response.headers["Location"]

def test_authenticated_profile_view(client):
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Diana Prince",
        "email": "diana@themyscira.gov",
        "password": "AmazonWarrior99",
        "confirm_password": "AmazonWarrior99",
        "avatar_color": "#4B5563"
    })

    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Diana Prince" in response.data
    assert b"diana@themyscira.gov" in response.data
    assert b"Saved Dataset History" in response.data
    assert b"Change Password" in response.data
    assert b"profileLogoutBtn" in response.data

def test_edit_profile(client):
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Bruce Wayne",
        "email": "bruce@wayne.com",
        "password": "BatcaveSecret1",
        "confirm_password": "BatcaveSecret1"
    })

    # Update profile
    response = client.post("/profile/edit", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Bruce Thomas Wayne",
        "email": "batman@wayne.com",
        "bio": "Billionaire Philanthropist",
        "avatar_color": "#858B94"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Profile updated successfully" in response.data
    assert b"Bruce Thomas Wayne" in response.data
    assert b"batman@wayne.com" in response.data
    assert b"Billionaire Philanthropist" in response.data

def test_change_password(client):
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Clark Kent",
        "email": "clark@dailyplanet.com",
        "password": "MetropolisPass1",
        "confirm_password": "MetropolisPass1"
    })

    # Change password with correct current password
    response = client.post("/profile/password", data={
        "csrf_token": "test-csrf-token-12345",
        "current_password": "MetropolisPass1",
        "new_password": "FortressOfSolitude2",
        "confirm_password": "FortressOfSolitude2"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Password changed successfully" in response.data

    # Log out
    client.get("/logout")

    # Old password fails
    res_old = client.post("/login", data={
        "csrf_token": "test-csrf-token-12345",
        "email": "clark@dailyplanet.com",
        "password": "MetropolisPass1"
    })
    assert res_old.status_code == 401

    # New password succeeds
    res_new = client.post("/login", data={
        "csrf_token": "test-csrf-token-12345",
        "email": "clark@dailyplanet.com",
        "password": "FortressOfSolitude2"
    }, follow_redirects=True)
    assert res_new.status_code == 200
    assert b"Clark" in res_new.data

def test_change_password_wrong_current(client):
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Tony Stark",
        "email": "tony@stark.com",
        "password": "IronManArmorMark85",
        "confirm_password": "IronManArmorMark85"
    })

    response = client.post("/profile/password", data={
        "csrf_token": "test-csrf-token-12345",
        "current_password": "WrongPassword99",
        "new_password": "NewSecretPass123",
        "confirm_password": "NewSecretPass123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Current password is incorrect" in response.data

def test_save_and_delete_analysis(client):
    # Sign up
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Peter Parker",
        "email": "peter@bugle.com",
        "password": "SpideyWebPass1",
        "confirm_password": "SpideyWebPass1"
    })

    # Create dummy analysis session
    import pandas as pd
    df = pd.DataFrame({"colA": range(500), "colB": range(500)})
    aid = SessionStore.create_session(df, "spiderman_data.csv")

    # Save to profile
    res_save = client.post(f"/profile/save-analysis/{aid}", data={
        "csrf_token": "test-csrf-token-12345"
    }, follow_redirects=True)
    assert res_save.status_code == 200
    assert b"Dataset analysis successfully saved" in res_save.data

    # Check profile displays saved analysis
    res_prof = client.get("/profile")
    assert b"spiderman_data.csv" in res_prof.data
    assert b"500 rows" in res_prof.data

    # Delete saved analysis
    res_del = client.post(f"/profile/delete-analysis/{aid}", data={
        "csrf_token": "test-csrf-token-12345"
    }, follow_redirects=True)
    assert res_del.status_code == 200
    assert b"Dataset removed from your saved history" in res_del.data

def test_passwords_are_never_stored_in_plaintext(client):
    raw_password = "SuperSecretPlainTextPassword123!"
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Security Tester",
        "email": "sec@example.com",
        "password": raw_password,
        "confirm_password": raw_password
    })

    with client.application.app_context():
        conn = get_db(client.application.config["USERS_DB_PATH"])
        row = conn.execute("SELECT password_hash FROM users WHERE email = 'sec@example.com'").fetchone()
        conn.close()

        stored_hash = row["password_hash"]
        assert stored_hash != raw_password
        assert not stored_hash.startswith("SuperSecret")
        assert stored_hash.startswith("scrypt:") or stored_hash.startswith("pbkdf2:")

def test_dynamic_header_ui(client):
    # Unauthenticated visitor:
    home_unauth = client.get("/")
    assert home_unauth.status_code == 200
    assert b"headerLoginBtn" in home_unauth.data
    assert b"headerSignupBtn" in home_unauth.data
    assert b"headerProfileBtn" not in home_unauth.data
    assert b"headerLogoutBtn" not in home_unauth.data
    assert b"headerAboutBtn" not in home_unauth.data
    assert b"headerFaqBtn" not in home_unauth.data

    # Sign up and authenticate:
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Natasha Romanoff",
        "email": "natasha@avengers.org",
        "password": "BlackWidowPass1",
        "confirm_password": "BlackWidowPass1"
    })

    # Authenticated visitor:
    home_auth = client.get("/")
    assert home_auth.status_code == 200
    assert b"headerLoginBtn" not in home_auth.data
    assert b"headerSignupBtn" not in home_auth.data
    assert b"headerProfileBtn" in home_auth.data
    assert b"headerLogoutBtn" not in home_auth.data
    assert b"headerAboutBtn" not in home_auth.data
    assert b"headerFaqBtn" not in home_auth.data
    assert b"Natasha" in home_auth.data

    # Profile page has logout:
    prof = client.get("/profile")
    assert b"profileLogoutBtn" in prof.data

def test_login_and_signup_pages_render_turnstile(client):
    res_login = client.get("/login")
    assert res_login.status_code == 200
    assert b"cf-turnstile" in res_login.data
    assert b"securityCaptchaCard" in res_login.data
    assert b"Verify you are human" in res_login.data
    assert b"CLOUDFLARE" in res_login.data
    # Ensures test keys do not load external script that triggers red message and auto-tick
    assert b"challenges.cloudflare.com/turnstile/v0/api.js" not in res_login.data

    res_signup = client.get("/signup")
    assert res_signup.status_code == 200
    assert b"cf-turnstile" in res_signup.data
    assert b"securityCaptchaCard" in res_signup.data
    assert b"Verify you are human" in res_signup.data
    assert b"CLOUDFLARE" in res_signup.data
    assert b"challenges.cloudflare.com/turnstile/v0/api.js" not in res_signup.data

def test_login_fails_on_invalid_turnstile(client):
    res = client.post("/login", data={
        "csrf_token": "test-csrf-token-12345",
        "email": "user@example.com",
        "password": "Password123!",
        "cf-turnstile-response": "test-fail-turnstile"
    })
    assert res.status_code == 400
    assert b"CAPTCHA verification failed" in res.data

def test_signup_fails_on_invalid_turnstile(client):
    res = client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Failed Captcha User",
        "email": "failed-captcha@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "cf-turnstile-response": "test-fail-turnstile"
    })
    assert res.status_code == 400
    assert b"CAPTCHA verification failed" in res.data

def test_login_fails_on_empty_captcha(client):
    res = client.post("/login", data={
        "csrf_token": "test-csrf-token-12345",
        "email": "user@example.com",
        "password": "Password123!",
        "cf-turnstile-response": ""
    })
    assert res.status_code == 400
    assert b"Please complete the security check" in res.data

def test_unauthenticated_analysis_and_cleaning_blocked(client):
    import pandas as pd
    df = pd.DataFrame({"colA": [1, 2, 3], "colB": ["x", "y", "z"]})
    aid = SessionStore.create_session(df, "sample.csv")

    # 1. Accessing results while unauthenticated redirects to /login
    res_get = client.get(f"/results/{aid}")
    assert res_get.status_code == 302
    assert "/login" in res_get.headers["Location"]

    # 2. AJAX results access returns 401
    res_ajax = client.get(f"/results/{aid}", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_ajax.status_code == 401
    assert not res_ajax.get_json()["success"]

    # 3. Rerun analysis returns 401
    res_analyze = client.post(f"/analyze/{aid}", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_analyze.status_code == 401

    # 4. Clean dataset returns 401
    res_clean = client.post(f"/clean/{aid}", json={"type": "remove_duplicates"}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_clean.status_code == 401

    # 5. Reset dataset returns 401
    res_reset = client.post(f"/reset/{aid}", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_reset.status_code == 401

    # 6. Download cleaned file redirects to /login
    res_dl = client.get(f"/download/{aid}")
    assert res_dl.status_code == 302
    assert "/login" in res_dl.headers["Location"]

def test_unauthenticated_to_authenticated_upload_flow(client):
    import io
    csv_bytes = b"id,val\n1,100\n2,200\n"
    data = {"file": (io.BytesIO(csv_bytes), "flow_test.csv")}

    # Step 1: Unauthenticated upload attempt is blocked
    res_unauth = client.post("/upload", data=data, content_type="multipart/form-data")
    assert res_unauth.status_code == 302
    assert "/login" in res_unauth.headers["Location"]

    # Step 2: Sign up / Log in
    client.post("/signup", data={
        "csrf_token": "test-csrf-token-12345",
        "name": "Flow User",
        "email": "flow@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })

    # Step 3: Now upload succeeds
    data2 = {"file": (io.BytesIO(csv_bytes), "flow_test.csv")}
    res_auth = client.post(
        "/upload",
        data=data2,
        content_type="multipart/form-data",
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert res_auth.status_code == 200
    json_data = res_auth.get_json()
    assert json_data["success"] is True
    aid = json_data["analysis_id"]

    # Step 4: Access results successfully
    res_res = client.get(f"/results/{aid}")
    assert res_res.status_code == 200
    assert b"flow_test.csv" in res_res.data



