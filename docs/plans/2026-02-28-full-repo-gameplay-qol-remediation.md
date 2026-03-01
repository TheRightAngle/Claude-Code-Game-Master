# Full Repo Gameplay and QoL Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix confirmed gameplay logic, continuity, and quality-of-life bugs across core, feature APIs, and advanced modules while increasing regression coverage.

**Architecture:** Apply focused, behavior-preserving fixes in the owning modules; add regression tests first for each defect; then verify end-to-end with full test runs from repository root.

**Tech Stack:** Python 3.11+, bash tools, pytest.

---

### Task 1: Protect Campaign Data During Import Cleanup

**Files:**
- Modify: `tools/dm-extract.sh`
- Test: `tests/test_dm_extract_cli_safety.py` (new)

**Step 1: Write the failing test**
- Add a test proving `clean` only removes extraction artifacts and never deletes the campaign root or core files.

**Step 2: Run test to verify it fails**
- Run: `uv run pytest tests/test_dm_extract_cli_safety.py -q`

**Step 3: Write minimal implementation**
- Update `clean` behavior to delete only `extracted/`, `chunks/`, and temporary extraction files.
- Keep campaign directory and gameplay files intact.

**Step 4: Run test to verify it passes**
- Run: `uv run pytest tests/test_dm_extract_cli_safety.py -q`

---

### Task 2: Make Session Save/Restore Complete and Atomic

**Files:**
- Modify: `lib/session_manager.py`
- Test: `tests/test_session_manager.py`

**Step 1: Write the failing tests**
- Add tests that save/restore round-trips include `plots.json` and `items.json`.
- Add test that restore failure does not partially mutate campaign files.
- Add test that ending a session increments/persists `session_count`.

**Step 2: Run tests to verify failure**
- Run: `uv run pytest tests/test_session_manager.py -q`

**Step 3: Write minimal implementation**
- Include `plots.json` and `items.json` in save snapshots.
- Implement restore rollback/atomic behavior (backup then rollback on write failure).
- Update `session_count` during session end.

**Step 4: Run tests to verify pass**
- Run: `uv run pytest tests/test_session_manager.py -q`

---

### Task 3: Harden Core Gameplay Managers and CLI QoL

**Files:**
- Modify: `lib/player_manager.py`
- Modify: `lib/plot_manager.py`
- Modify: `lib/time_manager.py`
- Modify: `tools/dm-search.sh`
- Test: `tests/test_player_manager.py`
- Test: `tests/test_plot_manager.py` (new)
- Test: `tests/test_time_manager.py` (new)
- Test: `tests/test_dm_search_cli.py` (new)

**Step 1: Write the failing tests**
- Player manager: provided name mismatch in single-character mode should fail without mutating data.
- Plot manager: mixed-type list entries in searchable fields should not crash search.
- Time manager/session context compatibility: top-level and nested time values remain consistent.
- Search CLI: reject `--world-only` + `--rag-only` combination.

**Step 2: Run tests to verify failure**
- Run: `uv run pytest tests/test_player_manager.py tests/test_plot_manager.py tests/test_time_manager.py tests/test_dm_search_cli.py -q`

**Step 3: Write minimal implementation**
- Enforce name-match guard in single-character operations.
- Type-guard list entry lowercasing in plot search.
- Write time updates to both canonical locations used by context display.
- Add mutually-exclusive flag validation in search shell wrapper.

**Step 4: Run tests to verify pass**
- Run: `uv run pytest tests/test_player_manager.py tests/test_plot_manager.py tests/test_time_manager.py tests/test_dm_search_cli.py -q`

---

### Task 4: Fix Feature API and Rules Accuracy Bugs

**Files:**
- Modify: `features/character-creation/save_character.py`
- Modify: `features/dnd-api/monsters/dnd_monsters.py`
- Modify: `features/dnd-api/monsters/dnd_encounter_v2.py`
- Modify: `features/dnd-api/monsters/dnd_monsters_api_filter.py`
- Modify: `features/rules/list_rules.py`
- Modify: `features/gear/dnd_equipment_list.py`
- Modify: `features/rules/combat_rules.py`
- Test: `tests/test_feature_api_behavior_fixes.py`

**Step 1: Write the failing tests**
- Validate character level type/range in save character flow.
- Verify red dragon wyrmling CR filtering correctness.
- Verify fractional CR input support (`1/2`, `1/4`, `1/8`) in relevant monster scripts.
- Verify negative `--limit` is rejected where currently accepted.
- Verify corrected death-save rule copy.

**Step 2: Run tests to verify failure**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -q`

**Step 3: Write minimal implementation**
- Add strict level validation in character creation save path.
- Correct incorrect cached CR data and add stable filtered total metadata.
- Add shared CR parsing helper support for fractions.
- Enforce non-negative limits consistently.
- Correct death-save rules text.

**Step 4: Run tests to verify pass**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -q`

---

### Task 5: Repair Advanced Module Gameplay Paths

**Files:**
- Modify: `.claude/modules/world-travel/lib/navigation_manager.py`
- Modify: `.claude/modules/world-travel/middleware/dm-session.sh`
- Modify: `.claude/modules/world-travel/tools/dm-navigation.sh`
- Modify: `.claude/modules/world-travel/module.json`
- Modify: `.claude/modules/firearms-combat/lib/firearms_resolver.py`
- Test: `.claude/modules/world-travel/tests/*` (update/add targeted tests)
- Test: `.claude/modules/firearms-combat/tests/test_firearms_resolver.py`

**Step 1: Write the failing tests**
- World travel: middleware auto-encounter receives usable move metadata from navigation output.
- Firearms: unsupported fire modes and enemy flags fail fast with accurate messaging.
- Firearms: ammo persistence message reflects true behavior.
- World-travel command metadata uses valid command names.

**Step 2: Run tests to verify failure**
- Run: `uv run pytest .claude/modules/world-travel .claude/modules/firearms-combat/tests/test_firearms_resolver.py -q`

**Step 3: Write minimal implementation**
- Add structured move output mode and consume it from middleware.
- Prevent misleading acceptance of unimplemented fire modes/flags (or hard-disable cleanly).
- Fix ammo persistence messaging to match actual behavior.
- Align module command metadata (`route` vs `routes`) via alias or manifest correction.

**Step 4: Run tests to verify pass**
- Run: `uv run pytest .claude/modules/world-travel .claude/modules/firearms-combat/tests/test_firearms_resolver.py -q`

---

### Task 6: Repository-Wide Verification and Category Commits

**Files:**
- Modify: `docs/plans/2026-02-28-full-repo-gameplay-qol-remediation.md` (status notes if needed)

**Step 1: Run full verification at top level**
- Run: `uv run pytest -q`

**Step 2: Run focused smoke commands for CLI wrappers**
- Run: `bash tools/dm-search.sh --help`
- Run: `bash tools/dm-extract.sh --help`

**Step 3: Create category commits at top level**
- Commit 1: Core/session/tooling safety fixes + tests
- Commit 2: Feature API/rules correctness fixes + tests
- Commit 3: Advanced module gameplay fixes + tests
