import json

from lib.json_ops import JsonOperations


def test_save_json_rejects_parent_traversal(tmp_path):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir(parents=True)
    ops = JsonOperations(str(campaign_dir))

    ok = ops.save_json("../escaped.json", {"ok": True})

    assert ok is False
    assert (tmp_path / "escaped.json").exists() is False


def test_load_json_rejects_parent_traversal(tmp_path):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir(parents=True)
    (tmp_path / "escaped.json").write_text(json.dumps({"bad": True}), encoding="utf-8")
    ops = JsonOperations(str(campaign_dir))

    value = ops.load_json("../escaped.json", default={"safe": True})

    assert value == {"safe": True}


def test_save_json_allows_absolute_path_within_campaign_root(tmp_path):
    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir(parents=True)
    ops = JsonOperations(str(campaign_dir))
    inside_path = campaign_dir / "nested" / "state.json"
    inside_path.parent.mkdir(parents=True)

    ok = ops.save_json(str(inside_path), {"ok": True})

    assert ok is True
    assert inside_path.exists() is True
