#!/usr/bin/env python3
"""
Ze vstupního JSONL (OpenAIRE researchProducts) vygeneruje Markdown report:

1) Úvodní statistiky:
   - celkový počet záznamů
   - počet záznamů s alespoň jedním PIDem
   - seznam všech PID schémat
   - tabulka kombinací PID schémat a počtů jejich výskytů

   Kombinace schémat se počítají z PIDů na úrovni:
     - record["pids"]
     - instances[].pids
     - instances[].alternateIdentifiers

2) Detailní tabulka (dva řádky na záznam – pro každý záznam ve vstupním JSONL):
   - 1. řádek: mainTitle | publicationDate | publisher | schemes
       (schemes = hodnoty record["pids"][].scheme, oddělené čárkou)
   - 2. řádek: všechny URL z instances[].urls v prvním sloupci, každá na vlastním řádku (<br>),
       ostatní tři sloupce prázdné
"""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set


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


def generate_markdown(input_path: str, output_path: str) -> None:
    # 1. průchod – sběr statistik
    total_records = 0
    records_with_pids = 0
    global_schemes: Set[str] = set()
    combo_counter: Counter[str] = Counter()

    in_fh = open_maybe_gzip(input_path, "rt", encoding="utf-8")
    try:
        for line in in_fh:
            line = line.strip()
            if not line:
                continue
            total_records += 1

            rec = json.loads(line)
            schemes = collect_all_pid_schemes(rec)
            if schemes:
                records_with_pids += 1
                global_schemes.update(schemes)
                combo_key = " + ".join(schemes)
                combo_counter[combo_key] += 1
    finally:
        in_fh.close()

    # 2. zápis reportu
    out_fh = Path(output_path).open("w", encoding="utf-8")

    try:
        # Úvodní shrnutí
        out_fh.write("# Overview of PID schemes in this report\n\n")
        out_fh.write(f"- Total records in this report: **{total_records}**\n")
        out_fh.write(f"- Records with at least one PID: **{records_with_pids}**\n")
        out_fh.write(
            f"- Records without any PID: **{total_records - records_with_pids}**\n"
        )
        if global_schemes:
            out_fh.write(
                "- Distinct PID schemes observed: "
                + ", ".join(sorted(global_schemes))
                + "\n\n"
            )
        else:
            out_fh.write("- Distinct PID schemes observed: *(none)*\n\n")

        # Tabulka kombinací schémat
        out_fh.write("## PID scheme combinations\n\n")
        out_fh.write("| PID schemes combination | Count |\n")
        out_fh.write("|-------------------------|-------|\n")
        if combo_counter:
            for combo, count in combo_counter.most_common():
                out_fh.write(f"| `{combo}` | {count} |\n")
        else:
            out_fh.write("| *(none)* | 0 |\n")

        out_fh.write("\n\n")

        # Detailní tabulka po záznamech
        out_fh.write("## Records\n\n")
        out_fh.write("| mainTitle | publicationDate | publisher | schemes |\n")
        out_fh.write("|-----------|-----------------|-----------|---------|\n")

        # 3. průchod – generování dvouřádkové tabulky pro každý záznam
        in_fh2 = open_maybe_gzip(input_path, "rt", encoding="utf-8")
        try:
            for line in in_fh2:
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
            in_fh2.close()

    finally:
        out_fh.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Vygeneruje Markdown report pro záznamy (typicky s non-DOI PIDy): "
            "souhrn PID schémat, kombinace, a dvouřádkovou tabulku na záznam."
        )
    )
    ap.add_argument(
        "--input",
        "-i",
        required=True,
        help="Vstupní JSONL/JSONL.GZ (např. cz_datasets_countryCZ_non_doi_pids.jsonl)",
    )
    ap.add_argument(
        "--output-md",
        "-o",
        required=True,
        help="Výstupní Markdown soubor (např. non_doi_records_table.md)",
    )
    args = ap.parse_args()

    generate_markdown(args.input, args.output_md)


if __name__ == "__main__":
    main()

