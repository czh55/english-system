#!/usr/bin/env python3
"""Validate english-system content JSON against lightweight schema rules."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"

MODULE_RULES = {
    "entity": {
        "id_prefix": "ent-",
        "required": ["id", "module", "lemma", "zh", "type"],
        "module": "entity",
        "types": {"person", "place", "object", "other"},
    },
    "function": {
        "id_prefix": "fn-",
        "required": ["id", "module", "lemma", "zh", "tags"],
        "module": "function",
        "tags": {
            "connect",
            "modal",
            "degree",
            "time",
            "filler",
            "verb",
            "adj",
            "noun",
            "phrasal",
            "priority",
        },
    },
    "phrases": {
        "id_prefix": "ph-",
        "required": ["id", "module", "frame_en", "frame_zh", "group"],
        "module": "phrases",
    },
    "scenarios": {
        "id_prefix": "sc-",
        "required": ["id", "module", "slug", "title", "scenes"],
        "module": "scenarios",
    },
}


def fail(path: Path, msg: str, errors: list[str]) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {msg}")


def validate_entry(path: Path, module: str, data: dict, errors: list[str]) -> None:
    rules = MODULE_RULES[module]
    if data.get("module") != rules["module"]:
        fail(path, f"module must be {rules['module']!r}", errors)
    eid = data.get("id", "")
    if not isinstance(eid, str) or not eid.startswith(rules["id_prefix"]):
        fail(path, f"id must start with {rules['id_prefix']!r}", errors)
    for key in rules["required"]:
        if key not in data or data[key] in (None, "", []):
            fail(path, f"missing required field {key!r}", errors)
    if module == "entity" and data.get("type") not in rules["types"]:
        fail(path, f"invalid type {data.get('type')!r}", errors)
    if module == "function":
        tags = data.get("tags") or []
        if not isinstance(tags, list) or not tags:
            fail(path, "tags must be non-empty list", errors)
        else:
            bad = set(tags) - rules["tags"]
            if bad:
                fail(path, f"unknown tags {sorted(bad)}", errors)
    if module == "scenarios":
        scenes = data.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            fail(path, "scenes must be non-empty list", errors)
        else:
            for i, sc in enumerate(scenes):
                if not sc.get("id") or not sc.get("title_cn") or not sc.get("sentences"):
                    fail(path, f"scenes[{i}] incomplete", errors)
    examples = data.get("examples")
    if examples is not None:
        if not isinstance(examples, list):
            fail(path, "examples must be list", errors)
        else:
            for i, ex in enumerate(examples):
                if not isinstance(ex, dict) or "en" not in ex:
                    fail(path, f"examples[{i}] needs en", errors)


def main() -> int:
    errors: list[str] = []
    counts: dict[str, int] = {}
    for module in MODULE_RULES:
        folder = CONTENT / module
        if not folder.is_dir():
            fail(folder, "directory missing", errors)
            continue
        files = sorted(folder.glob("*.json"))
        counts[module] = len(files)
        if not files:
            fail(folder, "no JSON files (empty module)", errors)
            continue
        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                fail(path, f"invalid JSON: {e}", errors)
                continue
            if not isinstance(data, dict):
                fail(path, "root must be object", errors)
                continue
            validate_entry(path, module, data, errors)

    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK")
    for m, n in counts.items():
        print(f"  {m}: {n} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
