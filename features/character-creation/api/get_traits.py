#!/usr/bin/env python3
"""
Get traits for a specific race
Usage: uv run python get_traits.py <race>
Example: uv run python get_traits.py elf
"""

import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse
sys.path.append(str(Path(__file__).parent.parent))

from character_creation_core import fetch, output, error_output

def normalize_trait_endpoint(trait_url):
    """Normalize absolute or relative trait URL into API endpoint format."""
    parsed_url = urlparse(trait_url)
    if parsed_url.scheme and parsed_url.netloc:
        endpoint = parsed_url.path
    else:
        endpoint = trait_url

    endpoint = endpoint.strip()
    if endpoint.startswith("/api/2014"):
        endpoint = endpoint[len("/api/2014"):]
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    return endpoint

def get_trait_details(trait_url):
    """Fetch details for a specific trait"""
    endpoint = normalize_trait_endpoint(trait_url)

    trait_data = fetch(endpoint)
    
    if "error" in trait_data:
        return None
    
    return {
        "name": trait_data.get("name", ""),
        "desc": trait_data.get("desc", []),
        "proficiencies": [
            prof.get("name", "") for prof in trait_data.get("proficiencies", [])
        ]
    }

def main():
    parser = argparse.ArgumentParser(description='Get racial traits')
    parser.add_argument('race', help='Race identifier (e.g., elf, dwarf)')
    
    args = parser.parse_args()
    
    # Convert to API format
    race_id = args.race.lower().replace(' ', '-')
    
    # First fetch race details to get trait URLs
    race_data = fetch(f"/races/{race_id}")
    
    if "error" in race_data:
        if race_data.get("error") == "HTTP 404":
            error_output(f"Race '{args.race}' not found")
        else:
            error_output(f"Failed to fetch race: {race_data.get('message', 'Unknown error')}")
    
    # Get detailed trait information
    traits = []
    for trait_ref in race_data.get("traits", []):
        trait_details = get_trait_details(trait_ref.get("url", ""))
        if trait_details:
            traits.append(trait_details)
    
    # Output formatted data
    output({
        "race": race_data.get("name", ""),
        "count": len(traits),
        "traits": traits
    })

if __name__ == "__main__":
    main()
