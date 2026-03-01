# Full Repo Security Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate security-significant findings from the full-repo review while preserving existing behavior.

**Architecture:** Centralize outbound API URL validation in each API core module and ensure direct URL call sites use explicit timeout and safe URL construction. Harden subprocess execution in world-travel navigation by resolving the executable path before invocation.

**Tech Stack:** Python 3.11+, pytest, bandit, existing project libs.

---

### Task 1: Harden Core API Fetchers

**Files:**
- Modify: `features/dnd-api/dnd_api_core.py`
- Modify: `features/rules/rules_api_core.py`
- Modify: `features/spells/spell_api_core.py`
- Modify: `features/character-creation/character_creation_core.py`
- Test: `tests/test_feature_api_behavior_fixes.py`

**Step 1: Write failing tests**
- Add tests that ensure fetchers reject non-http(s) base URLs (e.g., `file://`) and keep timeout behavior.

**Step 2: Run targeted tests to verify failure**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -k "api_core_fetch" -q`

**Step 3: Write minimal implementation**
- Add URL parsing/validation helper in each core file.
- Keep existing JSON output/error structure.
- Preserve timeout semantics.

**Step 4: Run targeted tests to verify pass**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -k "api_core_fetch" -q`

### Task 2: Harden Direct Monster API Calls

**Files:**
- Modify: `features/dnd-api/monsters/dnd_encounter_v2.py`
- Modify: `features/dnd-api/monsters/dnd_monsters_api_filter.py`
- Test: `tests/test_feature_api_behavior_fixes.py`

**Step 1: Write failing tests**
- Add tests that ensure helper functions pass timeout and reject non-http(s) base URL overrides.

**Step 2: Run targeted tests to verify failure**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -k "encounter_v2 or monsters_api_filter" -q`

**Step 3: Write minimal implementation**
- Validate base URL scheme and normalize endpoint URL handling.
- Use explicit timeout on urlopen calls.

**Step 4: Run targeted tests to verify pass**
- Run: `uv run pytest tests/test_feature_api_behavior_fixes.py -k "encounter_v2 or monsters_api_filter" -q`

### Task 3: Harden World-Travel Subprocess Invocation

**Files:**
- Modify: `.claude/modules/world-travel/lib/navigation_manager.py`
- Test: add/modify module tests if available and practical

**Step 1: Write failing test (if feasible)**
- Add a test for missing shell executable resolution behavior or extract helper to make testable.

**Step 2: Run targeted tests to verify failure**
- Run relevant module test file.

**Step 3: Write minimal implementation**
- Resolve `bash` via `shutil.which` before run; fail gracefully when missing.
- Keep `shell=False` list-arg subprocess invocation.

**Step 4: Run targeted tests to verify pass**
- Run relevant module test file.

### Task 4: Repository Verification

**Files:**
- No code changes required

**Step 1: Run integration verification at top level**
- Run: `uv run pytest -q`

**Step 2: Re-run security scan**
- Run: `uvx --from bandit bandit -r lib features .claude/modules`

**Step 3: Confirm issue closure**
- Verify B310 removed from previously flagged files.
