# Full Repo Review Remediation V4 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all confirmed logic, gameplay-flow, functionality, and quality-of-life defects found in the full-repo review, with regression tests for each bug.

**Architecture:** Apply targeted bugfixes in owning modules with strict TDD: write failing tests first for each defect, implement minimal fixes, then run targeted + full-suite verification. Keep behavior backward-compatible except where invalid input should fail fast with clear errors.

**Tech Stack:** Python 3.11+, Bash wrappers, pytest (core + feature + module suites), existing manager classes.

---

### Task 1: Fix Core Save/World Consistency Bugs

**Files:**
- Modify: `lib/session_manager.py`
- Modify: `lib/world.py`
- Modify: `tests/test_session_manager.py`
- Modify: `tests/test_world_stats.py`
- Create/Modify: `tests/test_world.py`

**Step 1: Write the failing tests**
- Add test: duplicate save names created within the same second produce distinct save files.
- Add test: partial save restore chooses deterministic best match (newest timestamp match) instead of first filesystem hit.
- Add tests: `World.get_status()` tolerates malformed `player_position` and legacy list-style `consequences.json` without traceback.
- Add test: `World` manager properties remain pinned to the campaign passed at construction even if global active campaign changes.

**Step 2: Run tests to verify failure**
- Run: `uv run pytest tests/test_session_manager.py tests/test_world.py -q`

**Step 3: Write minimal implementation**
- `session_manager.py`: ensure unique save filenames (append numeric suffix when collision detected).
- `session_manager.py`: make `_find_save()` deterministic for partial matches (prefer exact, then newest timestamped match).
- `world.py`: normalize malformed overview shapes (`player_position` dict guard, consequences dict/list guard).
- `world.py`: initialize all managers with campaign-specific paths (no active-campaign drift).

**Step 4: Run tests to verify pass**
- Run: `uv run pytest tests/test_session_manager.py tests/test_world.py -q`

---

### Task 2: Fix CLI Wrapper and Search QoL Defects

**Files:**
- Modify: `tools/dm-note.sh`
- Modify: `tools/dm-time.sh`
- Modify: `tools/dm-search.sh`
- Modify: `tests/test_note_manager.py`
- Modify: `tests/test_time_manager.py`
- Modify: `tests/test_dm_search_cli.py`

**Step 1: Write the failing tests**
- Add CLI integration test: `dm-note.sh categories` works when invoked from non-repo cwd.
- Add CLI integration test: `dm-time.sh` works when invoked from non-repo cwd.
- Add CLI test: unquoted multi-token search query preserves all terms (`foo bar` -> `"foo bar"`).

**Step 2: Run tests to verify failure**
- Run: `uv run pytest tests/test_note_manager.py tests/test_time_manager.py tests/test_dm_search_cli.py -q`

**Step 3: Write minimal implementation**
- Use script-path invocation (`$LIB_DIR/*.py`) in wrappers instead of `python -m lib.*`.
- In `dm-search.sh`, accumulate positional tokens into a single query string rather than silently discarding extra words.

**Step 4: Run tests to verify pass**
- Run: `uv run pytest tests/test_note_manager.py tests/test_time_manager.py tests/test_dm_search_cli.py -q`

---

### Task 3: Fix Feature API/Data Correctness Bugs

**Files:**
- Modify: `features/character-creation/save_character.py`
- Modify: `features/spells/spell_api_core.py`
- Modify: `features/gear/dnd_magic_item.py`
- Modify: `features/character-creation/api/get_class_details.py`
- Modify: `features/dnd-api/monsters/dnd_monsters.py`
- Modify: `tests/test_feature_api_behavior_fixes.py`

**Step 1: Write the failing tests**
- Add test: stat values in `save_character` must be integers (reject floats).
- Add test: slash spell names (e.g., `Blindness/Deafness`) resolve correctly.
- Add test: punctuation-heavy magic item names (e.g., `Spell Scroll (1st)`) resolve correctly.
- Add test: class details expose meaningful `primary_ability` for spellcasting classes.
- Add test: reversed CR ranges (`5-1`) return validation error instead of silent empty success.

**Step 2: Run tests to verify failure**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -q`

**Step 3: Write minimal implementation**
- Enforce integral stat values in character creation validation.
- Improve spell/item index normalization for common punctuation and separators.
- Extract `primary_ability` from spellcasting payload when available.
- Validate CR ranges with explicit `min <= max` check.

**Step 4: Run tests to verify pass**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -q`

---

### Task 4: Fix Advanced Module Gameplay Integrity Bugs

**Files:**
- Modify: `.claude/modules/custom-stats/lib/survival_engine.py`
- Modify: `.claude/modules/world-travel/lib/navigation_manager.py`
- Modify: `.claude/modules/world-travel/lib/encounter_engine.py`
- Modify: `.claude/modules/custom-stats/tests/test_survival_engine.py`
- Modify: `.claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py`
- Modify: `.claude/modules/world-travel/tests/test_encounter_engine.py`

**Step 1: Write the failing tests**
- Add test: `advance_time()` updates canonical top-level time fields as well as nested `time` block.
- Add test: `modify_custom_stat(name=...)` honors requested target and errors when name mismatches active/single-character state.
- Add test: navigation move with `speed_kmh <= 0` fails gracefully (no `ZeroDivisionError`).
- Add test: encounter stat config `stealth` maps to stealth skill path (or normalized equivalent), not nonexistent ability key.

**Step 2: Run tests to verify failure**
- Run: `uv run pytest .claude/modules/custom-stats/tests/test_survival_engine.py .claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`

**Step 3: Write minimal implementation**
- Sync top-level and nested time fields in custom-stats time advance.
- Route custom-stat updates through character lookup semantics that respect `name` argument.
- Validate effective speed before travel-time division.
- Normalize encounter stat configuration (`stealth` => skill lookup) while preserving existing `skill:*` behavior.

**Step 4: Run tests to verify pass**
- Run: `uv run pytest .claude/modules/custom-stats/tests/test_survival_engine.py .claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`

---

### Task 5: Top-Level Verification and Category Commits (Orchestrator)

**Files:**
- Modify (optional status notes): `docs/plans/2026-03-01-full-repo-review-remediation-v4.md`

**Step 1: Run integration verification from repository root**
- Run: `uv run pytest -q`

**Step 2: Run CLI smoke checks**
- Run: `bash tools/dm-search.sh --help`
- Run: `bash tools/dm-note.sh categories` (from both repo root and `/tmp`)
- Run: `bash tools/dm-time.sh Morning "Day 1"` (in test campaign context, from both repo root and `/tmp`)

**Step 3: Create category commits at top level (orchestrator only)**
- Commit 1: Core save/world consistency fixes + tests.
- Commit 2: CLI/QoL wrapper fixes + tests.
- Commit 3: Feature API correctness fixes + tests.
- Commit 4: Advanced module gameplay integrity fixes + tests.
