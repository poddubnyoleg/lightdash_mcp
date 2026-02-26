import logging
import os
from typing import Any
import json

import requests

logger = logging.getLogger(__name__)

LIGHTDASH_URL = os.getenv("LIGHTDASH_URL", "")
LIGHTDASH_TOKEN = os.getenv("LIGHTDASH_TOKEN", "")
CF_ACCESS_CLIENT_ID = os.getenv("CF_ACCESS_CLIENT_ID", "")
CF_ACCESS_CLIENT_SECRET = os.getenv("CF_ACCESS_CLIENT_SECRET", "")
IAP_CLIENT_ID = os.getenv("IAP_CLIENT_ID", "")

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


def _attach_iap_token() -> None:
    """Fetch a Google OIDC token and attach it for IAP authentication."""
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token
    except ImportError:
        raise RuntimeError(
            "google-auth is required for IAP support. "
            "Install with: pip install lightdash-mcp[iap]"
        )
    try:
        auth_req = google.auth.transport.requests.Request()
        token = google.oauth2.id_token.fetch_id_token(auth_req, IAP_CLIENT_ID)
        session.headers["Proxy-Authorization"] = f"Bearer {token}"
    except Exception as e:
        logger.warning("Failed to fetch IAP token: %s", e)


def _handle_request(method: str, path: str, **kwargs) -> dict[str, Any]:
    """Make a request to the Lightdash API with error handling"""
    if IAP_CLIENT_ID:
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
