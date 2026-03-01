# Full Repo Crash-Resilience Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate user-facing crash paths and high-friction gameplay/CLI failures discovered in full-repo review, with regression tests for each defect.

**Architecture:** Add failing tests for malformed/corrupted state and invalid runtime inputs, then apply minimal defensive guards in owning modules. Keep existing behavior for valid data unchanged while returning actionable errors for invalid inputs.

**Tech Stack:** Python 3.11+, bash wrappers, pytest (core + module suites), existing manager classes.

---

### Task 1: Harden Core Search/Overview/Time Against Malformed State

**Files:**
- Modify: `tests/test_search.py`
- Modify: `tests/test_world_stats.py`
- Modify: `tests/test_time_manager.py`
- Modify: `lib/search.py`
- Modify: `lib/world_stats.py`
- Modify: `lib/time_manager.py`

**Step 1: Write the failing test**

```python
def test_search_npcs_and_locations_tolerate_non_string_fields(...): ...
def test_print_results_tolerates_non_list_location_connections(...): ...
def test_world_stats_counts_tolerate_non_list_consequences(...): ...
def test_time_manager_handles_non_dict_overview_payload(...): ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_search.py tests/test_world_stats.py tests/test_time_manager.py -q`
Expected: FAIL on malformed-state crash regressions.

**Step 3: Write minimal implementation**

```python
# search.py
# - coerce description/position fields to strings before .lower()
# - only call len() on list-type location connections

# world_stats.py
# - treat consequences.active/resolved as 0 unless they are lists

# time_manager.py
# - normalize campaign-overview payload to dict in update_time/get_time
# - fail cleanly (False + error message) instead of traceback
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_search.py tests/test_world_stats.py tests/test_time_manager.py -q`
Expected: PASS.

---

### Task 2: Fix World-Travel Invalid-Input and use_luck Crash Paths

**Files:**
- Modify: `.claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py`
- Modify: `.claude/modules/world-travel/tests/test_encounter_engine.py`
- Modify: `.claude/modules/world-travel/lib/navigation_manager.py`
- Modify: `.claude/modules/world-travel/lib/encounter_engine.py`

**Step 1: Write the failing test**

```python
def test_move_rejects_non_positive_speed_multiplier(...): ...
def test_roll_encounter_nature_with_luck_uses_campaign_character(...): ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest .claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`
Expected: FAIL for speed-multiplier validation and `use_luck` runtime path.

**Step 3: Write minimal implementation**

```python
# navigation_manager.py
# - reject speed_multiplier <= 0 with structured error dict

# encounter_engine.py
# - initialize PlayerManager with module campaign path in direct-campaign mode
#   (no active-campaign global requirement)
# - keep existing behavior when use_luck is disabled
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest .claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`
Expected: PASS.

---

### Task 3: Top-Level Integration Verification and Category Commits (Orchestrator)

**Files:**
- Modify: `docs/plans/2026-03-01-full-repo-crash-resilience-remediation.md` (optional progress notes)

**Step 1: Run targeted integration verification from repo root**

Run: `uv run pytest tests/test_search.py tests/test_world_stats.py tests/test_time_manager.py .claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`

**Step 2: Run full suite verification from repo root**

Run: `uv run pytest -q`

**Step 3: Run gameplay CLI smoke checks**

Run: `bash tools/dm-search.sh --help`
Run: `bash tools/dm-time.sh Morning "Day 2"` (in temp campaign test context)

**Step 4: Create category commits at top level (orchestrator only)**

```bash
# Commit 1: Core malformed-state resilience
# files: lib/search.py lib/world_stats.py lib/time_manager.py tests/test_search.py tests/test_world_stats.py tests/test_time_manager.py

# Commit 2: World-travel runtime resilience
# files: .claude/modules/world-travel/lib/navigation_manager.py .claude/modules/world-travel/lib/encounter_engine.py .claude/modules/world-travel/tests/test_navigation_manager_survival_hook.py .claude/modules/world-travel/tests/test_encounter_engine.py
```
