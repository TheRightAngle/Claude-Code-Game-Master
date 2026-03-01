#!/usr/bin/env python3
"""
List monsters using API's built-in challenge_rating query parameter for efficient filtering.
This replaces the slow local filtering approach.
"""

import argparse
import json
import sys
from typing import List, Dict, Any, Optional
import urllib.parse
import urllib.request
import urllib.error

BASE_URL = "https://www.dnd5eapi.co"
REQUEST_TIMEOUT = 10
FRACTIONAL_CR_VALUES = {
    "1/8": 0.125,
    "1/4": 0.25,
    "1/2": 0.5,
}


def _validated_base_url() -> str:
    parsed = urllib.parse.urlparse(BASE_URL)
    if parsed.scheme not in {"http", "https"}:
        scheme = parsed.scheme or "<empty>"
        raise ValueError(f"Invalid BASE_URL scheme: {scheme}")
    return BASE_URL.rstrip("/")


def _urlopen_with_timeout(url: str):
    request = urllib.request.Request(url)
    opener = urllib.request.build_opener()
    return opener.open(request, timeout=REQUEST_TIMEOUT)


def parse_cr_value(value: str) -> float:
    """Parse CR values from CLI, including common fractional notation."""
    normalized = str(value).strip()
    if normalized in FRACTIONAL_CR_VALUES:
        return FRACTIONAL_CR_VALUES[normalized]
    try:
        return float(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid CR value: {value!r}") from exc


def fetch_monsters(
    challenge_ratings: Optional[List[float]] = None,
    limit: Optional[int] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch monsters from the API with optional filtering.
    
    Args:
        challenge_ratings: List of CR values to filter by
        limit: Maximum number of results to return
        search: Search term for monster names
    
    Returns:
        API response containing monster list
    """
    if limit is not None and limit < 0:
        return {"error": "--limit must be 0 or greater"}

    try:
        url = f"{_validated_base_url()}/api/2014/monsters"
        params = []

        # Add challenge_rating query parameter
        if challenge_ratings:
            # API expects comma-separated values
            cr_param = ",".join(str(cr) for cr in challenge_ratings)
            params.append(f"challenge_rating={cr_param}")

        # Build final URL with parameters
        if params:
            url += "?" + "&".join(params)

        with _urlopen_with_timeout(url) as response:
            data = json.loads(response.read())
            
            # Apply search filter if provided
            if search and "results" in data:
                search_lower = search.lower()
                data["results"] = [
                    m for m in data["results"]
                    if search_lower in m["name"].lower()
                ]
            
            # Apply limit if provided
            if limit is not None and "results" in data:
                data["results"] = data["results"][:limit]

            if "results" in data:
                data["count"] = len(data["results"])
            
            return data
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {"error": "Rate limited. Please wait a moment and try again."}
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def format_monster_list(monsters: List[Dict[str, Any]]) -> None:
    """Format and print monster list."""
    if not monsters:
        print("No monsters found matching criteria.")
        return
    
    print(f"\nFound {len(monsters)} monsters:")
    print("-" * 60)
    
    for monster in monsters:
        # Extract monster index from URL for potential detail lookup
        index = monster["url"].split("/")[-1]
        print(f"- {monster['name']} (index: {index})")


def main():
    parser = argparse.ArgumentParser(
        description="List D&D 5e monsters with efficient API filtering"
    )
    parser.add_argument(
        "--cr",
        type=parse_cr_value,
        action="append",
        help="Filter by challenge rating (can be used multiple times)"
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search for monsters by name"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of results"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON"
    )
    
    args = parser.parse_args()

    if args.limit is not None and args.limit < 0:
        print("Error: --limit must be 0 or greater", file=sys.stderr)
        sys.exit(1)
    
    # Fetch monsters with filters
    result = fetch_monsters(
        challenge_ratings=args.cr,
        limit=args.limit,
        search=args.search
    )
    
    # Handle errors
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    
    # Output results
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "results" in result:
            format_monster_list(result["results"])
            if args.cr:
                print(f"\nFiltered by CR: {', '.join(str(cr) for cr in args.cr)}")
        else:
            print("No results found.")


if __name__ == "__main__":
    main()
