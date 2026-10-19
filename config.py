import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Automatically load .env file if present
env_file = BASE_DIR / ".env"
if env_file.is_file():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k not in os.environ:
                os.environ[k] = v

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dqc-default-secret-key-change-in-prod-2026")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB max
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "temp_uploads"))
    ALLOWED_EXTENSIONS = {"csv"}
    PREVIEW_ROWS = int(os.environ.get("PREVIEW_ROWS", 10))
    MAX_INSPECT_ROWS = int(os.environ.get("MAX_INSPECT_ROWS", 50))
    SESSION_MAX_AGE_SECONDS = int(os.environ.get("SESSION_MAX_AGE_SECONDS", 7200))  # 2 hours
    USERS_DB_PATH = os.environ.get("USERS_DB_PATH", str(BASE_DIR / "instance" / "users.db"))
    
    # Cookie & Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    
    # Cloudflare Turnstile CAPTCHA
    CLOUDFLARE_TURNSTILE_ENABLED = os.environ.get("CLOUDFLARE_TURNSTILE_ENABLED", "true").lower() in ("true", "1", "yes")
    CLOUDFLARE_TURNSTILE_SITE_KEY = os.environ.get("CLOUDFLARE_TURNSTILE_SITE_KEY", "1x00000000000000000000AA")
    CLOUDFLARE_TURNSTILE_SECRET_KEY = os.environ.get("CLOUDFLARE_TURNSTILE_SECRET_KEY", "1x0000000000000000000000000000000AA")

    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com; "
            "frame-src https://challenges.cloudflare.com; "
            "connect-src 'self' https://challenges.cloudflare.com; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )
    }

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    USERS_DB_PATH = str(BASE_DIR / "instance" / "test_users.db")
    CLOUDFLARE_TURNSTILE_ENABLED = True

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
