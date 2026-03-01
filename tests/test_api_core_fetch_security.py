import importlib.util
import itertools
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_MODULE_COUNTER = itertools.count()


def load_module(relative_path: str):
    module_path = PROJECT_ROOT / relative_path
    module_name = f"api_core_security_module_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


API_CORE_MODULES = [
    "features/dnd-api/dnd_api_core.py",
    "features/rules/rules_api_core.py",
    "features/spells/spell_api_core.py",
    "features/character-creation/character_creation_core.py",
]


@pytest.mark.parametrize("module_path", API_CORE_MODULES)
def test_fetch_rejects_non_http_base_url(module_path, monkeypatch):
    module = load_module(module_path)
    monkeypatch.setattr(module, "BASE_URL", "file:///tmp/not-allowed")

    calls = []

    class DummyResponse:
        def read(self):
            return b"{}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyOpener:
        def open(self, request, timeout=None):
            calls.append({"url": request.full_url, "timeout": timeout})
            return DummyResponse()

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("urlopen should not be called")),
    )
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda: DummyOpener())

    result = module.fetch("/classes")

    assert result["error"] == "Request failed"
    assert "http" in result["message"].lower()
    assert "https" in result["message"].lower()
    assert calls == []


@pytest.mark.parametrize("module_path", API_CORE_MODULES)
def test_fetch_preserves_timeout_behavior(module_path, monkeypatch):
    module = load_module(module_path)
    monkeypatch.setattr(module, "REQUEST_TIMEOUT", 37)

    calls = []

    class DummyResponse:
        def read(self):
            return b'{"ok": true}'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyOpener:
        def open(self, request, timeout=None):
            calls.append({"url": request.full_url, "timeout": timeout})
            return DummyResponse()

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("urlopen should not be called")),
    )
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda: DummyOpener())

    result = module.fetch("/classes")

    assert result == {"ok": True}
    assert calls
    assert calls[0]["timeout"] == 37
