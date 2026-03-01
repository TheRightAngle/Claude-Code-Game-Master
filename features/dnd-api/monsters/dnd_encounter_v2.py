#!/usr/bin/env python3
"""
Quick D&D encounter helper using API CR filtering
Usage: uv run python dnd_encounter_v2.py --cr <CR> [--count <number>]
Example: uv run python dnd_encounter_v2.py --cr 2 --count 3
"""

import sys
import argparse
import random
import json
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dnd_api_core import fetch, output, error_output

BASE_URL = "https://www.dnd5eapi.co"
REQUEST_TIMEOUT = 10
FRACTIONAL_CR_VALUES = {
    "1/8": 0.125,
    "1/4": 0.25,
    "1/2": 0.5,
}


def _validated_base_url():
    parsed = urllib.parse.urlparse(BASE_URL)
    if parsed.scheme not in {"http", "https"}:
        scheme = parsed.scheme or "<empty>"
        raise ValueError(f"Invalid BASE_URL scheme: {scheme}")
    return BASE_URL.rstrip("/")


def _urlopen_with_timeout(url):
    request = urllib.request.Request(url)
    opener = urllib.request.build_opener()
    return opener.open(request, timeout=REQUEST_TIMEOUT)


def parse_cr_value(value):
    """Parse CR values from CLI, including common fractional CR notation."""
    normalized = str(value).strip()
    if normalized in FRACTIONAL_CR_VALUES:
        return FRACTIONAL_CR_VALUES[normalized]
    try:
        return float(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid CR value: {value!r}") from exc


def get_monsters_by_cr(target_cr):
    """Get all monsters of a specific CR using API filtering"""
    try:
        url = f"{_validated_base_url()}/api/2014/monsters?challenge_rating={target_cr}"
        with _urlopen_with_timeout(url) as response:
            data = json.loads(response.read())
            if "results" in data:
                monsters = []
                for monster in data["results"]:
                    monster_url = monster.get("url", "")
                    monster_index = monster_url.rstrip("/").split("/")[-1]
                    if not monster_index:
                        continue
                    monsters.append(
                        {
                            "index": monster_index,
                            "name": monster.get("name", monster_index),
                        }
                    )
                return monsters
            return []
    except urllib.error.HTTPError as e:
        if e.code == 429:
            error_output("Rate limited. Please wait a moment and try again.")
        else:
            error_output(f"HTTP {e.code}: {e.reason}")
    except Exception as e:
        error_output(str(e))
    
    return []

def main():
    parser = argparse.ArgumentParser(description='Quick D&D encounter helper')
    parser.add_argument('--cr', type=parse_cr_value, required=True, help='Challenge rating')
    parser.add_argument('--count', type=int, default=1, help='Number of monsters')
    parser.add_argument('--quick', action='store_true', help='Just return monster names')
    
    args = parser.parse_args()

    if args.count < 0:
        error_output("--count must be 0 or greater")
    
    # Get available monsters for this CR
    available = get_monsters_by_cr(args.cr)
    
    if not available:
        error_output(f"No monsters found for CR {args.cr}")
    
    # Select random monsters
    if args.count > len(available):
        # If we need more than available, allow duplicates
        selected = [random.choice(available) for _ in range(args.count)]
    else:
        # Otherwise, select unique monsters
        selected = random.sample(available, args.count)
    
    if args.quick:
        # Output human-readable monster names.
        output({
            "cr": args.cr,
            "count": args.count,
            "monsters": [monster.get("name", monster.get("index", "")) for monster in selected]
        })
    else:
        # Fetch full details
        monsters = []
        for monster in selected:
            monster_index = monster.get("index")
            if not monster_index:
                continue
            data = fetch(f"/monsters/{monster_index}")
            if "error" not in data:
                # Extract combat info
                monsters.append({
                    "name": data.get("name"),
                    "hp": data.get("hit_points"),
                    "ac": data.get("armor_class", [{}])[0].get("value", 10),
                    "cr": data.get("challenge_rating"),
                    "xp": data.get("xp")
                })
        
        output({
            "cr": args.cr,
            "count": args.count,
            "encounter_xp": sum(m.get("xp", 0) for m in monsters),
            "monsters": monsters
        })

if __name__ == "__main__":
    main()
