#!/usr/bin/env python3
"""
Ze vstupního JSONL (OpenAIRE researchProducts) vygeneruje Markdown tabulku.

Pro každý záznam (který už je předfiltrovaný na "má aspoň jeden non-DOI PID")
udělá DVA řádky:

1) mainTitle | publicationDate | publisher | schemes
   - schemes = všechny hodnoty z record["pids"][].scheme, oddělené čárkou

2) URLs přes „celou tabulku“:
   - první sloupec obsahuje všechny URLs z instances[].urls, každé na vlastním řádku (<br>)
   - ostatní tři sloupce jsou prázdné
"""

import argparse
import gzip
import json
from pathlib import Path
from typing import Dict, List, Optional


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


def get_pid_schemes(rec: Dict) -> str:
    """Vezme schemes z record['pids'] a vrátí je jako 'scheme1, scheme2, ...'."""
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
    in_fh = open_maybe_gzip(input_path, "rt", encoding="utf-8")
    out_fh = Path(output_path).open("w", encoding="utf-8")

    try:
        # hlavička tabulky
        out_fh.write("| mainTitle | publicationDate | publisher | schemes |\n")
        out_fh.write("|-----------|-----------------|-----------|---------|\n")

        for line in in_fh:
            line = line.strip()
            if not line:
                continue

            rec = json.loads(line)

            title = escape_md(rec.get("mainTitle"))
            pub_date = escape_md(rec.get("publicationDate"))
            publisher = escape_md(rec.get("publisher"))
            schemes = escape_md(get_pid_schemes(rec))

            urls = get_all_urls(rec)
            if urls:
                # každá URL na vlastním řádku, klikatelné
                urls_md = "<br>".join(
                    f"[{escape_md(u)}]({u})" for u in urls
                )
            else:
                urls_md = ""

            # 1. řádek: hlavní informace
            out_fh.write(f"| {title} | {pub_date} | {publisher} | {schemes} |\n")

            # 2. řádek: „colspan“ – všechny URLs v prvním sloupci, zbytek prázdný
            out_fh.write(f"| {urls_md} |  |  |  |\n")

    finally:
        in_fh.close()
        out_fh.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Vygeneruje Markdown tabulku pro záznamy s non-DOI PIDy (2 řádky na záznam)."
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

