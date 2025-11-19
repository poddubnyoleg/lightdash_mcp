import os
from typing import Any
import json

import requests

LIGHTDASH_URL = os.getenv("LIGHTDASH_URL", "")
LIGHTDASH_TOKEN = os.getenv("LIGHTDASH_TOKEN", "")
CF_ACCESS_CLIENT_ID = os.getenv("CF_ACCESS_CLIENT_ID", "")
CF_ACCESS_CLIENT_SECRET = os.getenv("CF_ACCESS_CLIENT_SECRET", "")

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

def _handle_request(method: str, path: str, **kwargs) -> dict[str, Any]:
    """Make a request to the Lightdash API with error handling"""
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
