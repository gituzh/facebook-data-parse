#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DATETIME_FORMAT = "%Y%m%d_%H%M%S"
DEFAULT_MAPPING_PATH = Path(__file__).with_name("posts.mapping.json")


def to_utc(ts: Optional[float]) -> Optional[str]:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(DATETIME_FORMAT)
    except Exception:
        return None


def fix_string(value: str) -> str:
    try:
        decoded = value.encode("latin1").decode("utf-8")
    except Exception:
        decoded = value
    return decoded.replace("\u2028", "\n").replace("\u2029", "\n")


def fix_mojibake(obj: Any) -> Any:
    if isinstance(obj, str):
        return fix_string(obj)
    if isinstance(obj, list):
        return [fix_mojibake(item) for item in obj]
    if isinstance(obj, dict):
        return {key: fix_mojibake(value) for key, value in obj.items()}
    return obj


def resolve_path(obj: Any, path: Any) -> List[Any]:
    if path is None:
        return []
    if isinstance(path, list):
        for candidate in path:
            values = resolve_path(obj, candidate)
            if any(v not in (None, "", [], {}) for v in values):
                return values
        return []

    parts = str(path).split(".")
    items = [obj]
    for part in parts:
        next_items: List[Any] = []
        is_list = part.endswith("[]")
        key = part[:-2] if is_list else part
        for item in items:
            if isinstance(item, dict) and key in item:
                value = item.get(key)
            else:
                value = None
            if is_list:
                if isinstance(value, list):
                    next_items.extend(value)
            else:
                if value is not None:
                    next_items.append(value)
        items = next_items
    return items


def get_transform(name: str):
    registry = {
        "decode": fix_string,
    }
    if name in registry:
        return registry[name]
    candidate = globals().get(name)
    if callable(candidate):
        return candidate
    raise ValueError(f"Unknown transform: {name}")


def apply_transforms(values: List[Any], transform: Any) -> List[Any]:
    if transform is None:
        return values
    if isinstance(transform, list):
        steps = transform
    else:
        steps = [transform]

    current = values
    for step in steps:
        func = get_transform(step)
        current = [func(v) for v in current]
    return current


def set_nested(obj: Dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    current = obj
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def extract_field(obj: Dict[str, Any], spec: Dict[str, Any]) -> Any:
    values = resolve_path(obj, spec.get("path"))
    values = apply_transforms(values, spec.get("transform"))
    if spec.get("first"):
        for value in values:
            if value not in (None, "", [], {}):
                return value
        return "" if values else ""
    if spec.get("collapse_single", True) and len(values) == 1:
        return values[0]
    return values


def process_each(obj: Dict[str, Any], each_spec: Dict[str, Any]) -> List[Any]:
    cases = each_spec.get("cases", [])
    output: List[Any] = []
    for case in cases:
        when_values = resolve_path(obj, case.get("when"))
        if not any(v not in (None, "", [], {}) for v in when_values):
            continue
        emit_spec = case.get("emit", {})
        emitted: Dict[str, Any] = {}
        for key, spec in emit_spec.items():
            value = extract_field(obj, spec)
            if isinstance(value, list) and spec.get("first"):
                value = value[0] if value else ""
            set_nested(emitted, key, value)
        if emitted:
            output.append(emitted)
    return output


def process_item(item: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for field, spec in mapping.get("fields", {}).items():
        if "each" in spec:
            items = resolve_path(item, spec.get("path"))
            collected: List[Any] = []
            for entry in items:
                if isinstance(entry, dict):
                    collected.extend(process_each(entry, spec.get("each", {})))
            result[field] = collected
        else:
            value = extract_field(item, spec)
            if isinstance(value, list) and spec.get("first"):
                value = value[0] if value else ""
            result[field] = value
    return fix_mojibake(result)


def collapse_single_branches(obj: Any) -> Any:
    if isinstance(obj, list):
        if len(obj) == 1:
            return collapse_single_branches(obj[0])
        return [collapse_single_branches(item) for item in obj]
    if isinstance(obj, dict):
        return {key: collapse_single_branches(value) for key, value in obj.items()}
    return obj


def flatten_dicts(obj: Any, prefix: str = "") -> Any:
    if isinstance(obj, list):
        return [flatten_dicts(item, prefix="") for item in obj]
    if not isinstance(obj, dict):
        return obj

    flattened: Dict[str, Any] = {}
    for key, value in obj.items():
        dotted_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            nested = flatten_dicts(value, dotted_key)
            if isinstance(nested, dict):
                flattened.update(nested)
            else:
                flattened[dotted_key] = nested
        elif isinstance(value, list):
            flattened[dotted_key] = [flatten_dicts(item, "") for item in value]
        else:
            flattened[dotted_key] = value
    return flattened


def process_posts(data: List[Dict[str, Any]], mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    processed: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        processed.append(process_item(item, mapping))
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process Facebook posts JSON into a simplified, decoded format."
    )
    parser.add_argument(
        "--mapping",
        default=str(DEFAULT_MAPPING_PATH),
        help="Path to mapping JSON file",
    )
    parser.add_argument(
        "input",
        help="Path to profile_posts_*.json file",
    )
    parser.add_argument(
        "--output-dir",
        default="data/output",
        help="Directory to write the processed file (default: data/output)",
    )
    parser.add_argument(
        "--sort-field",
        default="timestamp",
        help="Processed field name to sort by (default: timestamp)",
    )
    parser.add_argument(
        "--sort-order",
        choices=["asc", "desc"],
        default="asc",
        help="Sort order for --sort-field (default: asc)",
    )
    parser.add_argument(
        "--collapse-single-branches",
        action="store_true",
        help="Collapse single-item lists all the way down",
    )
    parser.add_argument(
        "--flatten-dicts",
        action="store_true",
        help="Flatten dicts into dotted keys (global)",
    )
    args = parser.parse_args()

    mapping_path = Path(args.mapping)
    if not mapping_path.exists():
        raise SystemExit(f"Mapping file not found: {mapping_path}")
    with mapping_path.open("r", encoding="utf-8") as f:
        mapping = json.load(f)

    src = Path(args.input)
    with src.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SystemExit("Input JSON must be a list of posts.")

    timestamps = [item.get("timestamp") for item in data if isinstance(item, dict)]
    timestamps = [ts for ts in timestamps if isinstance(ts, (int, float))]

    if timestamps:
        start = to_utc(min(timestamps)) or "unknown"
        end = to_utc(max(timestamps)) or "unknown"
    else:
        start = "unknown"
        end = "unknown"

    output_name = f"posts_{start}_{end}.json"
    output_path = Path(args.output_dir) / output_name

    processed = process_posts(data, mapping)
    if args.collapse_single_branches:
        processed = [collapse_single_branches(item) for item in processed]
    if args.flatten_dicts:
        processed = [flatten_dicts(item) for item in processed]
    if args.sort_field:
        sort_key = args.sort_field
        processed.sort(
            key=lambda item: (item.get(sort_key) is None, item.get(sort_key)),
            reverse=args.sort_order == "desc",
        )
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    print(str(output_path))


if __name__ == "__main__":
    main()
