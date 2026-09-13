#!/usr/bin/env python3
"""Import / cold-start entity + function + phrases from drama-analysis."""
from __future__ import annotations

import html
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DRAMA = Path(__file__).resolve().parents[2] / "drama-analysis"

TAG_MAP = {
    "connect": "connect",
    "modal": "modal",
    "degree": "degree",
    "time": "time",
    "filler": "filler",
    "verb": "verb",
    "adj": "adj",
    "noun": "noun",
    "phrasal": "phrasal",
    "priority": "priority",
}


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def entry_id(prefix: str, drama_slug: str, lemma: str, zh: str) -> str:
    ascii_part = slugify(lemma) if re.search(r"[a-zA-Z0-9]", lemma) else ""
    if ascii_part:
        return f"{prefix}-{drama_slug}-{ascii_part}"
    # stable id for Chinese-only names
    h = hashlib.sha1(zh.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{drama_slug}-{h}"


def decode(s: str) -> str:
    return html.unescape(s).strip()


def parse_vocab_html(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    # Split by section so we know category from section id
    sections = re.split(r'<section id="([^"]+)"', text)
    # sections[0]=preamble, then id, body, id, body...
    by_lemma: dict[str, dict] = {}
    i = 1
    while i + 1 < len(sections):
        sec_id = sections[i]
        body = sections[i + 1]
        i += 2
        tag = TAG_MAP.get(sec_id)
        if not tag or sec_id in ("discovery",):
            continue
        # word-row + following ex-row
        pattern = re.compile(
            r'<tr class="word-row"[^>]*data-term="([^"]*)"[^>]*>.*?'
            r'<td class="term-cell">(.*?)</td>\s*'
            r'<td class="zh-cell">(.*?)</td>\s*'
            r'<td class="freq-cell">.*?<b>(\d+)</b>',
            re.S,
        )
        for m in pattern.finditer(body):
            term = decode(re.sub(r"<[^>]+>", "", m.group(2)))
            zh = decode(re.sub(r"<[^>]+>", "", m.group(3)))
            freq = int(m.group(4))
            lemma = term.strip()
            if not lemma:
                continue
            # example immediately after this row if present
            end = m.end()
            ex_m = re.search(
                r'<tr class="ex-row">.*?<span class="ex-en">(.*?)</span>'
                r'<span class="ex-zh">(.*?)</span>',
                body[end : end + 1200],
                re.S,
            )
            examples = []
            if ex_m:
                examples.append(
                    {
                        "en": decode(re.sub(r"<[^>]+>", "", ex_m.group(1))),
                        "zh": decode(re.sub(r"<[^>]+>", "", ex_m.group(2))).strip("「」"),
                        "source": "drama:english-vocab",
                    }
                )
            key = lemma.lower()
            fid = f"fn-{slugify(lemma) or hashlib.sha1(lemma.encode()).hexdigest()[:10]}"
            if key not in by_lemma:
                by_lemma[key] = {
                    "id": fid,
                    "module": "function",
                    "lemma": lemma,
                    "zh": zh,
                    "tags": [tag],
                    "examples": examples,
                    "freq": freq,
                }
            else:
                entry = by_lemma[key]
                if tag not in entry["tags"]:
                    entry["tags"].append(tag)
                entry["freq"] = max(entry["freq"], freq)
                if examples and not entry["examples"]:
                    entry["examples"] = examples
                elif examples:
                    # keep at most 2
                    existing = {(e["en"], e["zh"]) for e in entry["examples"]}
                    for ex in examples:
                        if (ex["en"], ex["zh"]) not in existing and len(entry["examples"]) < 2:
                            entry["examples"].append(ex)
    return list(by_lemma.values())


def parse_phrases_html(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r'<section id="([^"]+)"', text)
    out: list[dict] = []
    seen: set[str] = set()
    i = 1
    while i + 1 < len(sections):
        sec_id = sections[i]
        body = sections[i + 1]
        i += 2
        if not sec_id.startswith("group-"):
            continue
        title_m = re.search(r"<h2>(.*?)</h2>", body)
        group = decode(re.sub(r"<[^>]+>", "", title_m.group(1))) if title_m else sec_id
        # frames table
        for row in re.finditer(
            r'<tr><td class="zh-cell">(.*?)</td><td class="en-cell">(.*?)</td>'
            r'<td class="use-cell">(.*?)</td></tr>',
            body,
            re.S,
        ):
            frame_zh = decode(re.sub(r"<[^>]+>", "", row.group(1)))
            frame_en = decode(re.sub(r"<[^>]+>", "", row.group(2)))
            usage = decode(re.sub(r"<[^>]+>", "", row.group(3)))
            eid = f"ph-{slugify(frame_en)[:48]}"
            if eid in seen:
                eid = f"{eid}-{len(seen)}"
            seen.add(eid)
            examples = []
            # pull up to 2 examples from this section
            for ex in re.finditer(
                r'<div class="example">\s*<div class="en">(.*?)</div>\s*'
                r'<div class="zh">(.*?)</div>(?:\s*<div class="ctx">(.*?)</div>)?',
                body,
                re.S,
            ):
                if len(examples) >= 2:
                    break
                en = decode(re.sub(r"<[^>]+>", "", ex.group(1)))
                zh = decode(re.sub(r"<[^>]+>", "", ex.group(2))).strip("「」")
                ctx = decode(re.sub(r"<[^>]+>", "", ex.group(3))) if ex.group(3) else ""
                examples.append(
                    {
                        "en": en,
                        "zh": zh,
                        "source": f"drama:english-phrases:{sec_id}",
                        **({"ctx": ctx} if ctx else {}),
                    }
                )
            out.append(
                {
                    "id": eid,
                    "module": "phrases",
                    "frame_en": frame_en,
                    "frame_zh": frame_zh,
                    "usage": usage,
                    "group": group,
                    "group_id": sec_id,
                    "examples": examples,
                    "tags": [sec_id],
                }
            )
    return out


def parse_cast_md(path: Path, drama_slug: str) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    # Find first markdown table with 角色
    rows = []
    in_table = False
    for line in text.splitlines():
        if line.strip().startswith("|") and "角色" in line:
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            if re.match(r"\|\s*-+", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 1 and cells[0]:
                rows.append(cells)
    entities = []
    for cells in rows:
        role = cells[0]
        # split aliases in parentheses
        m = re.match(r"([^（(]+)(?:[（(]([^）)]+)[）)])?", role)
        zh_name = (m.group(1) if m else role).strip()
        alias_raw = (m.group(2) if m and m.group(2) else "").strip()
        aliases = [a.strip() for a in re.split(r"[/、,，]", alias_raw) if a.strip()]
        # English-looking aliases become lemma preference
        en_aliases = [a for a in aliases if re.search(r"[A-Za-z]", a)]
        lemma = en_aliases[0] if en_aliases else zh_name
        eid = entry_id("ent", drama_slug, lemma if en_aliases else "", zh_name)
        relation = cells[2] if len(cells) > 2 else ""
        actor = cells[1] if len(cells) > 1 else ""
        # skip empty / separator junk
        if not zh_name or zh_name in ("角色", "—", "-"):
            continue
        entities.append(
            {
                "id": eid,
                "module": "entity",
                "lemma": lemma,
                "zh": zh_name,
                "type": "person",
                "aliases": aliases,
                "drama": drama_slug,
                "examples": [],
                "tags": [t for t in [actor, relation[:40]] if t],
                "freq": 0,
            }
        )
    return entities


def attach_quote_examples(entities: list[dict], drama_root: Path, limit_per: int = 2) -> None:
    """Scan content-e*.json quotes; if zh contains entity zh name, attach en/zh example."""
    by_drama: dict[str, list[dict]] = {}
    for e in entities:
        by_drama.setdefault(e["drama"], []).append(e)

    for drama_slug, ents in by_drama.items():
        folder = drama_root / "content" / drama_slug
        if not folder.is_dir():
            continue
        files = sorted(folder.glob("content-e*.json"))[:12]  # sample first episodes
        for fp in files:
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            ep = data.get("episode") or fp.stem.replace("content-", "")
            for scene in data.get("scenes") or []:
                sid = scene.get("id") or scene.get("num") or "s?"
                for qi, q in enumerate(scene.get("quotes") or []):
                    zh = (q.get("zh") or "").strip()
                    en = (q.get("en") or "").strip()
                    if not en or not zh:
                        continue
                    for e in ents:
                        if len(e["examples"]) >= limit_per:
                            continue
                        names = [e["zh"]] + e.get("aliases", [])
                        if any(n and n in zh for n in names):
                            e["examples"].append(
                                {
                                    "en": en.strip('"'),
                                    "zh": zh.strip("「」"),
                                    "source": f"drama:{drama_slug}:{ep}:{sid}-q{qi+1}",
                                }
                            )
                            e["freq"] = e.get("freq", 0) + 1


def write_json_files(folder: Path, items: list[dict], id_key: str = "id") -> int:
    folder.mkdir(parents=True, exist_ok=True)
    # clear old
    for old in folder.glob("*.json"):
        old.unlink()
    for item in items:
        path = folder / f"{item[id_key]}.json"
        path.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(items)


def main() -> int:
    if not DRAMA.is_dir():
        print(f"drama-analysis not found at {DRAMA}", file=sys.stderr)
        return 1

    vocab_path = DRAMA / "docs" / "english-vocab.html"
    phrases_path = DRAMA / "docs" / "english-phrases.html"
    if not vocab_path.exists() or not phrases_path.exists():
        print("missing english-vocab.html or english-phrases.html", file=sys.stderr)
        return 1

    functions = parse_vocab_html(vocab_path)
    # prefer priority tag first in sort
    functions.sort(key=lambda x: (-x.get("freq", 0), x["lemma"]))
    n_fn = write_json_files(CONTENT / "function", functions)
    print(f"function: {n_fn}")

    phrases = parse_phrases_html(phrases_path)
    n_ph = write_json_files(CONTENT / "phrases", phrases)
    print(f"phrases: {n_ph}")

    entities: list[dict] = []
    cast_files = list((DRAMA / "content").glob("*/cast.md"))
    for cast in cast_files:
        drama_slug = cast.parent.name
        entities.extend(parse_cast_md(cast, drama_slug))
    # dedupe by id
    by_id = {e["id"]: e for e in entities}
    entities = list(by_id.values())
    attach_quote_examples(entities, DRAMA)
    n_ent = write_json_files(CONTENT / "entity", entities)
    print(f"entity: {n_ent} from {len(cast_files)} cast.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
