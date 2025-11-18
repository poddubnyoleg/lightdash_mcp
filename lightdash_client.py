import os
from typing import Any

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

def get(path: str) -> dict[str, Any]:
    """Make a GET request to the Lightdash API"""
    url = f"{LIGHTDASH_URL}{path}"
    r = session.get(url)
    r.raise_for_status()
    return r.json()

def patch(path: str, data: dict[str, Any]) -> dict[str, Any]:
    """Make a PATCH request to the Lightdash API"""
    url = f"{LIGHTDASH_URL}{path}"
    r = session.patch(url, json=data)
    r.raise_for_status()
    return r.json()

def post(path: str, data: dict[str, Any]) -> dict[str, Any]:
    """Make a POST request to the Lightdash API"""
    url = f"{LIGHTDASH_URL}{path}"
    r = session.post(url, json=data)
    r.raise_for_status()
    return r.json()

def delete(path: str) -> dict[str, Any]:
    """Make a DELETE request to the Lightdash API"""
    url = f"{LIGHTDASH_URL}{path}"
    r = session.delete(url)
    r.raise_for_status()
    return r.json()
