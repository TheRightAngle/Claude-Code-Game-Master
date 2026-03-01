# Full Repo Logic & QoL Remediation V2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all confirmed user-impacting logic, gameplay-flow, and CLI QoL defects found in the full-repo review, with regression tests for each fix.

**Architecture:** Apply focused bug fixes in the owning modules, adding tests first for each defect. Keep behavior backward-compatible where possible, but fail fast on invalid input instead of hanging/crashing. Validate everything via targeted suites then full repo tests.

**Tech Stack:** Python 3.11+, bash tool wrappers, pytest, existing module test suites.

---

### Task 1: Fix Core CLI Failure Modes

**Files:**
- Modify: `tools/dm-search.sh`
- Modify: `tools/dm-enhance.sh`
- Modify: `tests/test_dm_search_cli.py`
- Create: `tests/test_dm_enhance_cli.py`

**Step 1: Write failing tests**
- Add `dm-search` tests for missing values on `-n`, `--tag-location`, `--tag-quest` to ensure non-hanging validation errors.
- Add `dm-enhance` test proving no-active-campaign path exits cleanly without Python traceback.

**Step 2: Run targeted tests to verify failure**
- Run: `uv run pytest tests/test_dm_search_cli.py tests/test_dm_enhance_cli.py -q`

**Step 3: Write minimal implementation**
- Validate option value presence before `shift 2` in `dm-search.sh`; fail with actionable error.
- Add `require_active_campaign` guard early in `dm-enhance.sh`.

**Step 4: Run targeted tests to verify pass**
- Run: `uv run pytest tests/test_dm_search_cli.py tests/test_dm_enhance_cli.py -q`

---

### Task 2: Harden Core Search/Stats/NPC Robustness

**Files:**
- Modify: `lib/search.py`
- Modify: `lib/world_stats.py`
- Modify: `lib/npc_manager.py`
- Modify: `tests/test_search.py`
- Modify: `tests/test_world_stats.py`
- Modify: `tests/test_npc_manager.py`

**Step 1: Write failing tests**
- Add search tests for non-dict JSON payloads and string facts lists.
- Add world-stats detailed mode test for malformed entity entries.
- Add NPC stat update test for party member sheet missing `hp` structure.

**Step 2: Run targeted tests to verify failure**
- Run: `uv run pytest tests/test_search.py tests/test_world_stats.py tests/test_npc_manager.py -q`

**Step 3: Write minimal implementation**
- Guard all `.items()` and list traversals in `search.py` for malformed JSON shapes.
- Ensure `search`/`print_results` support facts as either dict entries or plain strings.
- Make `world_stats` detailed extraction skip malformed entity records safely.
- Make `npc_manager` `hp_max` updates validate/create safe hp structure or fail gracefully.

**Step 4: Run targeted tests to verify pass**
- Run: `uv run pytest tests/test_search.py tests/test_world_stats.py tests/test_npc_manager.py -q`

---

### Task 3: Fix Feature API/Data Correctness Bugs

**Files:**
- Modify: `features/spells/list_spells.py`
- Modify: `features/spells/spell_api_core.py`
- Modify: `features/gear/dnd_magic_item.py`
- Modify: `features/character-creation/save_character.py`
- Modify: `features/character-creation/api/get_class_details.py`
- Modify: `tests/test_feature_api_behavior_fixes.py`

**Step 1: Write failing tests**
- Add regression for `--limit 0` in spell listing.
- Add regression for smart-quote spell and magic-item lookups.
- Add invalid-type character payload test (e.g., null name) expecting clean validation error.
- Add class detail test that all proficiency choice groups are preserved.

**Step 2: Run targeted tests to verify failure**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -q`

**Step 3: Write minimal implementation**
- Make limit logic honor explicit `0`.
- Normalize Unicode apostrophes before slug/url encoding in affected API callers.
- Add strict type validation for key required character fields with user-facing errors.
- Return all proficiency choice groups (not just first) from class details.

**Step 4: Run targeted tests to verify pass**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -q`

---

### Task 4: Repair World-Travel + Custom-Stats Integration

**Files:**
- Modify: `.claude/modules/world-travel/lib/navigation_manager.py`
- Modify: `.claude/modules/world-travel/lib/encounter_engine.py`
- Modify: `.claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py`
- Modify: `.claude/modules/world-travel/tests/test_encounter_engine.py`

**Step 1: Write failing tests**
- Add navigation test asserting survival hook is invoked with required `time_of_day` + `date` args.
- Add waypoint cleanup test asserting neighbor connections to waypoint are removed.

**Step 2: Run targeted tests to verify failure**
- Run: `uv run pytest .claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`

**Step 3: Write minimal implementation**
- Pass current/new time context to survival CLI invocation so travel updates stats/time.
- On waypoint cleanup, remove any backlinks in all locations before deleting waypoint.

**Step 4: Run targeted tests to verify pass**
- Run: `uv run pytest .claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`

---

### Task 5: Repair Firearms and Inventory Module Integrity

**Files:**
- Modify: `.claude/modules/firearms-combat/lib/firearms_resolver.py`
- Modify: `.claude/modules/firearms-combat/tests/test_firearms_resolver.py`
- Modify: `.claude/modules/inventory-system/lib/inventory_manager.py`
- Create: `.claude/modules/inventory-system/tests/test_inventory_manager.py`

**Step 1: Write failing tests**
- Add firearms tests asserting distributed target shots always sum to `shots_fired`.
- Add inventory tests asserting negative remove quantities are rejected.
- Add inventory CLI test asserting provided character name must match active character (or fail fast).

**Step 2: Run targeted tests to verify failure**
- Run: `uv run pytest .claude/modules/firearms-combat/tests/test_firearms_resolver.py .claude/modules/inventory-system/tests/test_inventory_manager.py -q`

**Step 3: Write minimal implementation**
- Allocate full-auto shots deterministically so totals exactly match ammo consumed.
- Reject non-positive remove/set/add quantities where semantically invalid.
- Enforce character argument validation in inventory CLI entry points.

**Step 4: Run targeted tests to verify pass**
- Run: `uv run pytest .claude/modules/firearms-combat/tests/test_firearms_resolver.py .claude/modules/inventory-system/tests/test_inventory_manager.py -q`

---

### Task 6: Top-Level Verification and Category Commits

**Files:**
- Modify: `docs/plans/2026-03-01-full-repo-logic-qol-remediation-v2.md` (optional status notes)

**Step 1: Run integration verification from repository root**
- Run: `uv run pytest -q`

**Step 2: CLI smoke verification**
- Run: `bash tools/dm-search.sh --help`
- Run: `bash tools/dm-enhance.sh --help`

**Step 3: Create category commits at top level (orchestrator only)**
- Commit 1: Core CLI and robustness fixes + tests
- Commit 2: Feature API/data correctness fixes + tests
- Commit 3: Advanced module travel/combat/inventory fixes + tests
