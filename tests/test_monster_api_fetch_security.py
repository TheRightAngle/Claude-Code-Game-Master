import importlib.util
import itertools
import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_MODULE_COUNTER = itertools.count()


def load_module(relative_path: str):
    module_path = PROJECT_ROOT / relative_path
    module_name = f"monster_api_security_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_encounter_v2_get_monsters_by_cr_propagates_timeout(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_encounter_v2.py")

    calls = []

    class DummyResponse:
        def __init__(self, payload: bytes):
            self._payload = payload

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    payload = json.dumps({"results": []}).encode("utf-8")

    class DummyOpener:
        def open(self, request, timeout=None):
            calls.append({"url": request.full_url, "timeout": timeout})
            return DummyResponse(payload)

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("urlopen should not be called")),
    )
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda: DummyOpener())

    module.get_monsters_by_cr(1)

    assert calls
    assert calls[0]["timeout"] == 10


def test_encounter_v2_get_monsters_by_cr_rejects_non_http_base_url(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_encounter_v2.py")
    monkeypatch.setattr(module, "BASE_URL", "file:///tmp")

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("urlopen should not be called")),
    )
    monkeypatch.setattr(
        module.urllib.request,
        "build_opener",
        lambda: (_ for _ in ()).throw(AssertionError("build_opener should not be called")),
    )
    monkeypatch.setattr(module, "error_output", lambda message: (_ for _ in ()).throw(RuntimeError(message)))

    with pytest.raises(RuntimeError, match="Invalid BASE_URL scheme"):
        module.get_monsters_by_cr(1)


def test_monsters_api_filter_fetch_monsters_propagates_timeout(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_monsters_api_filter.py")

    calls = []

    class DummyResponse:
        def __init__(self, payload: bytes):
            self._payload = payload

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    payload = json.dumps({"results": []}).encode("utf-8")

    class DummyOpener:
        def open(self, request, timeout=None):
            calls.append({"url": request.full_url, "timeout": timeout})
            return DummyResponse(payload)

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("urlopen should not be called")),
    )
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda: DummyOpener())

    module.fetch_monsters()

    assert calls
    assert calls[0]["timeout"] == 10


def test_monsters_api_filter_fetch_monsters_rejects_non_http_base_url(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_monsters_api_filter.py")
    monkeypatch.setattr(module, "BASE_URL", "ftp://example.com")

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("urlopen should not be called")),
    )
    monkeypatch.setattr(
        module.urllib.request,
        "build_opener",
        lambda: (_ for _ in ()).throw(AssertionError("build_opener should not be called")),
    )

    result = module.fetch_monsters()

    assert "error" in result
    assert "Invalid BASE_URL scheme" in result["error"]
