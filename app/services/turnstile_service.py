import os
import time
import hmac
import hashlib
import urllib.request
import urllib.parse
import json
from typing import Tuple, Optional, Dict, Any
from flask import current_app, session

# Cloudflare official testing keys:
DEFAULT_TEST_SITE_KEY = "1x00000000000000000000AA"
DEFAULT_TEST_SECRET_KEY = "1x0000000000000000000000000000000AA"
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

def get_turnstile_config() -> Dict[str, Any]:
    if current_app:
        enabled = current_app.config.get("CLOUDFLARE_TURNSTILE_ENABLED", True)
        site_key = current_app.config.get("CLOUDFLARE_TURNSTILE_SITE_KEY", DEFAULT_TEST_SITE_KEY)
        secret_key = current_app.config.get("CLOUDFLARE_TURNSTILE_SECRET_KEY", DEFAULT_TEST_SECRET_KEY)
    else:
        enabled = os.environ.get("CLOUDFLARE_TURNSTILE_ENABLED", "true").lower() in ("true", "1", "yes")
        site_key = os.environ.get("CLOUDFLARE_TURNSTILE_SITE_KEY", DEFAULT_TEST_SITE_KEY)
        secret_key = os.environ.get("CLOUDFLARE_TURNSTILE_SECRET_KEY", DEFAULT_TEST_SECRET_KEY)

    # Use interactive native widget if test keys are active (removes Cloudflare's red test disclaimer & forces manual click)
    is_test_key = (site_key == DEFAULT_TEST_SITE_KEY)

    return {
        "enabled": enabled,
        "site_key": site_key,
        "secret_key": secret_key,
        "is_test_key": is_test_key
    }

def generate_interactive_token(csrf_token: str) -> str:
    secret = (current_app.config.get("SECRET_KEY", "default-key") if current_app else "default-key").encode("utf-8")
    ts = str(int(time.time()))
    payload = f"{csrf_token}:{ts}"
    sig = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"cf-interactive:{payload}:{sig}"

def verify_interactive_token(token: str, csrf_token: str) -> bool:
    if not token or not token.startswith("cf-interactive:"):
        return False
    parts = token.split(":")
    if len(parts) != 4:
        return False
    _, token_csrf, ts_str, sig = parts
    if token_csrf != csrf_token:
        return False
    try:
        ts = int(ts_str)
        # 15 minutes validity
        if abs(time.time() - ts) > 900:
            return False
    except ValueError:
        return False
    secret = (current_app.config.get("SECRET_KEY", "default-key") if current_app else "default-key").encode("utf-8")
    payload = f"{token_csrf}:{ts_str}"
    expected_sig = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected_sig)

def verify_turnstile_response(
    response_token: Optional[str],
    csrf_token: Optional[str] = None,
    remote_ip: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    cfg = get_turnstile_config()
    if not cfg["enabled"]:
        return True, None

    # In testing mode (e.g. automated tests)
    if current_app and current_app.config.get("TESTING"):
        if response_token == "test-fail-turnstile":
            return False, "CAPTCHA verification failed. Please try again."
        if response_token == "" or response_token == "test-fail-empty":
            return False, "Please complete the security check (CAPTCHA)."
        if response_token is None:
            return True, None
        return True, None

    if not response_token or not response_token.strip():
        return False, "Please complete the security check (CAPTCHA)."

    token = response_token.strip()

    # Check interactive HMAC signed token
    if token.startswith("cf-interactive:"):
        active_csrf = csrf_token or session.get("csrf_token", "")
        if verify_interactive_token(token, active_csrf):
            return True, None
        return False, "Security verification failed or expired. Please try again."

    # If test key is in use, accept any non-empty test response
    if cfg["is_test_key"]:
        return True, None

    # If real Cloudflare key is configured, verify with Cloudflare API
    post_data = {
        "secret": cfg["secret_key"],
        "response": token
    }
    if remote_ip:
        post_data["remoteip"] = remote_ip

    encoded_data = urllib.parse.urlencode(post_data).encode("utf-8")
    req = urllib.request.Request(
        TURNSTILE_VERIFY_URL,
        data=encoded_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return False, "CAPTCHA verification service unavailable. Please try again."
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success"):
                return True, None
            return False, "CAPTCHA verification failed. Please try again."
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Turnstile verification error: {e}")
        return False, "Security verification encountered a network error. Please try again."
