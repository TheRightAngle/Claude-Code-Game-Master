#!/usr/bin/env python3
"""
Get D&D 5e rule details
Usage: uv run python get_rule.py <rule-name> [options]
Example: uv run python get_rule.py advantage
"""

import sys
import argparse
import re
from urllib.parse import urlparse
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from rules_api_core import fetch, output, error_output


def normalize_key(value):
    """Normalize text for reliable matching."""
    lowered = value.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")


def subsection_endpoint(url):
    """Convert subsection URL/path into rules_api_core-compatible endpoint."""
    if not url:
        return None

    parsed_path = urlparse(url).path if url.startswith("http") else url
    if parsed_path.startswith("/api/2014"):
        parsed_path = parsed_path[len("/api/2014"):]
    if not parsed_path.startswith("/"):
        parsed_path = f"/{parsed_path}"
    return parsed_path


def find_subsection(subsections, subsection_name):
    """Find subsection by name, slug, or URL suffix."""
    wanted = normalize_key(subsection_name)
    for subsection in subsections:
        candidates = [
            subsection.get("name", ""),
            subsection.get("index", ""),
            subsection.get("url", "").split("/")[-1],
        ]
        if any(normalize_key(candidate) == wanted for candidate in candidates if candidate):
            return subsection
    return None

def format_rule_output(rule_data):
    """Format rule data for clean display"""
    formatted = {
        "name": rule_data.get("name", "Unknown"),
        "desc": rule_data.get("desc", ""),
    }
    
    # Add subsections if available
    if "subsections" in rule_data and rule_data["subsections"]:
        formatted["subsections"] = []
        for subsection in rule_data["subsections"]:
            formatted["subsections"].append({
                "name": subsection.get("name", ""),
                "url": subsection.get("url", "")
            })
    
    return formatted

def search_rules(search_term):
    """Search through all available rules"""
    # First, get all rules
    data = fetch("/rules")
    
    if "error" in data:
        return None
    
    # Search through rules
    search_lower = search_term.lower()
    matches = []
    
    for rule in data.get("results", []):
        if search_lower in rule.get("name", "").lower():
            matches.append(rule)
    
    return matches

def main():
    parser = argparse.ArgumentParser(description='Get D&D 5e rule details')
    parser.add_argument('rule_name', help='Rule name or topic to look up')
    parser.add_argument('--subsection', help='Get specific subsection details')
    
    args = parser.parse_args()
    
    # Convert rule name to API format
    rule_index = args.rule_name.lower().replace(' ', '-')
    
    # Try direct lookup first
    data = fetch(f"/rules/{rule_index}")
    
    # If not found, try searching
    if "error" in data and data.get("error") == "HTTP 404":
        matches = search_rules(args.rule_name)
        
        if not matches:
            # Try rule sections
            sections_data = fetch("/rule-sections")
            if "error" not in sections_data:
                section_matches = []
                for section in sections_data.get("results", []):
                    if args.rule_name.lower() in section.get("name", "").lower():
                        section_matches.append(section)
                
                if section_matches:
                    error_output(f"Rule '{args.rule_name}' not found. Did you mean one of these rule sections?\n" + 
                               "\n".join([f"- {s['name']}" for s in section_matches[:5]]))
            
            error_output(f"Rule '{args.rule_name}' not found")
        else:
            # Show available matches
            error_output(f"Rule '{args.rule_name}' not found. Did you mean:\n" + 
                       "\n".join([f"- {r['name']}" for r in matches[:5]]))
    
    # Check for other errors
    if "error" in data:
        error_output(f"Failed to fetch rule: {data.get('message', 'Unknown error')}")

    if args.subsection:
        subsections = data.get("subsections", [])
        if not subsections:
            error_output(f"Rule '{data.get('name', args.rule_name)}' has no subsections")

        subsection = find_subsection(subsections, args.subsection)
        if subsection is None:
            available = "\n".join([f"- {s.get('name', 'Unknown')}" for s in subsections[:10]])
            error_output(
                f"Subsection '{args.subsection}' not found for rule '{data.get('name', args.rule_name)}'. "
                f"Available subsections:\n{available}"
            )

        endpoint = subsection_endpoint(subsection.get("url", ""))
        if endpoint is None:
            error_output(f"Subsection '{subsection.get('name', args.subsection)}' is missing a URL")

        subsection_data = fetch(endpoint)
        if "error" in subsection_data:
            error_output(
                f"Failed to fetch subsection '{subsection.get('name', args.subsection)}': "
                f"{subsection_data.get('message', 'Unknown error')}"
            )

        output({
            "rule": data.get("name", "Unknown"),
            "subsection": subsection_data,
        })
        return
    
    # Format and output
    output(format_rule_output(data))

if __name__ == "__main__":
    main()
