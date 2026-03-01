import importlib.util
import itertools
import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_MODULE_COUNTER = itertools.count()


def load_module(relative_path: str):
    module_path = PROJECT_ROOT / relative_path
    module_name = f"feature_fix_module_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_list_spells_empty_result_does_not_raise_indexerror(monkeypatch):
    module = load_module("features/spells/list_spells.py")

    captured = {}

    def fake_fetch(endpoint):
        assert endpoint == "/api/2014/spells"
        return {
            "count": 1,
            "results": [
                {
                    "index": "acid-arrow",
                    "name": "Acid Arrow",
                    "url": "/api/2014/spells/acid-arrow",
                }
            ],
        }

    def fake_output(data):
        captured["data"] = data

    monkeypatch.setattr(module, "fetch", fake_fetch)
    monkeypatch.setattr(module, "output", fake_output)
    monkeypatch.setattr(module.sys, "argv", ["list_spells.py", "--search", "does-not-match"])

    module.main()

    assert captured["data"]["count"] == 0
    assert captured["data"]["results"] == []


def test_monster_filter_fetches_unknown_cr_even_when_many(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_monsters.py")
    args = type("Args", (), {"cr": "2", "search": None})

    monsters = [{"index": f"unknown-{idx}", "name": f"Unknown {idx}"} for idx in range(21)]

    fetch_calls = []

    def fake_fetch(endpoint):
        fetch_calls.append(endpoint)
        return {"challenge_rating": 2}

    monkeypatch.setattr(module, "fetch", fake_fetch)

    results = module.filter_monsters_instant(monsters, args)

    assert len(results) == 21
    assert len(fetch_calls) == 21


def test_monster_cr_table_uses_correct_stirge_value():
    module = load_module("features/dnd-api/monsters/dnd_monsters.py")
    assert module.MONSTER_CR_TABLE["stirge"] == 0.125


def test_save_character_validates_required_stat_keys_before_calculation(tmp_path, monkeypatch):
    module = load_module("features/character-creation/save_character.py")

    class FakeCampaignManager:
        def __init__(self):
            self.campaign_dir = tmp_path / "world-state" / "campaigns" / "test"
            self.campaign_dir.mkdir(parents=True, exist_ok=True)

        def get_active_campaign_dir(self):
            return self.campaign_dir

        def get_active(self):
            return "test"

    monkeypatch.setattr(module, "CampaignManager", FakeCampaignManager)

    result = module.save_character(
        {
            "name": "Rhea",
            "race": "Human",
            "class": "Wizard",
            "level": 1,
            "stats": {"str": 10, "dex": 10, "int": 16, "wis": 12, "cha": 8},
        }
    )

    assert "error" in result
    assert "Missing required stats" in result["error"]


def test_save_character_prevents_non_positive_hp(tmp_path, monkeypatch):
    module = load_module("features/character-creation/save_character.py")

    class FakeCampaignManager:
        def __init__(self):
            self.campaign_dir = tmp_path / "world-state" / "campaigns" / "test"
            self.campaign_dir.mkdir(parents=True, exist_ok=True)

        def get_active_campaign_dir(self):
            return self.campaign_dir

        def get_active(self):
            return "test"

    monkeypatch.setattr(module, "CampaignManager", FakeCampaignManager)

    result = module.save_character(
        {
            "name": "Nix",
            "race": "Elf",
            "class": "Wizard",
            "level": 1,
            "stats": {"str": 8, "dex": 12, "con": -2, "int": 16, "wis": 10, "cha": 10},
        }
    )

    assert result["success"] is True
    assert result["character"]["hp"]["max"] == 1
    assert result["character"]["hp"]["current"] == 1


def test_dnd_monster_main_normalizes_apostrophes_and_punctuation(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_monster.py")

    endpoints = []

    def fake_fetch(endpoint):
        endpoints.append(endpoint)
        return {"name": "Any"}

    monkeypatch.setattr(module, "fetch", fake_fetch)
    monkeypatch.setattr(module, "output", lambda _: None)
    monkeypatch.setattr(module.sys, "argv", ["dnd_monster.py", "Mummy's Revenge!!"])

    module.main()

    assert endpoints[0] == "/monsters/mummys-revenge"


def test_dnd_equipment_main_normalizes_apostrophes_and_punctuation(monkeypatch):
    module = load_module("features/gear/dnd_equipment.py")

    endpoints = []

    def fake_fetch(endpoint):
        endpoints.append(endpoint)
        return {"name": "Any"}

    monkeypatch.setattr(module, "fetch", fake_fetch)
    monkeypatch.setattr(module, "output", lambda _: None)
    monkeypatch.setattr(module.sys, "argv", ["dnd_equipment.py", "Traveler's Clothes (Fine)"])

    module.main()

    assert endpoints[0] == "/equipment/travelers-clothes-fine"


def test_skills_list_uses_skill_details_to_group_by_ability(monkeypatch):
    module = load_module("features/rules/skills.py")

    def fake_fetch(endpoint):
        if endpoint == "/skills":
            return {
                "count": 2,
                "results": [
                    {"index": "stealth", "name": "Stealth"},
                    {"index": "arcana", "name": "Arcana"},
                ],
            }
        if endpoint == "/skills/stealth":
            return {"ability_score": {"name": "Dexterity"}}
        if endpoint == "/skills/arcana":
            return {"ability_score": {"name": "Intelligence"}}
        raise AssertionError(f"Unexpected endpoint: {endpoint}")

    monkeypatch.setattr(module, "fetch", fake_fetch)

    result = module.list_all_skills()

    assert "Dexterity" in result["skills_by_ability"]
    assert "Intelligence" in result["skills_by_ability"]
    assert result["skills_by_ability"]["Dexterity"][0]["index"] == "stealth"
    assert result["skills_by_ability"]["Intelligence"][0]["index"] == "arcana"


def test_get_rule_subsection_fetches_subsection_content(monkeypatch):
    module = load_module("features/rules/get_rule.py")

    calls = []
    captured = {}

    def fake_fetch(endpoint):
        calls.append(endpoint)
        if endpoint == "/rules/advantage":
            return {
                "name": "Advantage",
                "desc": "Roll two d20 and keep the higher result.",
                "subsections": [
                    {"name": "Special Cases", "url": "/api/2014/rule-sections/special-cases"}
                ],
            }
        if endpoint == "/rule-sections/special-cases":
            return {"name": "Special Cases", "desc": ["Special details."]}
        raise AssertionError(f"Unexpected endpoint: {endpoint}")

    def fake_output(data):
        captured["data"] = data

    monkeypatch.setattr(module, "fetch", fake_fetch)
    monkeypatch.setattr(module, "output", fake_output)
    monkeypatch.setattr(module, "error_output", lambda message: (_ for _ in ()).throw(RuntimeError(message)))
    monkeypatch.setattr(
        module.sys,
        "argv",
        ["get_rule.py", "advantage", "--subsection", "special cases"],
    )

    module.main()

    assert calls == ["/rules/advantage", "/rule-sections/special-cases"]
    assert captured["data"]["subsection"]["name"] == "Special Cases"


def test_monsters_api_filter_count_matches_limited_results(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_monsters_api_filter.py")

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    payload = (
        b'{"count": 4, "results": [{"name": "A", "url": "/api/2014/monsters/a"}, '
        b'{"name": "B", "url": "/api/2014/monsters/b"}, '
        b'{"name": "C", "url": "/api/2014/monsters/c"}]}'
    )

    class DummyOpener:
        def open(self, _request, timeout=None):
            return DummyResponse(payload)

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("urlopen should not be called")),
    )
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda: DummyOpener())

    result = module.fetch_monsters(limit=2)

    assert len(result["results"]) == 2
    assert result["count"] == 2


def test_save_character_legacy_id_stays_within_characters_directory(tmp_path, monkeypatch):
    module = load_module("features/character-creation/save_character.py")

    class FakeCampaignManager:
        def get_active_campaign_dir(self):
            return tmp_path / "unused"

        def get_active(self):
            return None

    monkeypatch.setattr(module, "CampaignManager", FakeCampaignManager)
    monkeypatch.chdir(tmp_path)

    result = module.save_character(
        {
            "name": "../Outside",
            "race": "Human",
            "class": "Fighter",
            "level": 1,
            "stats": {"str": 12, "dex": 12, "con": 12, "int": 10, "wis": 10, "cha": 10},
        }
    )

    assert result["success"] is True
    file_path = Path(result["file_path"]).resolve()
    characters_dir = (tmp_path / "world-state" / "characters").resolve()
    assert file_path.parent == characters_dir
    assert ".." not in result["character_id"]
    assert "/" not in result["character_id"]
    assert "\\" not in result["character_id"]


def test_save_character_rejects_non_numeric_stats_cleanly():
    module = load_module("features/character-creation/save_character.py")

    result = module.save_character(
        {
            "name": "Iria",
            "race": "Elf",
            "class": "Wizard",
            "level": 1,
            "stats": {"str": 8, "dex": 14, "con": "high", "int": 16, "wis": 12, "cha": 10},
        }
    )

    assert "error" in result
    assert result["error"] == "Invalid stat value for 'con': expected a number"


@pytest.mark.parametrize(
    "module_path",
    [
        "features/dnd-api/dnd_api_core.py",
        "features/rules/rules_api_core.py",
        "features/spells/spell_api_core.py",
        "features/character-creation/character_creation_core.py",
    ],
)
def test_api_core_fetch_uses_timeout(module_path, monkeypatch):
    module = load_module(module_path)

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
    module.fetch("/test-endpoint")

    assert calls
    assert calls[0]["timeout"] == 10


def test_encounter_v2_rejects_negative_count_before_fetch(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_encounter_v2.py")

    def fake_error_output(message):
        raise RuntimeError(message)

    monkeypatch.setattr(module, "get_monsters_by_cr", lambda _cr: (_ for _ in ()).throw(AssertionError("must not fetch")))
    monkeypatch.setattr(module, "error_output", fake_error_output)
    monkeypatch.setattr(module.sys, "argv", ["dnd_encounter_v2.py", "--cr", "1", "--count", "-2"])

    with pytest.raises(RuntimeError, match="--count must be 0 or greater"):
        module.main()


def test_encounter_v2_quick_mode_outputs_human_names(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_encounter_v2.py")

    captured = {}

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    payload = json.dumps(
        {
            "results": [
                {"name": "Wolf", "url": "/api/2014/monsters/wolf"},
                {"name": "Bear", "url": "/api/2014/monsters/black-bear"},
            ]
        }
    ).encode("utf-8")

    class DummyOpener:
        def open(self, _request, timeout=None):
            return DummyResponse(payload)

    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("urlopen should not be called")),
    )
    monkeypatch.setattr(module.urllib.request, "build_opener", lambda: DummyOpener())
    monkeypatch.setattr(module.random, "sample", lambda items, count: items[:count])
    monkeypatch.setattr(module, "output", lambda data: captured.setdefault("data", data))
    monkeypatch.setattr(module.sys, "argv", ["dnd_encounter_v2.py", "--cr", "1", "--count", "2", "--quick"])

    module.main()

    assert captured["data"]["monsters"] == ["Wolf", "Bear"]


@pytest.mark.parametrize(
    ("trait_url", "expected_endpoint"),
    [
        ("http://www.dnd5eapi.co/api/2014/traits/darkvision", "/traits/darkvision"),
        ("https://www.dnd5eapi.co/api/2014/traits/darkvision", "/traits/darkvision"),
        ("https://www.dnd5eapi.co/traits/darkvision", "/traits/darkvision"),
        ("/api/2014/traits/darkvision", "/traits/darkvision"),
        ("traits/darkvision", "/traits/darkvision"),
    ],
)
def test_get_traits_normalizes_absolute_and_relative_urls(trait_url, expected_endpoint, monkeypatch):
    module = load_module("features/character-creation/api/get_traits.py")

    endpoints = []

    def fake_fetch(endpoint):
        endpoints.append(endpoint)
        return {"name": "Darkvision", "desc": [], "proficiencies": []}

    monkeypatch.setattr(module, "fetch", fake_fetch)

    result = module.get_trait_details(trait_url)

    assert result["name"] == "Darkvision"
    assert endpoints == [expected_endpoint]


def test_list_spells_rejects_negative_limit(monkeypatch):
    module = load_module("features/spells/list_spells.py")

    def fake_error_output(message):
        raise RuntimeError(message)

    monkeypatch.setattr(module, "fetch", lambda _endpoint: (_ for _ in ()).throw(AssertionError("must not fetch")))
    monkeypatch.setattr(module, "error_output", fake_error_output)
    monkeypatch.setattr(module.sys, "argv", ["list_spells.py", "--limit", "-1"])

    with pytest.raises(RuntimeError, match="--limit must be 0 or greater"):
        module.main()


def test_list_spells_honors_zero_limit(monkeypatch):
    module = load_module("features/spells/list_spells.py")
    captured = {}

    def fake_fetch(endpoint):
        assert endpoint == "/api/2014/spells"
        return {
            "count": 2,
            "results": [
                {"index": "fire-bolt", "name": "Fire Bolt", "url": "/api/2014/spells/fire-bolt"},
                {"index": "mage-hand", "name": "Mage Hand", "url": "/api/2014/spells/mage-hand"},
            ],
        }

    monkeypatch.setattr(module, "fetch", fake_fetch)
    monkeypatch.setattr(module, "output", lambda payload: captured.setdefault("payload", payload))
    monkeypatch.setattr(module.sys, "argv", ["list_spells.py", "--limit", "0"])

    module.main()

    assert captured["payload"]["count"] == 0
    assert captured["payload"]["total"] == 2
    assert captured["payload"]["results"] == []


def test_get_spell_main_normalizes_smart_quotes_in_lookup(monkeypatch):
    module = load_module("features/spells/get_spell.py")

    endpoints = []

    def fake_fetch(endpoint):
        endpoints.append(endpoint)
        return {"name": "Any"}

    monkeypatch.setattr(module, "fetch", fake_fetch)
    monkeypatch.setattr(module, "output", lambda _data: None)
    monkeypatch.setattr(module.sys, "argv", ["get_spell.py", "Melf’s Acid Arrow"])

    module.main()

    assert endpoints[0] == "/api/2014/spells/melfs-acid-arrow"


def test_dnd_magic_item_main_normalizes_smart_quotes_in_lookup(monkeypatch):
    module = load_module("features/gear/dnd_magic_item.py")

    endpoints = []

    def fake_fetch(endpoint):
        endpoints.append(endpoint)
        return {"name": "Any"}

    monkeypatch.setattr(module, "fetch", fake_fetch)
    monkeypatch.setattr(module, "output", lambda _data: None)
    monkeypatch.setattr(module.sys, "argv", ["dnd_magic_item.py", "Dragon’s Wrath Weapon"])

    module.main()

    assert endpoints[0] == "/magic-items/dragons-wrath-weapon"


def test_filter_spells_applies_search_before_fetching_details(monkeypatch):
    module = load_module("features/spells/list_spells.py")

    details_calls = []

    def fake_fetch_spell_details(spell_index):
        details_calls.append(spell_index)
        return {"level": 0, "school": {"name": "Evocation", "index": "evocation"}}

    monkeypatch.setattr(module, "fetch_spell_details", fake_fetch_spell_details)

    args = type(
        "Args",
        (),
        {
            "search": "fire",
            "level": 0,
            "school": None,
            "spell_class": None,
            "ritual": False,
            "concentration": False,
        },
    )()
    spells = [
        {"index": "fire-bolt", "name": "Fire Bolt", "url": "/api/2014/spells/fire-bolt"},
        {"index": "mage-hand", "name": "Mage Hand", "url": "/api/2014/spells/mage-hand"},
    ]

    filtered = module.filter_spells(spells, args)

    assert details_calls == ["fire-bolt"]
    assert filtered[0]["name"] == "Fire Bolt"


@pytest.mark.parametrize("bad_level", [True, False, 0, -1, 1.5, "2", None])
def test_save_character_rejects_invalid_level_values(bad_level):
    module = load_module("features/character-creation/save_character.py")

    result = module.save_character(
        {
            "name": "Tess",
            "race": "Human",
            "class": "Fighter",
            "level": bad_level,
            "stats": {"str": 14, "dex": 12, "con": 13, "int": 10, "wis": 10, "cha": 8},
        }
    )

    assert "error" in result
    assert "level" in result["error"].lower()


def test_save_character_rejects_invalid_required_field_type():
    module = load_module("features/character-creation/save_character.py")

    result = module.save_character(
        {
            "name": None,
            "race": "Human",
            "class": "Fighter",
            "level": 1,
            "stats": {"str": 14, "dex": 12, "con": 13, "int": 10, "wis": 10, "cha": 8},
        }
    )

    assert "error" in result
    assert result["error"] == "Field 'name' must be a non-empty string"


def test_get_class_details_preserves_all_proficiency_choice_groups():
    module = load_module("features/character-creation/api/get_class_details.py")

    details = module.extract_class_details(
        {
            "name": "Fighter",
            "proficiency_choices": [
                {
                    "choose": 2,
                    "from": {
                        "options": [
                            {"item": {"name": "Skill: Acrobatics"}},
                            {"item": {"name": "Skill: Animal Handling"}},
                        ]
                    },
                },
                {
                    "choose": 1,
                    "from": {"options": [{"item": {"name": "Skill: Insight"}}]},
                },
            ],
        }
    )

    assert details["skill_choices"]["groups"] == [
        {"choose": 2, "from": ["Skill: Acrobatics", "Skill: Animal Handling"]},
        {"choose": 1, "from": ["Skill: Insight"]},
    ]


def test_dnd_monsters_cr_table_has_correct_red_dragon_wyrmling_cr():
    module = load_module("features/dnd-api/monsters/dnd_monsters.py")
    assert module.MONSTER_CR_TABLE["red-dragon-wyrmling"] == 4


def test_dnd_monsters_fractional_cr_range_parsing():
    module = load_module("features/dnd-api/monsters/dnd_monsters.py")

    assert module.parse_cr_range("1/2") == (0.5, 0.5)
    assert module.parse_cr_range("1/8-1/4") == (0.125, 0.25)


def test_dnd_monsters_filtered_total_reflects_matches_before_limit(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_monsters.py")
    captured = {}

    def fake_fetch(endpoint):
        assert endpoint == "/monsters"
        return {
            "count": 3,
            "results": [
                {"index": "red-dragon-wyrmling", "name": "Red Dragon Wyrmling"},
                {"index": "blue-dragon-wyrmling", "name": "Blue Dragon Wyrmling"},
                {"index": "goblin", "name": "Goblin"},
            ],
        }

    monkeypatch.setattr(module, "fetch", fake_fetch)
    monkeypatch.setattr(module, "output", lambda payload: captured.setdefault("payload", payload))
    monkeypatch.setattr(module.sys, "argv", ["dnd_monsters.py", "--search", "dragon", "--limit", "1"])

    module.main()

    assert captured["payload"]["count"] == 1
    assert captured["payload"]["total"] == 2


def test_encounter_v2_accepts_fractional_cr_cli(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_encounter_v2.py")
    captured = {}

    def fake_get_monsters_by_cr(cr):
        captured["cr"] = cr
        return [{"index": "wolf", "name": "Wolf"}]

    monkeypatch.setattr(module, "get_monsters_by_cr", fake_get_monsters_by_cr)
    monkeypatch.setattr(module.random, "sample", lambda items, count: items[:count])
    monkeypatch.setattr(module, "output", lambda payload: captured.setdefault("payload", payload))
    monkeypatch.setattr(module.sys, "argv", ["dnd_encounter_v2.py", "--cr", "1/2", "--count", "1", "--quick"])

    module.main()

    assert captured["cr"] == 0.5
    assert captured["payload"]["cr"] == 0.5


def test_monsters_api_filter_accepts_fractional_cr_cli(monkeypatch):
    module = load_module("features/dnd-api/monsters/dnd_monsters_api_filter.py")
    captured = {}

    def fake_fetch_monsters(challenge_ratings=None, limit=None, search=None):
        captured["challenge_ratings"] = challenge_ratings
        captured["limit"] = limit
        captured["search"] = search
        return {"count": 0, "results": []}

    monkeypatch.setattr(module, "fetch_monsters", fake_fetch_monsters)
    monkeypatch.setattr(module.sys, "argv", ["dnd_monsters_api_filter.py", "--cr", "1/4", "--json"])

    module.main()

    assert captured["challenge_ratings"] == [0.25]


@pytest.mark.parametrize(
    ("module_path", "argv"),
    [
        ("features/rules/list_rules.py", ["list_rules.py", "--limit", "-1"]),
        ("features/dnd-api/monsters/dnd_monsters.py", ["dnd_monsters.py", "--limit", "-1"]),
        ("features/gear/dnd_equipment_list.py", ["dnd_equipment_list.py", "--limit", "-1"]),
    ],
)
def test_cli_tools_reject_negative_limit_before_fetch(module_path, argv, monkeypatch):
    module = load_module(module_path)

    monkeypatch.setattr(module, "fetch", lambda _endpoint: (_ for _ in ()).throw(AssertionError("must not fetch")))
    monkeypatch.setattr(module, "error_output", lambda message: (_ for _ in ()).throw(RuntimeError(message)))
    monkeypatch.setattr(module.sys, "argv", argv)

    with pytest.raises(RuntimeError, match="--limit must be 0 or greater"):
        module.main()


def test_monsters_api_filter_rejects_negative_limit_before_fetch(monkeypatch, capsys):
    module = load_module("features/dnd-api/monsters/dnd_monsters_api_filter.py")

    monkeypatch.setattr(
        module, "fetch_monsters", lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not fetch"))
    )
    monkeypatch.setattr(module.sys, "argv", ["dnd_monsters_api_filter.py", "--limit", "-1"])

    with pytest.raises(SystemExit) as exc:
        module.main()

    stderr = capsys.readouterr().err
    assert exc.value.code == 1
    assert "--limit must be 0 or greater" in stderr


def test_combat_rules_death_saves_text_uses_death_saving_throw_not_con_save():
    module = load_module("features/rules/combat_rules.py")

    death_saves_text = module.COMBAT_TOPICS["death"]["content"]["Death Saves"]
    assert "DC 10" in death_saves_text
    assert "death saving throw" in death_saves_text.lower()
    assert "con save" not in death_saves_text.lower()
