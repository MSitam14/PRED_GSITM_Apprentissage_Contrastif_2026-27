from pathlib import Path
from urllib.parse import unquote
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(r"D:\Doss\Ecole\5ème\MYPRED")
SOURCE = ROOT / "analyse" / "tableau_comparatif.md"
OUTPUT = ROOT / "tableau_comparatif.xlsx"

LINK_RE = re.compile(r"\[([^\]]*)\]\(<([^>]+)>\)")
ESCAPED_PIPE = "\u0001"

TITLE = "Tableau comparatif — apprentissage contrastif, graphes et trajectoires"
WIDTHS = [32, 14, 52, 52, 52, 52, 46, 52, 46, 46, 20, 52]


def split_row(line):
    parts = line.strip().strip("|").replace("\\|", ESCAPED_PIPE).split("|")
    return [p.strip().replace(ESCAPED_PIPE, "|") for p in parts]


def resolve_target(raw):
    target = unquote(raw).split("#", 1)[0]
    if target.startswith("../"):
        target = target[3:]
    elif not target.startswith(("/", "http")):
        target = "analyse/" + target
    return target.replace("\\", "/")


def cell_value(text):
    links = LINK_RE.findall(text)
    display = LINK_RE.sub(lambda m: m.group(1), text)
    display = display.replace("**", "").replace("`", "").strip()
    target = resolve_target(links[0][1]) if links else None
    return display, target


def read_table():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith("| Titre |"))
    header = split_row(lines[header_index])
    rows = []
    for line in lines[header_index + 2:]:
        if not line.startswith("|"):
            break
        cells = split_row(line)
        if len(cells) != len(header):
            raise ValueError(f"Nombre de colonnes inattendu : {len(cells)}")
        rows.append([cell_value(c) for c in cells])
    return header, rows


def build_workbook(header, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Tableau comparatif"

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(header))
    title_cell = ws.cell(row=1, column=1, value=TITLE)
    title_cell.font = Font(bold=True, size=13)
    title_cell.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 24

    header_fill = PatternFill("solid", fgColor="1F3864")
    for col, name in enumerate(header, 1):
        cell = ws.cell(row=2, column=col, value=name)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[2].height = 32

    for row_index, row in enumerate(rows, 3):
        for col_index, (display, target) in enumerate(row, 1):
            value = target if col_index == 2 and target else display
            cell = ws.cell(row=row_index, column=col_index, value=value)
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    for index, width in enumerate(WIDTHS, 1):
        ws.column_dimensions[get_column_letter(index)].width = width

    last_row = len(rows) + 2
    last_col = get_column_letter(len(header))
    ws.freeze_panes = "C3"
    ws.auto_filter.ref = f"A2:{last_col}{last_row}"
    ws.sheet_view.showGridLines = True

    notes = wb.create_sheet("Notes")
    notes.column_dimensions["A"].width = 20
    notes.column_dimensions["B"].width = 80
    entries = [
        (TITLE, None),
        ("Source", "analyse/tableau_comparatif.md"),
        ("Contenu", "Feuille « Tableau comparatif » : 12 colonnes, 13 articles."),
        ("Colonne source", "Affiche le chemin réel du document Markdown source, relatif à la racine MYPRED."),
        ("", ""),
        ("Légende — Compatibilité G-SITM", None),
        ("Élevée", "Transposition directe au graphe typé et historisé de G-SITM."),
        ("Moyenne", "Applicable avec adaptation."),
        ("Faible", "Transposition partielle."),
        ("Nulle", "Pas de graphe ni d'approche transférable."),
        ("", ""),
        ("Références [Lnn]", "Pointent vers la ligne exacte du document Markdown source."),
        ("G-SITM", "Modèle de données, sans apprentissage contrastif."),
    ]
    for row_index, (key, value) in enumerate(entries, 1):
        label = notes.cell(row=row_index, column=1, value=key)
        label.font = Font(bold=True)
        label.alignment = Alignment(vertical="top")
        if value:
            notes.cell(row=row_index, column=2, value=value)

    return wb


def main():
    header, rows = read_table()
    wb = build_workbook(header, rows)
    wb.save(OUTPUT)
    print(f"Écrit : {OUTPUT}")
    print(f"Colonnes : {len(header)}, lignes de données : {len(rows)}")
    print(f"Chemins source : {sum(1 for row in rows if row[1][1])}")


if __name__ == "__main__":
    main()
