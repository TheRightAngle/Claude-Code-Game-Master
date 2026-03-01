#!/usr/bin/env python3
"""
D&D 5e Spell API Core - Simple request wrapper
Just makes requests and returns JSON. Nothing fancy.
"""

import json
import sys
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = "https://www.dnd5eapi.co"
REQUEST_TIMEOUT = 10


def _validate_base_url(base_url):
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("BASE_URL must use http or https scheme")


def _open_url_with_timeout(url):
    request = urllib.request.Request(url)
    opener = urllib.request.build_opener()
    return opener.open(request, timeout=REQUEST_TIMEOUT)


def fetch(endpoint):
    """Fetch data from D&D 5e API and return as dict"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        _validate_base_url(BASE_URL)
        with _open_url_with_timeout(url) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "message": e.reason}
    except Exception as e:
        return {"error": "Request failed", "message": str(e)}

def output(data):
    """Output data as JSON to stdout"""
    print(json.dumps(data, indent=2))

def error_output(message):
    """Output error in consistent format"""
    output({"error": message})
    sys.exit(1)

def format_spell_index(spell_name):
    """Convert spell name to API index format"""
    # Convert to lowercase and replace spaces with hyphens
    # Handle special cases like apostrophes
    return spell_name.lower().replace(" ", "-").replace("'", "")
