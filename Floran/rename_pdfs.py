from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent / "Document"
MAX_STEM = 120

LIGATURES = {
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb00": "ff",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "st",
    "\ufb06": "st",
}
INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {
    f"LPT{i}" for i in range(1, 10)
}


def normalize(text: str) -> str:
    text = "".join(LIGATURES.get(char, char) for char in text)
    text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text.strip(" .,:;-")


def is_boilerplate(text: str) -> bool:
    value = text.strip().lower()
    if len(value) < 3 or re.fullmatch(r"[\W\d_]+", value):
        return True
    if value.startswith(
        (
            "arxiv:",
            "www.",
            "https://",
            "http://",
            "doi:",
            "received:",
            "revised:",
            "accepted:",
            "published:",
            "licensee",
            "this article",
            "copyright",
            "scientific reports",
        )
    ):
        return True
    if value in {"open", "article", "abstract", "research highlights"}:
        return True
    if "ieee transactions" in value or "transactions on knowledge" in value:
        return True
    if re.search(r"\bvol\.?\s+\d+|\bno\.?\s+\d+", value):
        return True
    return False


def first_page_lines(path: Path) -> tuple[list[dict], float]:
    with pymupdf.open(path) as document:
        page = document[0]
        lines: list[dict] = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                spans.sort(key=lambda s: s["bbox"][0])
                chunks: list[str] = []
                previous_end = None
                for span in spans:
                    x0, x1 = span["bbox"][0], span["bbox"][2]
                    if previous_end is not None and x0 - previous_end > 1.2:
                        chunks.append(" ")
                    chunks.append(span["text"].strip())
                    previous_end = x1
                lines.append(
                    {
                        "text": "".join(chunks),
                        "size": max(s["size"] for s in spans),
                        "y": min(s["bbox"][1] for s in spans),
                    }
                )
        return lines, page.rect.height


def metadata_title(path: Path) -> str | None:
    with pymupdf.open(path) as document:
        raw = document.metadata.get("title") or ""
    title = normalize(raw)
    if len(title) < 10 or title.lower() in {
        "print",
        "untitled",
        "microsoft word",
        "document1",
    }:
        return None
    if "crossmark" in title.lower() or title.lower().startswith(("arxiv:", "1 introduction")):
        return None
    if re.fullmatch(r"[\d\s.:-]+", title):
        return None
    return title


def guess_title(path: Path) -> str:
    lines, height = first_page_lines(path)
    candidates = [
        line
        for line in lines
        if line["y"] < height * 0.55 and not is_boilerplate(line["text"])
    ]
    if candidates:
        largest = max(line["size"] for line in candidates)
        candidates = [line for line in candidates if line["size"] >= largest - 1.6]
        candidates.sort(key=lambda line: line["y"])
        chosen = [candidates[0]]
        for previous, current in zip(candidates, candidates[1:]):
            if current["y"] - previous["y"] > 45:
                break
            chosen.append(current)
        title = normalize(" ".join(line["text"] for line in chosen))
        if len(title) >= 8:
            return title
    return metadata_title(path) or normalize(path.stem)


def make_stem(title: str) -> str:
    stem = title.replace(":", " - ")
    stem = INVALID_CHARS.sub("-", stem)
    stem = re.sub(r"\s+", "_", stem.strip())
    stem = re.sub(r"_{2,}", "_", stem).strip("._- ")
    if stem.upper() in RESERVED:
        stem = "_" + stem
    if len(stem) > MAX_STEM:
        truncated = stem[:MAX_STEM]
        last_separator = truncated.rfind("_")
        if last_separator > MAX_STEM // 2:
            truncated = truncated[:last_separator]
        stem = truncated.rstrip("._- ")
    return stem


def unique_target(folder: Path, stem: str, source: Path) -> Path:
    target = folder / f"{stem}.pdf"
    suffix = 2
    while target.exists() and target != source:
        target = folder / f"{stem}_{suffix}.pdf"
        suffix += 1
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename PDF files after the document title.")
    parser.add_argument(
        "--apply", action="store_true", help="actually rename files (default: preview only)"
    )
    args = parser.parse_args()

    files = sorted(ROOT.rglob("*.pdf"), key=lambda path: str(path).lower())
    if not files:
        print(f"Aucun PDF trouve dans {ROOT}", file=sys.stderr)
        return 1

    print(f"Mode: {'APPLICATION' if args.apply else 'APERCU (aucune modification)'}")
    print(f"PDF trouves: {len(files)}\n")
    changed = 0
    for path in files:
        title = guess_title(path)
        target = unique_target(path.parent, make_stem(title), path)
        relative_old = path.relative_to(ROOT.parent)
        if target == path:
            print(f"=  {relative_old}  (deja conforme)")
            continue
        relative_new = target.relative_to(ROOT.parent)
        marker = "->" if args.apply else "=>"
        print(f"{marker} {relative_old}\n   {relative_new}")
        if args.apply:
            path.rename(target)
        changed += 1

    print(f"\n{changed} renommage(s) {'effectue(s)' if args.apply else 'prevu(s)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
