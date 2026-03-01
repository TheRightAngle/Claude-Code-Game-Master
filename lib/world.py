#!/usr/bin/env python3
"""
World context for DM operations.
Central entry point for all world state operations.
"""

import sys
from typing import Optional, Any, Dict
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from campaign_manager import CampaignManager
from json_ops import JsonOperations
from npc_manager import NPCManager
from location_manager import LocationManager
from plot_manager import PlotManager
from session_manager import SessionManager
from consequence_manager import ConsequenceManager
from player_manager import PlayerManager


class World:
    """Central context for all world state operations.

    Provides a unified interface to all entity managers and campaign data.
    Each manager shares the same campaign context, ensuring consistency.

    Usage:
        # Use active campaign
        world = World()

        # Use specific campaign
        world = World("conan")

        # Access managers
        world.npcs.create("Theron", "A brave warrior", "ally")
        world.locations.add("Tavern", "center of town")
        world.plots.list()

        # Get campaign info
        print(world.campaign_name)
        print(world.current_location)
    """

    def __init__(self, campaign_name: str = None):
        """Initialize world context.

        Args:
            campaign_name: Name of campaign to load. If None, uses active campaign.

        Raises:
            RuntimeError: If no active campaign is set and no name provided.
        """
        self.campaign_mgr = CampaignManager()

        if campaign_name:
            if not self.campaign_mgr.set_active(campaign_name):
                raise RuntimeError(f"Campaign '{campaign_name}' does not exist.")

        self.campaign_dir = self.campaign_mgr.get_active_campaign_dir()

        if self.campaign_dir is None:
            raise RuntimeError("No active campaign. Run /new-game or /import first.")

        self.json_ops = JsonOperations(str(self.campaign_dir))
        self._campaign_name = self.campaign_dir.name
        self._world_state_dir = str(self.campaign_dir.parent.parent)

        # Lazy-loaded manager instances pinned to this world's campaign.
        self._npcs = None
        self._locations = None
        self._plots = None
        self._session = None
        self._consequences = None
        self._player = None

    def _create_pinned_manager(self, manager_cls):
        """Create manager bound to this world's campaign, restoring global active campaign afterwards."""
        previous_active = self.campaign_mgr.get_active()
        switched = previous_active != self._campaign_name

        if switched and not self.campaign_mgr.set_active(self._campaign_name):
            raise RuntimeError(
                f"Failed to set active campaign to pinned campaign '{self._campaign_name}'"
            )

        try:
            manager = manager_cls(self._world_state_dir)
        finally:
            if switched and previous_active and not self.campaign_mgr.set_active(previous_active):
                raise RuntimeError(
                    f"Failed to restore active campaign '{previous_active}' "
                    f"after creating manager for '{self._campaign_name}'"
                )

        return manager

    # Lazy-loaded manager properties
    # This avoids loading all managers when only one is needed

    @property
    def npcs(self) -> NPCManager:
        """NPC manager for creating and updating NPCs."""
        if self._npcs is None:
            self._npcs = self._create_pinned_manager(NPCManager)
        return self._npcs

    @property
    def locations(self) -> LocationManager:
        """Location manager for world geography."""
        if self._locations is None:
            self._locations = self._create_pinned_manager(LocationManager)
        return self._locations

    @property
    def plots(self) -> PlotManager:
        """Plot manager for quests and storylines."""
        if self._plots is None:
            self._plots = self._create_pinned_manager(PlotManager)
        return self._plots

    @property
    def session(self) -> SessionManager:
        """Session manager for game state and saves."""
        if self._session is None:
            self._session = self._create_pinned_manager(SessionManager)
        return self._session

    @property
    def consequences(self) -> ConsequenceManager:
        """Consequence manager for tracking future events."""
        if self._consequences is None:
            self._consequences = self._create_pinned_manager(ConsequenceManager)
        return self._consequences

    @property
    def player(self) -> PlayerManager:
        """Player manager for character stats."""
        if self._player is None:
            self._player = self._create_pinned_manager(PlayerManager)
        return self._player

    # Convenience properties for common data

    @property
    def campaign_name(self) -> Optional[str]:
        """Get the name of the active campaign."""
        return self._campaign_name

    @property
    def current_location(self) -> Optional[str]:
        """Get the party's current location."""
        overview = self.json_ops.load_json("campaign-overview.json")
        if not isinstance(overview, dict):
            return None
        player_position = overview.get("player_position", {})
        if not isinstance(player_position, dict):
            return None
        return player_position.get("current_location")

    @property
    def time_of_day(self) -> Optional[str]:
        """Get the current time of day."""
        overview = self.json_ops.load_json("campaign-overview.json")
        if not isinstance(overview, dict):
            return None
        return overview.get("time_of_day")

    @property
    def current_date(self) -> Optional[str]:
        """Get the current in-game date."""
        overview = self.json_ops.load_json("campaign-overview.json")
        if not isinstance(overview, dict):
            return None
        return overview.get("current_date")

    @property
    def character(self) -> Optional[Dict[str, Any]]:
        """Get the player character data."""
        char_file = self.campaign_dir / "character.json"
        if char_file.exists():
            return self.json_ops.load_json("character.json")
        return None

    def get_overview(self) -> Dict[str, Any]:
        """Get the full campaign overview."""
        return self.json_ops.load_json("campaign-overview.json") or {}

    def update_overview(self, updates: Dict[str, Any]) -> bool:
        """Update the campaign overview with new values.

        Args:
            updates: Dictionary of fields to update

        Returns:
            True on success
        """
        overview = self.get_overview()
        overview.update(updates)
        return self.json_ops.save_json("campaign-overview.json", overview)

    def move_to(self, location: str) -> Dict[str, str]:
        """Move the party to a new location.

        Args:
            location: Name of the destination location

        Returns:
            Dict with previous_location and current_location
        """
        return self.session.move_party(location)

    def get_status(self) -> Dict[str, Any]:
        """Get a summary of the current world state.

        Returns:
            Dict with counts and current state info
        """
        npcs = self.json_ops.load_json("npcs.json")
        locations = self.json_ops.load_json("locations.json")
        consequences = self.json_ops.load_json("consequences.json")

        if isinstance(consequences, dict):
            active_consequences = consequences.get("active", [])
        elif isinstance(consequences, list):
            active_consequences = consequences
        else:
            active_consequences = []

        if not isinstance(active_consequences, list):
            active_consequences = []

        return {
            "campaign": self.campaign_name,
            "location": self.current_location,
            "time": self.time_of_day,
            "date": self.current_date,
            "npcs_count": len(npcs) if isinstance(npcs, (dict, list)) else 0,
            "locations_count": len(locations) if isinstance(locations, (dict, list)) else 0,
            "active_consequences": len(active_consequences),
        }

    def save_all(self):
        """Force save all cached data.

        Currently a no-op as managers save immediately.
        Reserved for future caching implementation.
        """
        pass


def main():
    """CLI interface for world operations."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='World context operations')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Status
    subparsers.add_parser('status', help='Get world status summary')

    # Overview
    subparsers.add_parser('overview', help='Get full campaign overview')

    # Move
    move_parser = subparsers.add_parser('move', help='Move party to location')
    move_parser.add_argument('location', nargs='+', help='Destination location')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    try:
        world = World()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if args.action == 'status':
        status = world.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.action == 'overview':
        overview = world.get_overview()
        print(json.dumps(overview, indent=2, ensure_ascii=False))

    elif args.action == 'move':
        location = ' '.join(args.location)
        result = world.move_to(location)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
