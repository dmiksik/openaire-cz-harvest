#!/usr/bin/env python3
"""
Vyfiltruje ze souboru s OpenAIRE researchProducts (type=dataset, countryCode=CZ)
všechny záznamy, které mají alespoň jeden PID se schématem jiným než DOI.

PIDy bereme z:
  - record["pids"]
  - record["instances"][].pids
  - record["instances"][].alternateIdentifiers

Výstup:
  - JSONL se záznamy splňujícími podmínku
  - Markdown přehled kombinací PID schémat a počtů jejich výskytů

Použití:

  python filter_cz_datasets_non_doi_pids.py \
      --input cz_datasets_countryCZ.jsonl.gz \
      --output-json cz_datasets_countryCZ_non_doi_pids.jsonl \
      --summary-md pid_combinations.md
"""

import argparse
import gzip
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def open_maybe_gzip(path: str, mode: str = "rt", encoding: str = "utf-8"):
    p = Path(path)
    if p.suffix == ".gz":
        return gzip.open(p, mode, encoding=encoding)
    else:
        return p.open(mode, encoding=encoding)


def collect_record_pids(rec: Dict) -> List[Tuple[Optional[str], str]]:
    """
    Nasbírá všechny PIDs z jednoho researchProduct záznamu.

    Vrací list (scheme, value), kde scheme může být None.
    """
    pids: List[Tuple[Optional[str], str]] = []

    def add_pid(scheme: Optional[str], value: Optional[str]):
        if not value:
            return
        pids.append((scheme, value))

    # 1) top-level pids
    for pid in rec.get("pids") or []:
        add_pid(pid.get("scheme"), pid.get("value"))

    # 2) instances[].pids a instances[].alternateIdentifiers
    for inst in rec.get("instances") or []:
        for pid in inst.get("pids") or []:
            add_pid(pid.get("scheme"), pid.get("value"))
        for alt in inst.get("alternateIdentifiers") or []:
            add_pid(alt.get("scheme"), alt.get("value"))

    return pids


def has_non_doi_pid(pids: List[Tuple[Optional[str], str]]) -> bool:
    """
    True, pokud mezi PIDy existuje alespoň jeden, jehož scheme != 'doi'
    (case-insensitive) a není None.
    """
    for scheme, _ in pids:
        if scheme is None:
            continue
        if scheme.lower() != "doi":
            return True
    return False


def pid_scheme_combo(pids: List[Tuple[Optional[str], str]]) -> Optional[str]:
    """
    Vrátí kanonický string reprezentující kombinaci PID schémat
    v jednom záznamu (např. 'doi + hdl', 'ark', ...).

    Schémata jsou:
      - zmenšená na lowercase
      - None se zahazuje (tedy jen pojmenovaná schémata)
      - unikátní (set), seřazená abecedně

    Pokud neexistuje žádné schéma, vrací None.
    """
    schemes = { (scheme or "").lower() for scheme, _ in pids if scheme }
    if not schemes:
        return None
    return " + ".join(sorted(schemes))


def process_file(
    input_path: str,
    output_json: str,
    summary_md_path: Optional[str] = None,
) -> None:
    total = 0
    matched = 0
    combo_counter: Counter[str] = Counter()

    in_fh = open_maybe_gzip(input_path, "rt", encoding="utf-8")
    out_fh = Path(output_json).open("w", encoding="utf-8")

    try:
        for line in in_fh:
            line = line.strip()
            if not line:
                continue
            total += 1

            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                sys.stderr.write(f"[warn] JSON decode error at line {total}: {e}\n")
                continue

            pids = collect_record_pids(rec)
            if not pids:
                continue

            if not has_non_doi_pid(pids):
                # záznam má pouze DOI, nebo žádné rozumné scheme → nezajímá nás
                continue

            # tenhle záznam bereme
            matched += 1
            out_fh.write(json.dumps(rec, ensure_ascii=False))
            out_fh.write("\n")

            combo = pid_scheme_combo(pids)
            if combo:
                combo_counter[combo] += 1

        sys.stderr.write(
            f"[done] Zpracováno {total} řádků, z toho {matched} se zjištěným alespoň jedním non-DOI PIDem.\n"
        )
        sys.stderr.flush()
    finally:
        in_fh.close()
        out_fh.close()

    # vytvořit Markdown přehled kombinací
    if combo_counter:
        lines = []
        lines.append("| PID schemes combination | Count |")
        lines.append("|------------------------|-------|")
        for combo, count in combo_counter.most_common():
            lines.append(f"| `{combo}` | {count} |")

        markdown = "\n".join(lines) + "\n"

        if summary_md_path:
            Path(summary_md_path).write_text(markdown, encoding="utf-8")
        else:
            # pošleme na stdout, logy zůstávají na stderr
            sys.stdout.write(markdown)
            sys.stdout.flush()


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Vybere záznamy, kde existuje alespoň jeden PID se schématem "
            "jiným než DOI, a udělá přehled kombinací PID schémat."
        )
    )
    ap.add_argument(
        "--input",
        "-i",
        required=True,
        help="Vstupní JSONL/JSONL.GZ soubor (výstup z harvestu type=dataset,countryCode=CZ)",
    )
    ap.add_argument(
        "--output-json",
        "-o",
        required=True,
        help="Výstupní JSONL se záznamy obsahujícími alespoň jeden non-DOI PID.",
    )
    ap.add_argument(
        "--summary-md",
        help=(
            "Volitelné: soubor, do kterého se uloží Markdown přehled kombinací "
            "PID schémat. Pokud není zadáno, vypíše se na stdout."
        ),
    )
    args = ap.parse_args()

    process_file(args.input, args.output_json, args.summary_md)


if __name__ == "__main__":
    main()

