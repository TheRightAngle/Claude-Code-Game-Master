#!/usr/bin/env python3
"""
Get detailed information about a specific class
Usage: uv run python get_class_details.py <class>
Example: uv run python get_class_details.py wizard
"""

import sys
import argparse
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from character_creation_core import fetch, output, error_output

SPELLCASTING_PRIMARY_ABILITY_FALLBACKS = {
    "artificer": "INT",
    "bard": "CHA",
    "cleric": "WIS",
    "druid": "WIS",
    "paladin": "CHA",
    "ranger": "WIS",
    "sorcerer": "CHA",
    "warlock": "CHA",
    "wizard": "INT",
}


def extract_class_details(class_data):
    """Extract key class information"""
    proficiency_choices = class_data.get("proficiency_choices", [])
    choice_groups = [
        {
            "choose": choice.get("choose", 0),
            "from": [
                option.get("item", {}).get("name", "")
                for option in choice.get("from", {}).get("options", [])
            ],
        }
        for choice in proficiency_choices
    ]
    primary_skill_choice = choice_groups[0] if choice_groups else {"choose": 0, "from": []}
    spellcasting_data = class_data.get("spellcasting") or {}

    primary_ability = class_data.get("primary_ability", "")
    if not primary_ability and isinstance(spellcasting_data, dict):
        primary_ability = (
            spellcasting_data.get("spellcasting_ability", {}) or {}
        ).get("name", "")
    if not primary_ability and spellcasting_data:
        primary_ability = SPELLCASTING_PRIMARY_ABILITY_FALLBACKS.get(
            class_data.get("index", class_data.get("name", "")).lower(),
            "",
        )

    return {
        "name": class_data.get("name", "Unknown"),
        "hit_die": class_data.get("hit_die", 0),
        "primary_ability": primary_ability,
        "saving_throw_proficiencies": [
            prof.get("name", "") for prof in class_data.get("saving_throws", [])
        ],
        "proficiencies": [
            prof.get("name", "") for prof in class_data.get("proficiencies", [])
        ],
        "skill_choices": {
            "choose": primary_skill_choice["choose"],
            "from": primary_skill_choice["from"],
            "groups": choice_groups,
        },
        "starting_equipment": [
            equip.get("equipment", {}).get("name", "") 
            for equip in class_data.get("starting_equipment", [])
        ],
        "spellcasting": bool(spellcasting_data),
        "subclasses": [
            {
                "name": subclass.get("name", ""),
                "index": subclass.get("index", "")
            }
            for subclass in class_data.get("subclasses", [])
        ]
    }

def main():
    parser = argparse.ArgumentParser(description='Get class details')
    parser.add_argument('class_name', help='Class identifier (e.g., wizard, fighter)')
    
    args = parser.parse_args()
    
    # Convert to API format
    class_id = args.class_name.lower().replace(' ', '-')
    
    # Fetch class details
    data = fetch(f"/classes/{class_id}")
    
    if "error" in data:
        if data.get("error") == "HTTP 404":
            error_output(f"Class '{args.class_name}' not found")
        else:
            error_output(f"Failed to fetch class: {data.get('message', 'Unknown error')}")
    
    # Extract and output details
    output(extract_class_details(data))

if __name__ == "__main__":
    main()
