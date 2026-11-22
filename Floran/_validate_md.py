#!/usr/bin/env python3
import os
import re
from pathlib import Path
from urllib.parse import unquote

base = Path(r"D:\Doss\Ecole\5ème\MYPRED")
tc = base / "analyse" / "tableau_comparatif.md"
fic_dir = base / "analyse" / "fiches"
doc_dir = base / "Document markdown"

issues = []

# 1) Check table: count data rows (lines starting with '| [' )
with open(tc, "r", encoding="utf-8") as f:
    lines = f.readlines()

# header is line1 '# ...' then line2 empty then line3 header row then line4 separator? Let us inspect
# From read: line5 is header row (| Titre | ...), line6 is separator, line7+ are data rows until line21? 
data_rows = []
for i, line in enumerate(lines, start=1):
    if line.startswith("| [") or (line.startswith("| [") is False and line.strip().startswith("| [") == False):
        pass
    # more directly: data rows are table rows that begin with '| [' (the title links)
    if re.match(r'^\|\s*\[', line):
        data_rows.append((i, line))

print(f"DATA_ROWS: {len(data_rows)}")
if len(data_rows) != 13:
    issues.append(f"(1) Tableau: attendu 13 lignes de documents, trouvé {len(data_rows)}.")

# Check columns roughly: header has 11 columns
header_line = None
for i, line in enumerate(lines, start=1):
    if line.startswith("| Titre | Réf. source"):
        header_line = (i, line)
        break
if header_line:
    # count '|' separators: number of columns = count of '|' - 1 (ends with |) roughly
    h = header_line[1].strip()
    # split by | but keep empty? easier: count occurrences
    cols = [c for c in h.split("|")]
    # first and last may be empty
    cols = [c for c in cols if c.strip() != "" or c == ""]
    # better
    cols2 = h.strip().strip("|").split("|")
    colcount = len(cols2)
    print(f"HEADER_COLS: {colcount}")
    if colcount != 11:
        issues.append(f"(1) Tableau: en-tête semble avoir {colcount} colonnes, attendu 11.")
else:
    issues.append("(1) Tableau: ligne d'en-tête 'Titre | Réf. source ...' non trouvée.")

# 2) Extract all markdown links: [text](<target>) or [text](target)
link_pattern = re.compile(r'\]\((<[^>]+>|[^)]+)\)')
all_links = []  # (srcfile, lineno, target)
for i, line in enumerate(lines, start=1):
    for m in link_pattern.finditer(line):
        target = m.group(1)
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        all_links.append((str(tc), i, target))

# also check fiches files
fic_files = sorted(fic_dir.glob("*.md"))
for ff in fic_files:
    with open(ff, "r", encoding="utf-8") as f:
        flines = f.readlines()
    for i, line in enumerate(flines, start=1):
        for m in link_pattern.finditer(line):
            target = m.group(1)
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            all_links.append((str(ff), i, target))

print(f"TOTAL_LINKS: {len(all_links)}")

# validate links
for src, lno, target in all_links:
    # skip external http
    if target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
        continue
    # split anchor
    if "#" in target:
        path_part, anchor = target.split("#", 1)
    else:
        path_part, anchor = target, None
    # decode
    path_part_decoded = unquote(path_part)
    # resolve relative to src file
    srcp = Path(src)
    if path_part_decoded == "" or path_part_decoded is None:
        # anchor only, same file
        resolved = srcp
    else:
        resolved = (srcp.parent / path_part_decoded).resolve()
    # check existence
    if not resolved.exists():
        issues.append(f"(2) Lien cassé: dans {os.path.basename(src)}:{lno} -> '{target}' (résolu: {resolved})")
        continue
    # check anchor #Lnn
    if anchor:
        # match L digits
        m = re.match(r'^L(\d+)$', anchor, re.IGNORECASE)
        if m:
            ln = int(m.group(1))
            # count lines in resolved file
            try:
                with open(resolved, "r", encoding="utf-8") as rf:
                    rlines = rf.readlines()
                rcount = len(rlines)
                if ln > rcount:
                    issues.append(f"(3) Ancre hors limites: dans {os.path.basename(src)}:{lno} -> '{target}' pointe L{ln} mais fichier a {rcount} lignes ({resolved.name})")
            except Exception as e:
                issues.append(f"(3) Impossible de lire pour vérifier ancre: {resolved} ({e})")
        # else: non-L anchor, ignore for now

# 4) suspicious filename patterns (obvious typos in names) - check targets
for src, lno, target in all_links:
    if target.startswith("http"):
        continue
    path_part = target.split("#", 1)[0]
    path_part_decoded = unquote(path_part)
    # look for weird chars sequences or common typos patterns?
    # check for 'scolar' in path
    if "scolar" in path_part_decoded.lower():
        issues.append(f"(4) Nom de fichier suspect ('scolar'): dans {os.path.basename(src)}:{lno} -> '{target}'")
    # check for double spaces
    if "  " in path_part_decoded:
        issues.append(f"(4) Espace double suspect: dans {os.path.basename(src)}:{lno} -> '{target}'")

# 5) French typos visible in created files (tableau + fiches 10,11,12)
# scan for common typos
typo_patterns = [
    (r'\bcomapr', "comapr?"),
    (r'\bmodèl[es]?\b', None),  # just example
]
# be specific: look for 'fautes de frappeFrench visibles restantes' - maybe check known patterns
# common: 'apprentissage' ok, look for obvious typos like 'recommadation', 'contratstif', 'graphees' etc.
# scan all created files: tableau + fiches 10,11,12
files_to_check = [tc, fic_dir/"10_llm_mgcl_poi_recommendation.md", fic_dir/"11_graphcl_hafidi_node_level.md", fic_dir/"12_graphcl_you_augmentations.md"]
typo_regexes = [
    (r'\brecommadation\b', 'recommadation'),
    (r'\bcontratstif\b', 'contratstif'),
    (r'\bgraphees\b', 'graphees'),
    (r'\bapproches\b.*\bapproches\b', None),  # not a typo
    (r'\baprentissage\b', 'aprentissage'),
    (r'\bconstrastive\b', 'constrastive'),
    (r'\btrajectoire?s?\b.*\btrajectoire?s?\b', None),
]
for fp in files_to_check:
    if not fp.exists():
        issues.append(f"(5) Fichier à vérifier (typos) manquant: {fp}")
        continue
    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            # check some typos
            if re.search(r'\brecommadation\b', line, re.IGNORECASE):
                issues.append(f"(5) Faute possible 'recommadation': {fp.name}:{i}")
            if re.search(r'\baprentissage\b', line, re.IGNORECASE):
                issues.append(f"(5) Faute possible 'aprentissage': {fp.name}:{i}")
            if re.search(r'\bconstrastive\b', line, re.IGNORECASE):
                issues.append(f"(5) Faute possible 'constrastive': {fp.name}:{i}")
            if re.search(r'\bcontrastee\b', line, re.IGNORECASE):
                issues.append(f"(5) Faute possible 'contrastee': {fp.name}:{i}")
            if re.search(r'GraphCL\s*—\s*Hafidi', line):
                pass
            # look for 'fautes de frappeFrench' in text? probably not
            # check 'modeles' missing accent in some contexts? optional

# Print issues
if not issues:
    print("ALL_OK")
else:
    for it in issues:
        print(it)
