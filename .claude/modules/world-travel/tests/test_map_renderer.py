#!/usr/bin/env python3
"""Regression tests for ASCII map rendering."""

import json
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(MODULE_DIR))

from map_renderer import MapRenderer


def test_render_map_places_locations_inside_grid(tmp_path):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir(parents=True)

    (campaign_dir / "campaign-overview.json").write_text(
        json.dumps(
            {
                "campaign_name": "Renderer Test",
                "player_position": {"current_location": "Alpha"},
            }
        ),
        encoding="utf-8",
    )
    (campaign_dir / "locations.json").write_text(
        json.dumps(
            {
                "Alpha": {
                    "coordinates": {"x": 1000, "y": 10},
                    "connections": [{"to": "Beta", "path": "road"}],
                },
                "Beta": {
                    "coordinates": {"x": 2000, "y": 20},
                    "connections": [{"to": "Alpha", "path": "road"}],
                },
            }
        ),
        encoding="utf-8",
    )

    renderer = MapRenderer(str(campaign_dir))
    output = renderer.render_map(width=40, height=20, show_labels=False, show_compass=False, use_colors=False)

    lines = output.splitlines()
    grid_lines = lines[3:23]
    grid_text = "\n".join(grid_lines)

    assert "@" in grid_text
    assert "●" in grid_text
