import json
from harnessctl.emit.jsonmerge import deep_merge, merge_json_content


def test_deep_merge():
    target = {"a": 1, "b": {"c": 2}}
    source = {"b": {"d": 3}, "e": 4}
    res = deep_merge(target, source)
    assert res == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}


def test_merge_json_content_with_comments():
    original = """
    {
        // This is a comment
        "user_key": "user_value",
        "mcp": {
            "old_server": {}
        }
    }
    """
    managed = {"mcp": {"new_server": {"command": "test"}}}
    merged = merge_json_content(original, managed)
    data = json.loads(merged)
    assert data["user_key"] == "user_value"
    assert "old_server" in data["mcp"]
    assert data["mcp"]["new_server"]["command"] == "test"


def test_merge_json_content_empty():
    assert json.loads(merge_json_content("", {"a": 1})) == {"a": 1}


def test_merge_json_content_invalid():
    assert json.loads(merge_json_content("invalid", {"a": 1})) == {"a": 1}
