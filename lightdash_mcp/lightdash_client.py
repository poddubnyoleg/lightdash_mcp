import os
import sys
import time
from typing import Any
import json

import requests

LIGHTDASH_URL = os.getenv("LIGHTDASH_URL", "")
LIGHTDASH_TOKEN = os.getenv("LIGHTDASH_TOKEN", "")
CF_ACCESS_CLIENT_ID = os.getenv("CF_ACCESS_CLIENT_ID", "")
CF_ACCESS_CLIENT_SECRET = os.getenv("CF_ACCESS_CLIENT_SECRET", "")
IAP_ENABLED = os.getenv("IAP_ENABLED", "").lower() in ("1", "true", "yes")

session = requests.Session()
session.headers.update({
    "Authorization": f"ApiKey {LIGHTDASH_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
})

if CF_ACCESS_CLIENT_ID and CF_ACCESS_CLIENT_SECRET:
    session.headers.update({
        "CF-Access-Client-Id": CF_ACCESS_CLIENT_ID,
        "CF-Access-Client-Secret": CF_ACCESS_CLIENT_SECRET
    })

_iap_jwt_cache: dict = {}


def _attach_iap_token() -> None:
    """Sign a JWT and attach it as Proxy-Authorization for Cloud Run IAP."""
    try:
        import google.auth
        import google.auth.iam
        import google.auth.jwt
        import google.auth.transport.requests
    except ImportError:
        raise RuntimeError(
            "google-auth is required for IAP support. "
            "Install with: pip install lightdash-mcp[iap]"
        )

    now = int(time.time())
    cached = _iap_jwt_cache.get("token")
    if cached and _iap_jwt_cache.get("exp", 0) > now + 300:
        session.headers["Proxy-Authorization"] = f"Bearer {cached}"
        return

    try:
        credentials, _ = google.auth.default()
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)

        sa_email = credentials.service_account_email
        signer = google.auth.iam.Signer(request, credentials, sa_email)

        exp = now + 3600
        payload = {
            "iss": sa_email,
            "sub": sa_email,
            "aud": f"{LIGHTDASH_URL}/*",
            "iat": now,
            "exp": exp,
        }

        token = google.auth.jwt.encode(signer, payload)
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        _iap_jwt_cache["token"] = token
        _iap_jwt_cache["exp"] = exp
        session.headers["Proxy-Authorization"] = f"Bearer {token}"
        print(f"[IAP] JWT signed for {sa_email}, valid until {exp}", file=sys.stderr)
    except Exception as e:
        print(f"[IAP] Failed to sign JWT: {e}", file=sys.stderr)


def _handle_request(method: str, path: str, **kwargs) -> dict[str, Any]:
    """Make a request to the Lightdash API with error handling"""
    if IAP_ENABLED:
        _attach_iap_token()
    url = f"{LIGHTDASH_URL}{path}"
    try:
        r = session.request(method, url, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_details = r.json()
        except Exception:
            error_details = r.text

        raise Exception(
            f"Lightdash API Error: {e} - Details: {json.dumps(error_details) if isinstance(error_details, dict) else error_details}"
        ) from e

def get(path: str) -> dict[str, Any]:
    """Make a GET request to the Lightdash API"""
    return _handle_request("GET", path)

def patch(path: str, data: dict[str, Any]) -> dict[str, Any]:
    """Make a PATCH request to the Lightdash API"""
    return _handle_request("PATCH", path, json=data)

def post(path: str, data: dict[str, Any]) -> dict[str, Any]:
    """Make a POST request to the Lightdash API"""
    return _handle_request("POST", path, json=data)

def delete(path: str) -> dict[str, Any]:
    """Make a DELETE request to the Lightdash API"""
    return _handle_request("DELETE", path)
