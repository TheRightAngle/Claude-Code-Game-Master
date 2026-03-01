# Full Repo Code Review Remediation V3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all confirmed gameplay/QoL logic defects discovered in the full-repo review, with regression tests for each defect and top-level verified category commits.

**Architecture:** Apply narrowly scoped bug fixes at script/module owners, prioritizing fail-fast CLI behavior and malformed-state resilience. Use TDD per bug: add failing regression tests first, implement minimal fix, then re-run targeted suites plus full integration from repo root. Keep subagents limited to working-tree edits only; top-level orchestrator owns final verification and commits.

**Tech Stack:** Bash tool wrappers, Python 3.11, pytest (`uv run pytest`), existing module test suites.

---

### Task 1: Harden Core CLI UX and Argument Validation

**Files:**
- Modify: `tools/dm-search.sh`
- Modify: `tools/dm-player.sh`
- Modify: `tests/test_dm_search_cli.py`
- Create: `tests/test_dm_player_cli.py`

**Step 1: Write the failing tests**

```python
def test_dm_search_unknown_flag_returns_error(...):
    ...

def test_dm_search_rejects_non_numeric_n(...):
    ...

def test_dm_player_unknown_action_is_nonzero(...):
    ...

def test_dm_player_help_without_active_campaign(...):
    ...
```

**Step 2: Run tests to verify RED**

Run: `uv run pytest tests/test_dm_search_cli.py tests/test_dm_player_cli.py -q`
Expected: FAIL for new unknown-flag / invalid-`-n` / dm-player action-exit behavior.

**Step 3: Write minimal implementation**

```bash
# dm-search.sh
# - reject unknown flags that start with '-'
# - validate -n is integer >= 0 regardless of RAG availability

# dm-player.sh
# - parse help/usage before require_active_campaign
# - return exit 1 for unknown/empty action errors
```

**Step 4: Run tests to verify GREEN**

Run: `uv run pytest tests/test_dm_search_cli.py tests/test_dm_player_cli.py -q`
Expected: PASS.

**Step 5: Commit (orchestrator later)**

```bash
git add tools/dm-search.sh tools/dm-player.sh tests/test_dm_search_cli.py tests/test_dm_player_cli.py
# commit deferred to orchestrator category-commit stage
```

---

### Task 2: Make Core State Search/Overview/Context Robust to Malformed Data

**Files:**
- Modify: `lib/search.py`
- Modify: `lib/world_stats.py`
- Modify: `lib/session_manager.py`
- Modify: `tests/test_search.py`
- Modify: `tests/test_world_stats.py`
- Modify: `tests/test_session_manager.py`

**Step 1: Write the failing tests**

```python
def test_search_tag_handles_non_string_tag_entries(...):
    ...

def test_search_related_plots_ignores_non_string_entries(...):
    ...

def test_search_getters_tolerate_non_dict_payloads(...):
    ...

def test_world_stats_handles_non_dict_player_position(...):
    ...

def test_session_context_handles_non_dict_time_and_position(...):
    ...
```

**Step 2: Run tests to verify RED**

Run: `uv run pytest tests/test_search.py tests/test_world_stats.py tests/test_session_manager.py -q`
Expected: FAIL on new malformed-state regressions.

**Step 3: Write minimal implementation**

```python
# search.py
# - guard tag/plot list traversals with isinstance(str)
# - harden get_npc/get_location/get_pending/get_facts helpers for non-dict roots

# world_stats.py
# - normalize overview/player_position to dicts before .get chains

# session_manager.py
# - normalize campaign/time/player_position to dicts in get_full_context
```

**Step 4: Run tests to verify GREEN**

Run: `uv run pytest tests/test_search.py tests/test_world_stats.py tests/test_session_manager.py -q`
Expected: PASS.

**Step 5: Commit (orchestrator later)**

```bash
git add lib/search.py lib/world_stats.py lib/session_manager.py tests/test_search.py tests/test_world_stats.py tests/test_session_manager.py
# commit deferred to orchestrator category-commit stage
```

---

### Task 3: Fix Advanced Module Input Validation and Crash Paths

**Files:**
- Modify: `.claude/modules/inventory-system/lib/inventory_manager.py`
- Modify: `.claude/modules/inventory-system/tests/test_inventory_manager.py`
- Modify: `.claude/modules/firearms-combat/lib/firearms_resolver.py`
- Modify: `.claude/modules/firearms-combat/tests/test_firearms_resolver.py`
- Modify: `.claude/modules/world-travel/lib/encounter_engine.py`
- Modify: `.claude/modules/world-travel/tests/test_encounter_engine.py`

**Step 1: Write the failing tests**

```python
def test_inventory_rejects_negative_add_quantity(...):
    ...

def test_inventory_rejects_negative_set_quantity(...):
    ...

def test_firearms_rejects_negative_ammo(...):
    ...

def test_encounter_engine_invalid_precise_time_falls_back(...):
    ...
```

**Step 2: Run tests to verify RED**

Run: `uv run pytest .claude/modules/inventory-system/tests/test_inventory_manager.py .claude/modules/firearms-combat/tests/test_firearms_resolver.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`
Expected: FAIL on new negative-quantity/ammo/time-format regressions.

**Step 3: Write minimal implementation**

```python
# inventory_manager.py
# - reject negative quantities for add/set operations

# firearms_resolver.py
# - enforce ammo_available >= 0 in resolver and CLI arg validation

# encounter_engine.py
# - parse precise_time defensively; fallback to default HH:MM when invalid
```

**Step 4: Run tests to verify GREEN**

Run: `uv run pytest .claude/modules/inventory-system/tests/test_inventory_manager.py .claude/modules/firearms-combat/tests/test_firearms_resolver.py .claude/modules/world-travel/tests/test_encounter_engine.py -q`
Expected: PASS.

**Step 5: Commit (orchestrator later)**

```bash
git add .claude/modules/inventory-system/lib/inventory_manager.py .claude/modules/inventory-system/tests/test_inventory_manager.py .claude/modules/firearms-combat/lib/firearms_resolver.py .claude/modules/firearms-combat/tests/test_firearms_resolver.py .claude/modules/world-travel/lib/encounter_engine.py .claude/modules/world-travel/tests/test_encounter_engine.py
# commit deferred to orchestrator category-commit stage
```

---

### Task 4: Top-Level Verification and Orchestrator Category Commits

**Files:**
- Modify: `docs/plans/2026-02-28-full-repo-code-review-remediation-v3.md` (optional status notes)

**Step 1: Run integration verification from repo root**

Run: `uv run pytest -q`
Expected: all core tests pass.

**Step 2: Run module verification from repo root**

Run: `uv run pytest .claude/modules/world-travel/tests .claude/modules/firearms-combat/tests .claude/modules/inventory-system/tests .claude/modules/custom-stats/tests -q`
Expected: all module tests pass.

**Step 3: CLI smoke checks**

Run: `bash tools/dm-search.sh --help`
Run: `bash tools/dm-player.sh --help`
Run: `bash tools/dm-enhance.sh --help`
Expected: usage/help displayed without stack traces.

**Step 4: Create category commits at top level (orchestrator only)**

```bash
# Commit 1: Core CLI UX + tests
git add tools/dm-search.sh tools/dm-player.sh tests/test_dm_search_cli.py tests/test_dm_player_cli.py
git commit -m "fix(cli): harden search/player argument handling"

# Commit 2: Core resilience + tests
git add lib/search.py lib/world_stats.py lib/session_manager.py tests/test_search.py tests/test_world_stats.py tests/test_session_manager.py
git commit -m "fix(core): tolerate malformed world state payloads"

# Commit 3: Advanced module validation + tests
git add .claude/modules/inventory-system/lib/inventory_manager.py .claude/modules/inventory-system/tests/test_inventory_manager.py .claude/modules/firearms-combat/lib/firearms_resolver.py .claude/modules/firearms-combat/tests/test_firearms_resolver.py .claude/modules/world-travel/lib/encounter_engine.py .claude/modules/world-travel/tests/test_encounter_engine.py
git commit -m "fix(modules): validate combat/inventory inputs and time parsing"
```

