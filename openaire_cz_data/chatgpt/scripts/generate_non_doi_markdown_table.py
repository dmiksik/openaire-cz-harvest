#!/usr/bin/env python3
"""
Ze vstupních JSONL souborů vygeneruje Markdown report:

- --full-input  : celý harvest (např. cz_datasets_countryCZ.jsonl)
- --input       : podmnožina záznamů (např. jen non-DOI PIDy)

Výstup (Markdown):

1) Úvodní statistiky pro FULL harvest:
   - celkový počet záznamů
   - počet záznamů s alespoň jedním PIDem
   - počet bez PIDu
   - seznam všech PID schémat

2) Úvodní statistiky pro SUBSET (--input):
   - totéž jako výše
   - tabulka kombinací PID schémat (z record['pids'], instances[].pids a
     instances[].alternateIdentifiers) pro tuto podmnožinu

3) Detailní tabulka po záznamech ze SUBSETu (dva řádky na záznam):
   - 1. řádek: mainTitle | publicationDate | publisher | schemes
       (schemes = hodnoty record['pids'][].scheme, oddělené čárkou)
   - 2. řádek: všechny URL z instances[].urls v prvním sloupci,
       každá na vlastním řádku (<br>), ostatní tři sloupce prázdné
"""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def open_maybe_gzip(path: str, mode: str = "rt", encoding: str = "utf-8"):
    p = Path(path)
    if p.suffix == ".gz":
        return gzip.open(p, mode, encoding=encoding)
    else:
        return p.open(mode, encoding=encoding)


def escape_md(text: Optional[str]) -> str:
    r"""
    Jednoduché escapování pro použití v Markdown tabulce:
    - None -> ""
    - nahradí | za \|
    - odřádkuje na <br>
    """
    if text is None:
        return ""
    s = str(text)
    s = s.replace("|", r"\|")
    s = s.replace("\n", "<br>")
    return s


def get_pid_schemes_top(rec: Dict) -> str:
    """Vezme schemes jen z record['pids'] (pro sloupec 'schemes' v hlavní tabulce)."""
    schemes: List[str] = []
    for pid in rec.get("pids") or []:
        scheme = pid.get("scheme")
        if scheme:
            schemes.append(str(scheme))
    # unikátní v pořadí výskytu
    seen = set()
    unique = []
    for s in schemes:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return ", ".join(unique)


def collect_all_pid_schemes(rec: Dict) -> List[str]:
    """
    Nasbírá schémata všech PIDů z:
      - record['pids']
      - instances[].pids
      - instances[].alternateIdentifiers

    Vrací seřazený seznam unikátních schémat (lowercase) pro daný záznam.
    """
    schemes: List[str] = []

    def add_scheme(s: Optional[str]):
        if not s:
            return
        schemes.append(str(s).lower())

    for pid in rec.get("pids") or []:
        add_scheme(pid.get("scheme"))

    for inst in rec.get("instances") or []:
        for pid in inst.get("pids") or []:
            add_scheme(pid.get("scheme"))
        for alt in inst.get("alternateIdentifiers") or []:
            add_scheme(alt.get("scheme"))

    # unikátní v pořadí výskytu
    seen = set()
    unique = []
    for s in schemes:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def get_all_urls(rec: Dict) -> List[str]:
    """Všechny URL z instances[].urls, bez duplicit, v pořadí výskytu."""
    urls: List[str] = []
    for inst in rec.get("instances") or []:
        for u in inst.get("urls") or []:
            u = str(u).strip()
            if not u:
                continue
            urls.append(u)
    # deduplikace se zachováním pořadí
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def compute_basic_pid_stats(path: str) -> Tuple[int, int, Set[str]]:
    """
    Spočítá základní PID statistiky pro daný JSONL/JSONL.GZ soubor:
      - total_records
      - records_with_pids
      - global_schemes (set všech PID schémat)
    """
    total_records = 0
    records_with_pids = 0
    global_schemes: Set[str] = set()

    fh = open_maybe_gzip(path, "rt", encoding="utf-8")
    try:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total_records += 1
            rec = json.loads(line)
            schemes = collect_all_pid_schemes(rec)
            if schemes:
                records_with_pids += 1
                global_schemes.update(schemes)
    finally:
        fh.close()

    return total_records, records_with_pids, global_schemes


def generate_markdown(full_input_path: str, subset_input_path: str, output_path: str) -> None:
    # 1) Statistika pro FULL harvest
    full_total, full_with_pids, full_schemes = compute_basic_pid_stats(full_input_path)

    # 2) Statistika pro SUBSET (+ kombinace schémat)
    subset_total = 0
    subset_with_pids = 0
    subset_schemes: Set[str] = set()
    combo_counter: Counter[str] = Counter()

    subset_fh = open_maybe_gzip(subset_input_path, "rt", encoding="utf-8")
    try:
        for line in subset_fh:
            line = line.strip()
            if not line:
                continue
            subset_total += 1
            rec = json.loads(line)
            schemes = collect_all_pid_schemes(rec)
            if schemes:
                subset_with_pids += 1
                subset_schemes.update(schemes)
                combo_key = " + ".join(schemes)
                combo_counter[combo_key] += 1
    finally:
        subset_fh.close()

    # 3) Zápis reportu
    out_fh = Path(output_path).open("w", encoding="utf-8")
    try:
        # Shrnutí – FULL harvest
        out_fh.write("# Overview of PID schemes\n\n")

        out_fh.write("## Full harvest (all countryCode=CZ datasets)\n\n")
        out_fh.write(f"- Input file: `{full_input_path}`\n")
        out_fh.write(f"- Total records: **{full_total}**\n")
        out_fh.write(f"- Records with at least one PID: **{full_with_pids}**\n")
        out_fh.write(
            f"- Records without any PID: **{full_total - full_with_pids}**\n"
        )
        if full_schemes:
            out_fh.write(
                "- Distinct PID schemes (full harvest): "
                + ", ".join(sorted(full_schemes))
                + "\n\n"
            )
        else:
            out_fh.write("- Distinct PID schemes (full harvest): *(none)*\n\n")

        # Shrnutí – SUBSET
        out_fh.write("## This report subset\n\n")
        out_fh.write(f"- Input file: `{subset_input_path}`\n")
        out_fh.write(f"- Total records in this subset: **{subset_total}**\n")
        out_fh.write(
            f"- Records with at least one PID (subset): **{subset_with_pids}**\n"
        )
        out_fh.write(
            f"- Records without any PID (subset): "
            f"**{subset_total - subset_with_pids}**\n"
        )
        if subset_schemes:
            out_fh.write(
                "- Distinct PID schemes in subset: "
                + ", ".join(sorted(subset_schemes))
                + "\n\n"
            )
        else:
            out_fh.write("- Distinct PID schemes in subset: *(none)*\n\n")

        # Tabulka kombinací schémat pro SUBSET
        out_fh.write("### PID scheme combinations in subset\n\n")
        out_fh.write("| PID schemes combination | Count |\n")
        out_fh.write("|-------------------------|-------|\n")
        if combo_counter:
            for combo, count in combo_counter.most_common():
                out_fh.write(f"| `{combo}` | {count} |\n")
        else:
            out_fh.write("| *(none)* | 0 |\n")

        out_fh.write("\n\n")

        # Detailní tabulka po záznamech SUBSETu
        out_fh.write("## Records (subset)\n\n")
        out_fh.write("| mainTitle | publicationDate | publisher | schemes |\n")
        out_fh.write("|-----------|-----------------|-----------|---------|\n")

        subset_fh2 = open_maybe_gzip(subset_input_path, "rt", encoding="utf-8")
        try:
            for line in subset_fh2:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)

                title = escape_md(rec.get("mainTitle"))
                pub_date = escape_md(rec.get("publicationDate"))
                publisher = escape_md(rec.get("publisher"))
                schemes_top = escape_md(get_pid_schemes_top(rec))

                urls = get_all_urls(rec)
                if urls:
                    urls_md = "<br>".join(
                        f"[{escape_md(u)}]({u})" for u in urls
                    )
                else:
                    urls_md = ""

                # 1. řádek: hlavní informace
                out_fh.write(
                    f"| {title} | {pub_date} | {publisher} | {schemes_top} |\n"
                )
                # 2. řádek: všechny URLs v prvním sloupci
                out_fh.write(f"| {urls_md} |  |  |  |\n")
        finally:
            subset_fh2.close()

    finally:
        out_fh.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Vygeneruje Markdown report: statistiky PID pro full harvest "
            "i subset a detailní dvouřádkovou tabulku pro subset."
        )
    )
    ap.add_argument(
        "--full-input",
        required=True,
        help="JSONL/JSONL.GZ s celým harvestem (např. cz_datasets_countryCZ.jsonl)",
    )
    ap.add_argument(
        "--input",
        "-i",
        required=True,
        help="JSONL/JSONL.GZ s podmnožinou záznamů (např. non-DOI PIDy).",
    )
    ap.add_argument(
        "--output-md",
        "-o",
        required=True,
        help="Výstupní Markdown soubor (např. non_doi_records_table.md)",
    )
    args = ap.parse_args()

    generate_markdown(args.full_input, args.input, args.output_md)


if __name__ == "__main__":
    main()

