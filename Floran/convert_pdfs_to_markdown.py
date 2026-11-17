"""Convertit les PDF de ./Document en fichiers Markdown dans ./Document markdown.

- Titres detectes par taille de police / gras / numerotation -> dièses
- Colonnes gerees (lecture colonne par colonne)
- Images extraites dans ./Document markdown/images/<nom du fichier>/
- Figures vectorielles rendues en PNG
- Tableaux convertis en table Markdown

Usage:
    python convert_pdfs_to_markdown.py [--only nom_partiel]
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "Document"
OUT = ROOT / "Document markdown"
GS_PREFIX = "Google scolar - "

LIGATURES = {
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb00": "ff",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "st",
    "\ufb06": "st",
}
CAPTION_RE = re.compile(
    r"^(figure|fig\.|table|algorithm|listing|equation|eq\.|schema|schéma|figure\s)\s*\d+",
    re.I,
)
EXAMPLE_RE = re.compile(r"^(trajectory|episode|segment|sub-?trajectory)\s*\d", re.I)
KEYWORD_RE = re.compile(r"^(keywords?|key\s?words|mots\s?clés|index\s+terms)\s*:", re.I)
NUMBERED_RE = re.compile(r"^(\d+(\.\d+)*)\.?\s+\S")
BARE_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\.?$")
BULLET_RE = re.compile(r"^([•‣▪◦·]|[-–—]\s|\d{1,2}[.)]|[a-z][.)])\s+")
KNOWN_SECTION_RE = re.compile(
    r"^(abstract|résumé|resumo|highlights|introduction|references|bibliography|"
    r"acknowledg\w*|conclusion\w*|related\s+work|background|methodology|methods?|"
    r"experiment\w*|results?|discussion|appendix|supplementary|index\s+terms)\b",
    re.I,
)
FOOTER_RE = re.compile(
    r"^(page\s*)?\d+(\s*(of|/)\s*\d+)?$|"
    r"^(arxiv:|doi:|www\.|https?://)|"
    r"preprint submitted to|authorized licensed use|"
    r"^preprint\s*\.|under review as a conference|"
    r"^\s*(received|accepted|revised|published)\s*:?\s*\d",
    re.I,
)
MATHY_RE = re.compile(r"[=∑∫√≈≤≥→↦⇒↔∞±−∈∀⊂∪∩]")
CITATION_RE = re.compile(r"\[\d{1,3}([,;]\s*\d{1,3})*\]")
MATH_START_RE = re.compile(r"^\d+\s*[\(\[]")
ROMAN_RE = re.compile(r"^[IVXLCDM]+\.(?:\s+\S|$)")
LOOSE_WORDS_RE = re.compile(r"\b[a-z]\s+[a-z]\b")
STANDALONE_RE = re.compile(
    r"(?i)^(?:abstract|keywords?|key\s+words|acknowledgments?|references|highlights|contents|index)\b"
)
SPLIT_HEAD_RE = re.compile(r"(?i)^(?:abstract|keywords?|key\s+words|acknowledgments?)\b")
CONNECTOR_END_RE = re.compile(
    r"(?i)(?:\b(?:of|and|the|in|for|with|to|a|an|on|by|from|at|or|as|via|through|using|under|into|per))\s*$"
)


def is_numbered(text: str) -> bool:
    return bool(NUMBERED_RE.match(text) or ROMAN_RE.match(text))
SENTENCE_END = tuple(".!?;:”\"')]")
HEADING_GAP = 0.9
LABEL_RE = re.compile(
    r"^(article|open|original research|research article|review article|short report|"
    r"proceedings|preprint)$",
    re.I,
)
AUTHOR_RE = re.compile(
    r"[@]|"
    r"\b(university|université|institute|institut|laborator|department|faculty|school|"
    r"college|correspondence|research center|center for|school of)\b",
    re.I,
)


def looks_like_author(text: str) -> bool:
    if AUTHOR_RE.search(text):
        return True
    if text.count(",") >= 2 and len(text) <= 160 and not text.endswith((".", "!", "?")):
        capitals = re.findall(r"\b[A-ZÀ-Ý][\wÀ-ÿ'’-]*", text)
        if len(capitals) >= 3:
            return True
    return False


def heading_worthy(text: str) -> bool:
    if is_numbered(text) or KNOWN_SECTION_RE.match(text):
        return True
    return bool(re.search(r"[A-Za-zÀ-ÿ]{4,}", text))


def heading_rejected(text: str, numbered: bool, max_len: int = 160) -> bool:
    if len(text) > max_len:
        return True
    if not numbered and text.endswith((".", ",", ";", ":")):
        return True
    if re.fullmatch(r"[\d\s.()+\-*/=]+", text):
        return True
    if MATHY_RE.search(text) or MATH_START_RE.match(text):
        return True
    if CITATION_RE.search(text):
        return True
    if text[:1] in "•‣▪◦·":
        return True
    if EXAMPLE_RE.match(text):
        return True
    if LOOSE_WORDS_RE.search(text):
        return True
    if text[:1].islower() and not numbered:
        return True
    if re.match(r"^[a-z]\.\s", text):
        return True
    if numbered:
        match = re.match(r"^(?:\d+(?:\.\d+)*|[IVXLCDM]+|[ivxlcdm]+)\.?\s*(.*)$", text)
        if match is not None and len(match.group(1).strip()) < 3:
            if not KNOWN_SECTION_RE.match(text):
                return True
    return False


# --------------------------------------------------------------------------- utils
def soft_round(value: float, step: float = 0.5) -> float:
    return round(value / step) * step


def clean_text(text: str) -> str:
    text = "".join(LIGATURES.get(ch, ch) for ch in text)
    text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def join_lines(previous: str, current: str) -> str:
    if not previous:
        return current
    if not current:
        return previous
    if previous.endswith("-") and current[:1].islower():
        return previous[:-1] + current
    if previous.endswith(("-", "\u2010", "\u2011")) and current[:1].islower():
        return previous[:-1] + current
    return previous + " " + current


def is_bold(span: dict) -> bool:
    flags = span.get("flags", 0)
    if flags & 16:
        return True
    return "bold" in span.get("font", "").lower()


def overlap(a, b) -> float:
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def center_inside(rect, box) -> bool:
    cx = (rect[0] + rect[2]) / 2
    cy = (rect[1] + rect[3]) / 2
    return box[0] <= cx <= box[2] and box[1] <= cy <= box[3]


def md_escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


# --------------------------------------------------------------------------- stats
def extract_block_lines(block: dict) -> list[dict]:
    lines = []
    for line in block.get("lines", []):
        spans = [s for s in line.get("spans", []) if s["text"].strip()]
        if not spans:
            continue
        spans.sort(key=lambda s: s["bbox"][0])
        parts: list[str] = []
        previous_end = None
        for span in spans:
            if previous_end is not None and span["bbox"][0] - previous_end > 1.4:
                parts.append(" ")
            parts.append(span["text"])
            previous_end = span["bbox"][2]
        text = clean_text("".join(parts))
        if not text:
            continue
        by_size: dict[float, int] = {}
        by_bold: dict[bool, int] = {}
        for span in spans:
            count = len(span["text"])
            key = soft_round(span["size"])
            by_size[key] = by_size.get(key, 0) + count
            by_bold[is_bold(span)] = by_bold.get(is_bold(span), 0) + count
        size = max(by_size, key=lambda k: by_size[k])
        bold = max(by_bold, key=lambda k: by_bold[k])
        lines.append(
            {
                "text": text,
                "size": size,
                "raw_size": size,
                "bold": bold,
                "bbox": list(line["bbox"]),
            }
        )
    return lines


def page_text_blocks(page: pymupdf.Page) -> list[dict]:
    blocks = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type", 0) != 0:
            continue
        lines = extract_block_lines(block)
        if not lines:
            continue
        blocks.append({"bbox": list(block["bbox"]), "lines": lines, "kind": "text"})
    return blocks


def collect_stats(doc: pymupdf.Document) -> dict:
    size_counter: Counter = Counter()
    all_size_counter: Counter = Counter()
    footer_counter: Counter = Counter()
    page_count = len(doc)

    for page in doc:
        height = page.rect.height
        for block in page_text_blocks(page):
            y0, y1 = block["bbox"][1], block["bbox"][3]
            text = " ".join(line["text"] for line in block["lines"])
            band = None
            if y1 < 0.075 * height:
                band = "top"
            elif y0 > 0.925 * height:
                band = "bottom"
            if band and text:
                key = re.sub(r"\d+", "#", text.lower())
                key = re.sub(r"\s+", " ", key).strip()
                footer_counter[(band, key)] += 1
            for line in block["lines"]:
                if line["raw_size"] < 5.5:
                    continue
                if len(line["text"]) >= 50:
                    size_counter[line["size"]] += len(line["text"])
                all_size_counter[line["size"]] += len(line["text"])

    source = size_counter or all_size_counter
    if not source:
        body = 10.0
    else:
        body = source.most_common(1)[0][0]
        if body < 6:
            body = 10.0

    threshold = max(3, math.ceil(0.25 * page_count))
    dropped = {key for key, count in footer_counter.items() if count >= threshold}

    return {"body": body, "footers": dropped, "pages": page_count}


# --------------------------------------------------------------------------- layout
def classify_column(items: list[dict], page: pymupdf.Page) -> list[dict]:
    width = page.rect.width
    mid = width / 2.0
    tol = 0.05 * width

    left, right, spanning = [], [], []
    for item in items:
        bbox = item["bbox"]
        if bbox[2] <= mid + tol and bbox[0] < mid:
            left.append(item)
        elif bbox[0] >= mid - tol and bbox[2] > mid:
            right.append(item)
        else:
            spanning.append(item)

    columnish = len(left) + len(right)
    two_cols = (
        len(left) >= 2
        and len(right) >= 2
        and columnish >= 0.55 * max(1, len(items))
    )
    if not two_cols:
        return sorted(items, key=lambda i: (round(i["bbox"][1], 1), i["bbox"][0]))

    col_tops = [i["bbox"][1] for i in left + right]
    col_bottoms = [i["bbox"][3] for i in left + right]
    top_edge = min(col_tops) if col_tops else 0
    bottom_edge = max(col_bottoms) if col_bottoms else height_of(page)

    head, tail, middle_span = [], [], []
    for item in spanning:
        bbox = item["bbox"]
        if bbox[3] <= top_edge + 6:
            head.append(item)
        elif bbox[1] >= bottom_edge - 6:
            tail.append(item)
        else:
            middle_span.append(item)

    for item in middle_span:
        cx = (item["bbox"][0] + item["bbox"][2]) / 2
        (left if cx < mid else right).append(item)

    by_y = lambda i: (round(i["bbox"][1], 1), i["bbox"][0])
    return sorted(head, key=by_y) + sorted(left, key=by_y) + sorted(right, key=by_y) + sorted(
        tail, key=by_y
    )


def height_of(page: pymupdf.Page) -> float:
    return page.rect.height


# --------------------------------------------------------------------------- figures
def raster_images(page: pymupdf.Page, doc: pymupdf.Document) -> list[dict]:
    images = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 1:
            continue
        bbox = list(block["bbox"])
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width < 55 or height < 45:
            continue
        payload = block.get("image")
        if not payload:
            continue
        images.append(
            {
                "bbox": bbox,
                "data": payload,
                "ext": block.get("ext", "png"),
                "w": block.get("width", 0),
                "h": block.get("height", 0),
            }
        )
    return images


def cluster_rects(rects: list[tuple], gap: float = 10.0) -> list[tuple]:
    if not rects:
        return []
    expanded = [(r[0] - gap, r[1] - gap, r[2] + gap, r[3] + gap) for r in rects]
    parent = list(range(len(rects)))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = expanded[i], expanded[j]
            if a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]:
                continue
            union(i, j)

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(rects)):
        groups[find(i)].append(i)

    clusters = []
    for members in groups.values():
        x0 = min(rects[i][0] for i in members)
        y0 = min(rects[i][1] for i in members)
        x1 = max(rects[i][2] for i in members)
        y1 = max(rects[i][3] for i in members)
        clusters.append((x0, y0, x1, y1))
    return clusters


def vector_figures(page: pymupdf.Page, text_blocks: list[dict], images: list[dict],
                   tables: list[tuple]) -> list[tuple]:
    drawings = page.get_drawings()
    if len(drawings) < 4:
        return []

    width, height = page.rect.width, page.rect.height
    rects = []
    for drawing in drawings:
        rect = drawing["rect"]
        box = (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1))
        w, h = box[2] - box[0], box[3] - box[1]
        if w < 6 or h < 4:
            continue
        if w > 0.92 * width and h > 0.92 * height:
            continue
        rects.append(box)

    figures = []
    image_boxes = [tuple(i["bbox"]) for i in images]
    for cluster in cluster_rects(rects):
        x0, y0, x1, y1 = cluster
        w, h = x1 - x0, y1 - y0
        if w < 85 or h < 55:
            continue
        if w * h > 0.45 * width * height:
            continue
        if any(overlap(cluster, t) > 0.15 * overlap(t, t) for t in tables):
            continue
        if any(overlap(cluster, img) > 0.2 * min(w * h, (img[2] - img[0]) * (img[3] - img[1]))
               for img in image_boxes):
            continue

        inside_chars = 0
        inside_blocks = 0
        for block in text_blocks:
            if overlap(block["bbox"], cluster) <= 0:
                continue
            if not center_inside(block["bbox"], cluster):
                continue
            inside_blocks += 1
            inside_chars += sum(len(line["text"]) for line in block["lines"])
        if inside_chars > 900 or inside_blocks > 12:
            continue

        captions = [
            b for b in text_blocks
            if center_inside(b["bbox"], cluster)
            and b["lines"]
            and CAPTION_RE.match(b["lines"][0]["text"])
        ]
        if captions:
            top = min(b["bbox"][1] for b in captions)
            if top > y0 + 8:
                y1 = min(y1, top - 3)
        if y1 - y0 < 45:
            continue
        figures.append((x0, y0, x1, y1))
    return figures


# --------------------------------------------------------------------------- tables
def page_tables(page: pymupdf.Page) -> list[dict]:
    out = []
    try:
        finder = page.find_tables()
    except Exception:
        return out
    for table in finder.tables:
        try:
            rows = table.extract()
        except Exception:
            continue
        if not rows:
            continue
        cleaned = []
        for row in rows:
            cells = [clean_text(cell) if cell else "" for cell in row]
            cleaned.append(cells)
        if not any(any(cell for cell in row) for row in cleaned):
            continue
        out.append({"bbox": list(table.bbox), "rows": cleaned})
    return out


def table_to_markdown(rows: list[list[str]]) -> str:
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    while len(rows) > 1 and not any(cells for cells in rows[-1]):
        rows.pop()
    header = rows[0]
    body = rows[1:]
    if body and [c.lower() for c in header] == [c.lower() for c in body[0]]:
        body = body[1:]
    lines = ["| " + " | ".join(md_escape_cell(c) for c in header) + " |"]
    lines.append("| " + " | ".join("---" for _ in range(width)) + " |")
    for row in body:
        lines.append("| " + " | ".join(md_escape_cell(c) for c in row) + " |")
    return "\n".join(lines)


# --------------------------------------------------------------------------- headings
def heading_candidates(lines_by_page: list[list[dict]], body: float) -> list[tuple]:
    candidates = []
    for page_index, lines in enumerate(lines_by_page):
        for line in lines:
            text = line["text"]
            numbered = is_numbered(text)
            if CAPTION_RE.match(text) or KEYWORD_RE.match(text):
                continue
            if heading_rejected(text, numbered):
                continue
            if looks_like_author(text) or not heading_worthy(text):
                continue
            size = line["size"]
            if size >= body + HEADING_GAP:
                candidates.append((page_index, line, size))
            elif numbered and line["bold"] and size >= body - 0.5 and len(text) <= 80:
                candidates.append((page_index, line, size))
            elif numbered and size >= body - 0.5 and len(text) <= 80 and _shouty(text):
                candidates.append((page_index, line, size))
            elif page_index <= 1 and KNOWN_SECTION_RE.match(text) and size >= body:
                candidates.append((page_index, line, size))
    return candidates


def _shouty(text: str) -> bool:
    letters = [ch for ch in text if ch.isalpha()]
    return bool(letters) and all(ch.isupper() for ch in letters)


def probe_line(lines: list[dict]) -> str:
    first = lines[0]["text"]
    if len(lines) > 1 and len(first) <= 10 and not re.search(r"[A-Za-zÀ-ÿ]{4,}", first):
        return first + " " + lines[1]["text"]
    return first


def build_tier_levels(candidates: list[tuple], body: float) -> tuple[dict, float]:
    big = [(page, line, size) for page, line, size in candidates if size >= body + HEADING_GAP]
    if not big:
        if not candidates:
            return {}, 0.0
        return {}, max(size for _, _, size in candidates)

    title_size = max(size for _, _, size in big)
    sizes = sorted({size for _, _, size in big}, reverse=True)
    clusters: list[list[float]] = []
    for size in sizes:
        if clusters and clusters[-1][0] - size <= 1.2:
            clusters[-1].append(size)
        else:
            clusters.append([size])

    levels: dict[float, int] = {}
    for index, group in enumerate(clusters):
        level = min(1 + index, 6)
        for size in group:
            levels[size] = level
    return levels, title_size


def number_depth(text: str) -> int:
    match = re.match(r"^\s*(\d+(?:\.\d+)*|[IVXLCDM]+|[ivxlcdm]+)", text)
    if not match:
        return 1
    parts = [part for part in match.group(1).split(".") if part]
    return max(1, len(parts))


def heading_level(lines: list[dict], levels: dict, title_size: float, page_index: int,
                  body: float) -> int | None:
    if not lines:
        return None
    first = lines[0]["text"]
    probe = probe_line(lines)
    numbered = is_numbered(probe)
    if CAPTION_RE.match(first) or KEYWORD_RE.match(first):
        return None
    if heading_rejected(probe, numbered):
        return None
    if looks_like_author(probe) or not heading_worthy(probe):
        return None

    size = lines[0]["size"]
    known = bool(KNOWN_SECTION_RE.match(probe))
    level: int | None

    if numbered:
        if len(probe) <= 80 and (
            size >= body + HEADING_GAP
            or lines[0]["bold"]
            or _shouty(probe)
        ):
            level = min(1 + number_depth(probe), 6)
        else:
            level = None
    elif size in levels:
        level = levels[size]
    elif size >= body + HEADING_GAP:
        level = max(2, min(1 + sum(1 for other in levels if other > size), 6))
    elif page_index <= 1 and known and size >= body:
        level = 3
    else:
        level = None

    if level is not None and page_index <= 1 and level != 1 and not numbered and not known:
        level = None
    return level


def looks_like_new_heading(text: str) -> bool:
    words = re.findall(r"[A-Za-zÀ-ÿ']+", text)
    if len(words) < 2:
        return False
    return all(word[0].isupper() for word in words)


def is_bare_marker(text: str) -> bool:
    return len(text) <= 12 and not re.search(r"[A-Za-zÀ-ÿ]{4,}", text)


def split_heading(lines: list[dict], level: int, body: float) -> tuple[str, list[dict]]:
    first_size = lines[0]["size"]
    big = first_size >= body + HEADING_GAP
    if big:
        min_size = max(body + HEADING_GAP, first_size - 1.0)
        max_size = first_size + 0.6
    else:
        min_size = min(first_size, body - 0.5)
        max_size = first_size + 1.0
    first_bold = lines[0]["bold"]
    bare = is_bare_marker(lines[0]["text"])
    allow_new = level != 1

    heading = lines[0]["text"]
    split_mark = SPLIT_HEAD_RE.match(heading)
    if split_mark is not None and len(heading) > split_mark.end() + 20:
        tail_line = dict(lines[0])
        tail_line["text"] = heading[split_mark.end():].strip()
        return heading[: split_mark.end()].strip(), [tail_line] + lines[1:]
    if allow_new and len(lines) > 1 and not bare:
        second = lines[1]["text"]
        if STANDALONE_RE.match(heading) and re.match(r"^[A-ZÀ-Þ]", second):
            return heading, lines[1:]
        if (
            len(heading) < 40
            and not CONNECTOR_END_RE.search(heading)
            and not re.match(r"^[a-zà-ÿ]", second)
        ):
            return heading, lines[1:]
    for index in range(1, len(lines)):
        text = lines[index]["text"]
        size = lines[index]["size"]
        stop = (
            is_numbered(text)
            or BARE_NUMBER_RE.match(text) is not None
            or size < min_size
            or size > max_size
            or (big and lines[index]["bold"] != first_bold)
            or (not big and not lines[index]["bold"])
            or (allow_new and not bare and looks_like_new_heading(text))
        )
        if stop:
            return heading, lines[index:]
        sentence = re.search(r'[.!?]["”\')]?[\s]', text)
        if sentence:
            heading = (heading + " " + text[: sentence.end()]).strip()
            remainder = text[sentence.end():].strip()
            tail = lines[index + 1:]
            if remainder:
                head_line = dict(lines[index])
                head_line["text"] = remainder
                tail = [head_line] + tail
            return heading, tail
        if len(heading) + 1 + len(text) > 170:
            return heading, lines[index:]
        heading = (heading + " " + text).strip()
    return heading, []


# --------------------------------------------------------------------------- rendering
def render_document(doc: pymupdf.Document, stats: dict) -> str:
    body = stats["body"]
    footers = stats["footers"]
    page_count = len(doc)

    pages_items: list[list[dict]] = []
    lines_by_page: list[list[dict]] = []
    image_store: list[dict] = []
    seen_hashes: dict[str, str] = {}

    for page_index, page in enumerate(doc):
        text_blocks = page_text_blocks(page)
        kept_blocks = []
        for block in text_blocks:
            text = " ".join(line["text"] for line in block["lines"])
            key = (None, re.sub(r"\s+", " ", re.sub(r"\d+", "#", text.lower())).strip())
            y0, y1 = block["bbox"][1], block["bbox"][3]
            height = page.rect.height
            band = None
            if y1 < 0.075 * height:
                band = "top"
            elif y0 > 0.925 * height:
                band = "bottom"
            if band:
                key = (band, key[1])
            if key in footers:
                continue
            if FOOTER_RE.match(text.strip()):
                continue
            kept_blocks.append(block)

        tables = page_tables(page)
        for table in tables:
            for block in list(kept_blocks):
                if center_inside(block["bbox"], table["bbox"]) or (
                    overlap(block["bbox"], table["bbox"]) > 0.6 * overlap(block["bbox"], block["bbox"])
                ):
                    kept_blocks.remove(block)

        images = raster_images(page, doc)
        figures = vector_figures(page, kept_blocks, images, [t["bbox"] for t in tables])

        for figure in figures:
            for block in list(kept_blocks):
                if center_inside(block["bbox"], figure):
                    lines = block["lines"]
                    if lines and CAPTION_RE.match(lines[0]["text"]):
                        continue
                    kept_blocks.remove(block)

        items: list[dict] = []
        for block in kept_blocks:
            items.append({"kind": "text", "bbox": block["bbox"], "block": block})
        for table in tables:
            items.append({"kind": "table", "bbox": table["bbox"], "table": table})
        for image in images:
            items.append({"kind": "image", "bbox": image["bbox"], "image": image})
        for figure in figures:
            items.append({"kind": "vector", "bbox": list(figure), "figure": figure})

        items = classify_column(items, page)
        pages_items.append(items)

        page_lines = []
        for item in items:
            if item["kind"] == "text":
                page_lines.extend(item["block"]["lines"])
        lines_by_page.append(page_lines)

    candidates = heading_candidates(lines_by_page, body)
    levels, title_size = build_tier_levels(candidates, body)

    if pages_items:
        pages_items[0] = merge_title_blocks(pages_items[0], title_size)

    blocks_out: list[str] = []
    last_kind: str | None = None
    title_written = False
    title_norm = ""

    def emit(text: str, kind: str) -> None:
        nonlocal last_kind
        if not text:
            return
        if kind == "list" and last_kind == "list" and blocks_out:
            blocks_out[-1] += "\n" + text
        else:
            blocks_out.append(text)
        last_kind = kind

    for page_index, items in enumerate(pages_items):
        for item in items:
            kind = item["kind"]

            if kind == "table":
                emit(table_to_markdown(item["table"]["rows"]), "other")
                continue

            if kind == "image":
                link = save_image(item["image"], image_store, seen_hashes)
                emit(f"![figure]({link})" if link else "<!-- image non extraite -->", "other")
                continue

            if kind == "vector":
                link = save_vector(page_index, item["figure"], image_store, seen_hashes,
                                   doc[page_index])
                emit(f"![figure]({link})" if link else "<!-- image non extraite -->", "other")
                continue

            block = item["block"]
            lines = block["lines"]
            if not lines:
                continue

            first = lines[0]["text"]
            joined = " ".join(line["text"] for line in lines)

            if page_index <= 1 and LABEL_RE.match(first):
                continue

            if title_norm and page_index > 0:
                normalized = re.sub(r"\s+", " ", joined.lower()).strip()
                if len(normalized) >= 25 and (
                    title_norm.startswith(normalized) or normalized.startswith(title_norm)
                ):
                    continue

            if CAPTION_RE.match(first):
                emit("*" + joined + "*", "other")
                continue

            remaining = lines
            while remaining:
                level = heading_level(remaining, levels, title_size, page_index, body)
                if level is None:
                    break
                heading, rest = split_heading(remaining, level, body)
                if re.fullmatch(r"[\d\s.]+", heading):
                    break
                remaining = rest
                if level == 1:
                    if title_written:
                        level = 2
                    else:
                        title_written = True
                        title_norm = re.sub(r"\s+", " ", heading.lower()).strip()
                if not heading.endswith(("U.S.", "e.g.", "i.e.", "etc.")):
                    heading = re.sub(r"(?<=[A-Za-z])\.$", "", heading)
                emit("#" * min(level, 6) + " " + heading, "other")

            if not remaining:
                continue

            text = ""
            for line in remaining:
                text = join_lines(text, line["text"])
            if not text:
                continue

            if BULLET_RE.match(text) and not is_numbered(text):
                payload = BULLET_RE.match(text)
                emit("- " + text[payload.end():].strip(), "list")
                continue

            if (
                last_kind == "para"
                and blocks_out
                and not blocks_out[-1].endswith(SENTENCE_END)
            ):
                blocks_out[-1] = join_lines(blocks_out[-1], text)
                continue

            emit(text, "para")

    body_text = "\n\n".join(blocks_out).strip()

    header = [
        "---",
        f"source: {_current_source}",
        f"pages: {page_count}",
        "---",
        "",
    ]
    return "\n".join(header) + "\n" + body_text + "\n"


def merge_title_blocks(items: list[dict], title_size: float) -> list[dict]:
    if not items or title_size <= 0:
        return items
    threshold = title_size - 0.6
    out: list[dict] = []
    buffer: dict | None = None
    count = 0

    def flush() -> None:
        nonlocal buffer, count
        if buffer is not None:
            out.append(buffer)
        buffer = None
        count = 0

    for item in items:
        usable = item["kind"] == "text" and count < 3
        if usable:
            lines = item["block"]["lines"]
            joined = " ".join(line["text"] for line in lines)
            usable = (
                all(line["size"] >= threshold for line in lines)
                and not is_numbered(joined)
                and not KNOWN_SECTION_RE.match(joined)
                and not CAPTION_RE.match(joined)
                and not KEYWORD_RE.match(joined)
                and "@" not in joined
                and not looks_like_author(joined)
                and not re.search(
                    r"\b(university|institute|laboratory|department|school|college|"
                    r"research|faculty|institut|université|laboratoire)\b",
                    joined,
                    re.I,
                )
            )
        if not usable:
            flush()
            out.append(item)
            continue
        lines = item["block"]["lines"]
        if buffer is None:
            buffer = {
                "kind": "text",
                "bbox": list(item["bbox"]),
                "block": {"bbox": list(item["bbox"]), "lines": list(lines)},
            }
        else:
            buffer["block"]["lines"].extend(lines)
            old, new = buffer["bbox"], item["bbox"]
            merged = [min(old[0], new[0]), min(old[1], new[1]),
                      max(old[2], new[2]), max(old[3], new[3])]
            buffer["bbox"] = merged
            buffer["block"]["bbox"] = merged
        count += 1
    flush()
    return out



def save_image(image: dict, store: list[dict], seen: dict[str, str]) -> str | None:
    data = image["data"]
    digest = hashlib.sha1(data).hexdigest()
    if digest in seen:
        return seen[digest]
    ext = (image["ext"] or "png").lower()
    if ext == "jpeg":
        ext = "jpg"
    if ext not in {"png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "webp"}:
        ext = "png"
    name = f"img_{len(store) + 1:03d}.{ext}"
    folder = OUT / "images" / _current_stem
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(data)
    link = f"images/{_current_stem}/{name}"
    seen[digest] = link
    store.append(link)
    return link


def save_vector(page_index: int, box: tuple, store: list[dict], seen: dict[str, str],
                page: pymupdf.Page) -> str | None:
    key = "vector:" + hashlib.sha1(
        f"{page_index}:{box[0]:.1f}:{box[1]:.1f}:{box[2]:.1f}:{box[3]:.1f}".encode()
    ).hexdigest()
    if key in seen:
        return seen[key]
    name = f"img_{len(store) + 1:03d}.png"
    folder = OUT / "images" / _current_stem
    folder.mkdir(parents=True, exist_ok=True)
    try:
        clip = pymupdf.Rect(box[0] - 2, box[1] - 2, box[2] + 2, box[3] + 2)
        pix = page.get_pixmap(clip=clip, dpi=200)
        pix.save(str(folder / name))
    except Exception:
        return None
    link = f"images/{_current_stem}/{name}"
    seen[key] = link
    store.append(link)
    return link


_current_source = ""
_current_stem = ""


# --------------------------------------------------------------------------- main
def convert(path: Path) -> Path:
    global _current_source, _current_stem

    relative = path.relative_to(ROOT)
    if "Google scolar" in path.parent.name:
        stem = GS_PREFIX + path.stem
    else:
        stem = path.stem

    _current_source = relative.as_posix()
    _current_stem = re.sub(r'[<>:"/\\|?*]', "-", stem)

    target = OUT / f"{stem}.md"
    OUT.mkdir(parents=True, exist_ok=True)

    with pymupdf.open(path) as doc:
        stats = collect_stats(doc)
        markdown = render_document(doc, stats)

    target.write_text(markdown, encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Convertit les PDF de Document en Markdown.")
    parser.add_argument("--only", default="", help="ne convertit que les fichiers contenant cette chaine")
    args = parser.parse_args()

    if not SRC.exists():
        print(f"Dossier introuvable: {SRC}", file=sys.stderr)
        return 1

    files = sorted(SRC.rglob("*.pdf"), key=lambda p: str(p).lower())
    if args.only:
        files = [f for f in files if args.only.lower() in f.name.lower()]
    if not files:
        print("Aucun PDF trouve.", file=sys.stderr)
        return 1

    for path in files:
        if "GSITEM" in str(path):
            print(f"ignore (GSITEM): {path.name}")
            continue
        target = convert(path)
        print(f"ok  {target.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
