#!/usr/bin/env python3
"""
Analyze 'Unknown Repository' records:

- breakdown by publisher
- detailed Markdown table, 2 rows per record, sorted by mainTitle:

  1) | mainTitle | mainTitle | publicationDate | publisher | collectedFrom | schemes |
  2) | all URLs as clickable links in column 1 | ...empty columns... |

Input:  JSONL/JSONL.GZ with records (typically unknown_repository_records.jsonl)
Output: Markdown report
"""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


def open_maybe_gzip(path: str, mode: str = "rt", encoding: str = "utf-8"):
    p = Path(path)
    if p.suffix == ".gz":
        return gzip.open(p, mode, encoding=encoding)
    else:
        return p.open(mode, encoding=encoding)


def escape_md(text: Optional[str]) -> str:
    r"""
    Basic escaping for Markdown table cells:
    - None -> ""
    - replace '|' with '\|'
    - replace newlines with '<br>'
    """
    if text is None:
        return ""
    s = str(text)
    s = s.replace("|", r"\|")
    s = s.replace("\n", "<br>")
    return s


def collect_all_pid_schemes(rec: Dict) -> List[str]:
    """
    Collect PID schemes from:
      - rec['pids']
      - rec['instances'][].pids
      - rec['instances'][].alternateIdentifiers

    Returns a list of unique schemes (lowercase), in order of first appearance.
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

    # unique, preserving order
    seen = set()
    unique: List[str] = []
    for s in schemes:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def collect_urls(rec: Dict) -> List[str]:
    """Return all distinct URLs from instances[].urls, in order of appearance."""
    urls: List[str] = []
    for inst in rec.get("instances") or []:
        for u in inst.get("urls") or []:
            u = str(u).strip()
            if not u:
                continue
            urls.append(u)

    seen = set()
    unique: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def collect_collected_from_values(rec: Dict) -> List[str]:
    """Return distinct collectedFrom.value strings, in order of appearance."""
    vals: List[str] = []
    for cf in rec.get("collectedFrom") or []:
        v = (cf.get("value") or "").strip()
        if not v:
            # fallback na key, kdyby value nebylo
            v = (cf.get("key") or "").strip()
        if not v:
            continue
        vals.append(v)

    seen = set()
    unique: List[str] = []
    for v in vals:
        if v not in seen:
            seen.add(v)
            unique.append(v)
    return unique


def load_records_and_publishers(path: str) -> Tuple[List[Dict], Counter]:
    """
    Načte všechny záznamy z JSONL/JSONL.GZ, vrátí:
      - seznam záznamů
      - Counter publisherů
    """
    records: List[Dict] = []
    publisher_counter: Counter[str] = Counter()

    fh = open_maybe_gzip(path, "rt", encoding="utf-8")
    try:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records.append(rec)

            pub = (rec.get("publisher") or "").strip()
            if not pub:
                pub = "(no publisher)"
            publisher_counter[pub] += 1
    finally:
        fh.close()

    return records, publisher_counter


def generate_markdown(input_path: str, output_path: str) -> None:
    records, publisher_counter = load_records_and_publishers(input_path)

    # seřadit záznamy podle mainTitle (case-insensitive), fallback na ""
    records.sort(
        key=lambda r: (
            str(r.get("mainTitle") or "").lower(),
            str(r.get("publicationDate") or ""),
        )
    )

    out = Path(output_path).open("w", encoding="utf-8")

    try:
        out.write("# Unknown Repository records – publishers and detailed list\n\n")
        out.write(f"- Input file: `{input_path}`\n")
        out.write(f"- Total records: **{len(records)}**\n\n")

        # --- Breakdown by publisher ---
        out.write("## Breakdown by publisher\n\n")
        out.write("| publisher | records |\n")
        out.write("|-----------|---------|\n")
        if publisher_counter:
            for pub, count in publisher_counter.most_common():
                out.write(f"| {escape_md(pub)} | {count} |\n")
        else:
            out.write("| *(none)* | 0 |\n")
        out.write("\n\n")

        # --- Detailed per-record table ---
        out.write("## Records (sorted by mainTitle)\n\n")
        out.write(
            "| mainTitle | mainTitle | publicationDate | publisher | collectedFrom | schemes |\n"
        )
        out.write(
            "|-----------|-----------|-----------------|-----------|---------------|---------|\n"
        )

        for rec in records:
            title = escape_md(rec.get("mainTitle"))
            pub_date = escape_md(rec.get("publicationDate"))
            publisher = escape_md(rec.get("publisher") or "")
            cf_vals = collect_collected_from_values(rec)
            cf_str = ", ".join(cf_vals)
            schemes = ", ".join(collect_all_pid_schemes(rec))

            urls = collect_urls(rec)
            if urls:
                urls_md = "<br>".join(f"[{escape_md(u)}]({u})" for u in urls)
            else:
                urls_md = ""

            # 1. řádek: metadata (2x mainTitle podle zadání)
            out.write(
                f"| {title} | {title} | {pub_date} | {publisher} | "
                f"{escape_md(cf_str)} | {escape_md(schemes)} |\n"
            )

            # 2. řádek: všechny URLs v prvním sloupci (ostatní prázdné)
            out.write(f"| {urls_md} |  |  |  |  |  |\n")

    finally:
        out.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Generate publisher breakdown and detailed two-row-per-record "
            "Markdown table from unknown_repository_records.jsonl."
        )
    )
    ap.add_argument(
        "--input-jsonl",
        "-i",
        required=True,
        help="JSONL/JSONL.GZ with unknown repository records "
             "(e.g. unknown_repository_records.jsonl)",
    )
    ap.add_argument(
        "--output-md",
        "-o",
        required=True,
        help="Output Markdown file.",
    )
    args = ap.parse_args()

    generate_markdown(args.input_jsonl, args.output_md)


if __name__ == "__main__":
    main()

