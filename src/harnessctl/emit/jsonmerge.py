from typing import Any, Dict
import json
import json5


def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merges source dict into target dict.
    Returns the updated target dict.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # Get node or create one
            node = target.setdefault(key, {})
            if isinstance(node, dict):
                deep_merge(node, value)
            else:
                # If target is not a dict, overwrite it
                target[key] = value
        else:
            target[key] = value
    return target


def merge_json_content(original_content: str, managed_data: Dict[str, Any]) -> str:
    """
    Parses original JSONC/JSON, deep merges managed_data into it,
    and returns the formatted JSON string.
    """
    if not original_content.strip():
        data = {}
    else:
        try:
            data = json5.loads(original_content)
        except Exception:
            # Fallback to standard json if json5 fails for some reason
            try:
                data = json.loads(original_content)
            except Exception:
                # If completely invalid, just overwrite it
                data = {}

    if not isinstance(data, dict):
        data = {}

    merged = deep_merge(data, managed_data)
    # Output standard JSON (comments are not preserved, but keys are)
    return json.dumps(merged, indent=2) + "\n"
