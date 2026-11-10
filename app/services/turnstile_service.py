import os
import urllib.request
import urllib.parse
import json
from typing import Tuple, Optional, Dict, Any
from flask import current_app

DEFAULT_TEST_SITE_KEY = "1x00000000000000000000AA"
DEFAULT_TEST_SECRET_KEY = "1x0000000000000000000000000000000AA"
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

def get_turnstile_config() -> Dict[str, Any]:
    """
    Returns the Cloudflare Turnstile configuration.
    If real keys are not supplied in production/development, Turnstile can be disabled
    in favor of standard CSRF protection and server-side rate-limiting.
    """
    if current_app:
        enabled = current_app.config.get("CLOUDFLARE_TURNSTILE_ENABLED", True)
        site_key = current_app.config.get("CLOUDFLARE_TURNSTILE_SITE_KEY", DEFAULT_TEST_SITE_KEY)
        secret_key = current_app.config.get("CLOUDFLARE_TURNSTILE_SECRET_KEY", DEFAULT_TEST_SECRET_KEY)
    else:
        enabled = os.environ.get("CLOUDFLARE_TURNSTILE_ENABLED", "true").lower() in ("true", "1", "yes")
        site_key = os.environ.get("CLOUDFLARE_TURNSTILE_SITE_KEY", DEFAULT_TEST_SITE_KEY)
        secret_key = os.environ.get("CLOUDFLARE_TURNSTILE_SECRET_KEY", DEFAULT_TEST_SECRET_KEY)

    is_test_key = (site_key == DEFAULT_TEST_SITE_KEY)

    return {
        "enabled": enabled,
        "site_key": site_key,
        "secret_key": secret_key,
        "is_test_key": is_test_key
    }

def verify_turnstile_response(
    response_token: Optional[str],
    csrf_token: Optional[str] = None,
    remote_ip: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Verifies Cloudflare Turnstile CAPTCHA response token against Cloudflare's siteverify endpoint.
    When Turnstile is disabled or during automated testing, appropriate bypasses/mocks are respected.
    """
    cfg = get_turnstile_config()
    if not cfg["enabled"]:
        return True, None

    # In testing mode (e.g. automated pytest test suite)
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

    # If Cloudflare test key is active, accept non-empty response token
    if cfg["is_test_key"]:
        return True, None

    # Verify with Cloudflare Siteverify API
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
