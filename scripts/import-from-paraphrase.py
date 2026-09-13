#!/usr/bin/env python3
"""Import / cold-start scenarios from language_paraphrase HTML cards."""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
LP = Path(__file__).resolve().parents[2] / "language_paraphrase"

# Prefer linking to published paraphrase site when assets stay there
LP_PAGES_BASE = "https://czh55.github.io/language_paraphrase"


def decode(s: str) -> str:
    return html.unescape(s).strip()


def strip_tags(s: str) -> str:
    return decode(re.sub(r"<[^>]+>", "", s))


def load_function_index() -> list[tuple[str, str]]:
    """Return list of (id, lemma.lower()) sorted by lemma length desc for matching."""
    items = []
    for path in (CONTENT / "function").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        items.append((data["id"], data["lemma"].lower()))
    items.sort(key=lambda x: len(x[1]), reverse=True)
    return items


def load_phrase_index() -> list[tuple[str, str]]:
    items = []
    for path in (CONTENT / "phrases").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        # use a short key from frame (strip italics placeholders)
        key = re.sub(r"\s+", " ", data["frame_en"].lower())
        key = re.sub(r"\bx\b|\by\b|\.\.\.", "", key)
        key = key.strip(" ,.")
        if len(key) >= 4:
            items.append((data["id"], key[:40]))
    items.sort(key=lambda x: len(x[1]), reverse=True)
    return items


STOP = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "for",
    "is",
    "it",
    "be",
    "as",
    "at",
    "by",
    "if",
    "so",
    "no",
    "not",
    "too",
    "all",
    "get",
    "got",
    "do",
    "did",
    "does",
    "have",
    "has",
    "had",
    "was",
    "were",
    "with",
    "from",
    "this",
    "that",
    "real",
}


def link_chunk(chunk: str, fn_idx: list[tuple[str, str]], ph_idx: list[tuple[str, str]]) -> list[dict]:
    text = chunk.lower().strip()
    links = []
    for fid, lemma in fn_idx:
        if not lemma or lemma in STOP or len(lemma) < 4:
            continue
        # prefer whole-word-ish match
        if re.search(rf"(?<![a-z]){re.escape(lemma)}(?![a-z])", text):
            links.append({"module": "function", "id": fid})
            break
    for pid, key in ph_idx:
        tokens = [t for t in re.split(r"[^a-z']+", key) if len(t) > 3 and t not in STOP]
        if tokens and all(t in text for t in tokens[:1]) and any(t in text for t in tokens[:2] or tokens):
            # require first distinctive token
            if tokens[0] in text:
                links.append({"module": "phrases", "id": pid})
                break
    return links


def parse_scenario_html(path: Path, meta: dict, fn_idx, ph_idx) -> dict:
    text = path.read_text(encoding="utf-8")
    slug = meta["slug"]

    scenes = []
    for sm in re.finditer(
        r'<section class="scene-card" id="(s\d+)"[^>]*>(.*?)</section>',
        text,
        re.S,
    ):
        sid = sm.group(1)
        body = sm.group(2)
        title_cn_m = re.search(r"<h2>(.*?)</h2>", body)
        title_en_m = re.search(r'<p class="scene-title-en">(.*?)</p>', body, re.S)
        time_m = re.search(r'<span class="time">(.*?)</span>', body)
        title_cn = strip_tags(title_cn_m.group(1)) if title_cn_m else sid
        title_en = strip_tags(title_en_m.group(1)) if title_en_m else ""
        time = strip_tags(time_m.group(1)) if time_m else ""

        sentences = []
        for art in re.finditer(r'<article class="sentence">(.*?)</article>', body, re.S):
            ab = art.group(1)
            zh_m = re.search(r'class="lang-block zh-block".*?<p>(.*?)</p>', ab, re.S)
            en_m = re.search(r'<p class="english">(.*?)</p>', ab, re.S)
            note_m = re.search(r'<p class="note"><span>表达提示</span>(.*?)</p>', ab, re.S)
            audio_m = re.search(r'data-audio="([^"]+)"', ab)
            if not zh_m or not en_m:
                continue
            sentences.append(
                {
                    "zh": strip_tags(zh_m.group(1)),
                    "en": strip_tags(en_m.group(1)),
                    **({"note": strip_tags(note_m.group(1))} if note_m else {}),
                    **({"audio": audio_m.group(1)} if audio_m else {}),
                }
            )

        paraphrase = []
        det = re.search(r'<details class="paraphrase">(.*?)</details>', body, re.S)
        if det:
            for li in re.finditer(r"<li>(.*?)</li>", det.group(1), re.S):
                lb = li.group(1)
                p_m = re.search(r"<p>(.*?)</p>", lb, re.S)
                ch_m = re.search(r'<div class="chunks">(.*?)</div>', lb, re.S)
                if not p_m:
                    continue
                label_en = strip_tags(p_m.group(1))
                # "中文 → english"
                if "→" in label_en:
                    label, en = [x.strip() for x in label_en.split("→", 1)]
                else:
                    label, en = label_en, label_en
                chunks = []
                if ch_m:
                    raw = strip_tags(ch_m.group(1))
                    chunks = [c.strip() for c in re.split(r"[·|/]", raw) if c.strip()]
                    if not chunks and raw:
                        chunks = [raw]
                links = []
                for ch in chunks:
                    links.extend(link_chunk(ch, fn_idx, ph_idx))
                # dedupe links
                seen = set()
                uniq = []
                for lk in links:
                    k = (lk["module"], lk["id"])
                    if k not in seen:
                        seen.add(k)
                        uniq.append(lk)
                paraphrase.append(
                    {
                        "label": label,
                        "en": en,
                        "chunks": chunks,
                        **({"links": uniq} if uniq else {}),
                    }
                )

        scenes.append(
            {
                "id": sid,
                "title_cn": title_cn,
                "title_en": title_en,
                "time": time,
                "sentences": sentences,
                "paraphrase": paraphrase,
            }
        )

    practice = []
    prac = re.search(r'id="practice"[^>]*>(.*?)</section>', text, re.S)
    if prac:
        for art in re.finditer(r"<article>(.*?)</article>", prac.group(1), re.S):
            ab = art.group(1)
            zh_m = re.search(r"<p>(.*?)</p>", ab, re.S)
            en_m = re.search(r'class="practice-en"[^>]*>(.*?)<(?:button|$)', ab, re.S)
            if not en_m:
                en_m = re.search(r'class="practice-en">(.*?)</div>', ab, re.S)
            audio_m = re.search(r'data-audio="([^"]+)"', ab)
            if zh_m and en_m:
                practice.append(
                    {
                        "zh": strip_tags(zh_m.group(1)),
                        "en": strip_tags(en_m.group(1)),
                        **({"audio": audio_m.group(1)} if audio_m else {}),
                    }
                )

    return {
        "id": f"sc-{slug}",
        "module": "scenarios",
        "slug": slug,
        "title": meta.get("title") or slug,
        "title_en": meta.get("title_en") or "",
        "date": meta.get("date") or "",
        "platform": meta.get("platform") or "",
        "source_url": meta.get("webpage_url") or meta.get("url") or "",
        "external_html": f"{LP_PAGES_BASE}/{meta.get('html', '')}",
        "scenes": scenes,
        "practice": practice,
        "tags": [meta.get("platform") or "video"],
    }


def main() -> int:
    if not LP.is_dir():
        print(f"language_paraphrase not found at {LP}", file=sys.stderr)
        return 1

    index_path = LP / "docs" / "index.json"
    if not index_path.exists():
        print("missing language_paraphrase/docs/index.json", file=sys.stderr)
        return 1

    index = json.loads(index_path.read_text(encoding="utf-8"))
    fn_idx = load_function_index()
    ph_idx = load_phrase_index()

    out_dir = CONTENT / "scenarios"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.json"):
        old.unlink()

    n = 0
    for meta in index:
        html_name = meta.get("html")
        if not html_name:
            continue
        path = LP / "docs" / html_name
        if not path.exists():
            print(f"skip missing {html_name}")
            continue
        data = parse_scenario_html(path, meta, fn_idx, ph_idx)
        # sanitize any accidental bool title_en from earlier bug pattern
        for sc in data["scenes"]:
            if not isinstance(sc.get("title_en"), str):
                sc["title_en"] = ""
            if not isinstance(sc.get("time"), str):
                sc["time"] = ""
        (out_dir / f"{data['id']}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        n += 1
        linked = sum(
            1
            for sc in data["scenes"]
            for p in sc.get("paraphrase") or []
            if p.get("links")
        )
        print(f"  {data['slug']}: {len(data['scenes'])} scenes, {linked} paraphrases with links")

    print(f"scenarios: {n}")
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
