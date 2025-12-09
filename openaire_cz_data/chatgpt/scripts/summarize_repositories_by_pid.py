#!/usr/bin/env python3
"""
Summarise source repositories (instances[].hostedBy) for:

1) Full CZ dataset harvest (all records in --full-input)
2) A subset of records (--subset-input), typically "non-DOI PIDs",
   broken down by PID scheme combinations.

Output: a single Markdown report with:
- table of repositories for ALL datasets
- per-PID-combination tables of repositories for the subset
"""

import argparse
import gzip
import json
from collections import Counter, defaultdict
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


def collect_hostedby_repos(rec: Dict) -> List[Tuple[str, str]]:
    """
    Collect hostedBy repos from instances[] as (key, name) tuples.
    Returns unique repos per record, in order of appearance.
    """
    repos: List[Tuple[str, str]] = []

    for inst in rec.get("instances") or []:
        hb = inst.get("hostedBy") or {}
        key = hb.get("key") or ""
        name = hb.get("value") or ""
        if not key and not name:
            continue
        repos.append((key, name))

    # unique, preserving order
    seen = set()
    unique: List[Tuple[str, str]] = []
    for r in repos:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def compute_full_repo_stats(full_path: str):
    """
    For the full harvest:
    - count total records
    - count, for each repo (hostedBy), in how many records it appears
    """
    total_records = 0
    repo_counter: Counter[Tuple[str, str]] = Counter()

    fh = open_maybe_gzip(full_path, "rt", encoding="utf-8")
    try:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total_records += 1
            rec = json.loads(line)
            repos = collect_hostedby_repos(rec)
            for r in repos:
                repo_counter[r] += 1
    finally:
        fh.close()

    return total_records, repo_counter


def compute_subset_repo_by_combo(subset_path: str):
    """
    For the subset:
    - compute PID scheme combination per record (string like 'doi + hdl')
    - for each combination, count in how many records each repo appears

    Returns:
      combos_to_repos: dict[combo_str] -> Counter[(key, name)]
      combos_total: dict[combo_str] -> total records for that combo
    """
    combos_to_repos: Dict[str, Counter] = defaultdict(Counter)
    combos_total: Counter[str] = Counter()

    fh = open_maybe_gzip(subset_path, "rt", encoding="utf-8")
    try:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)

            schemes = collect_all_pid_schemes(rec)
            combo = " + ".join(schemes) if schemes else "(no pid)"

            repos = collect_hostedby_repos(rec)

            combos_total[combo] += 1
            for r in repos:
                combos_to_repos[combo][r] += 1
    finally:
        fh.close()

    return combos_to_repos, combos_total


def generate_markdown(
    full_input: str, subset_input: str, output_path: str
) -> None:
    total_records_full, repo_counter_full = compute_full_repo_stats(full_input)
    combos_to_repos, combos_total = compute_subset_repo_by_combo(subset_input)

    out = Path(output_path).open("w", encoding="utf-8")

    try:
        # --- Section 1: full harvest ---
        out.write("# Source repositories for CZ datasets (OpenAIRE)\n\n")

        out.write("## 1. All CZ datasets (full harvest)\n\n")
        out.write(f"- Full input file: `{full_input}`\n")
        out.write(f"- Total records: **{total_records_full}**\n\n")

        out.write("| hostedBy name | hostedBy key | records | share [%] |\n")
        out.write("|---------------|-------------|---------|-----------|\n")

        for (key, name), count in repo_counter_full.most_common():
            share = 100.0 * count / total_records_full if total_records_full else 0.0
            out.write(
                f"| {escape_md(name)} | `{escape_md(key)}` | {count} | {share:.2f} |\n"
            )

        out.write("\n\n")

        # --- Section 2: subset by PID scheme combination ---
        out.write("## 2. Non-DOI subset by PID scheme combination\n\n")
        out.write(f"- Subset input file: `{subset_input}`\n\n")

        # Summary of combinations
        out.write("### 2.1 Overview of PID scheme combinations in subset\n\n")
        out.write("| PID schemes combination | records |\n")
        out.write("|-------------------------|---------|\n")
        for combo, total in combos_total.most_common():
            out.write(f"| `{combo}` | {total} |\n")
        out.write("\n\n")

        # Per-combo tables
        out.write("### 2.2 Repositories per PID scheme combination\n\n")

        # combos sorted by total count desc
        for combo, total in combos_total.most_common():
            out.write(f"#### Combination: `{combo}` ({total} records)\n\n")
            repo_counter = combos_to_repos[combo]

            if not repo_counter:
                out.write("_No hostedBy repositories found for this combination._\n\n")
                continue

            out.write("| hostedBy name | hostedBy key | records |\n")
            out.write("|---------------|-------------|---------|\n")

            for (key, name), count in repo_counter.most_common():
                out.write(
                    f"| {escape_md(name)} | `{escape_md(key)}` | {count} |\n"
                )

            out.write("\n")

    finally:
        out.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Summarise source repositories (instances[].hostedBy) "
            "for full CZ dataset harvest and for a subset, "
            "broken down by PID scheme combinations."
        )
    )
    ap.add_argument(
        "--full-input",
        required=True,
        help="JSONL/JSONL.GZ with full CZ harvest (e.g. cz_datasets_countryCZ.jsonl)",
    )
    ap.add_argument(
        "--subset-input",
        required=True,
        help="JSONL/JSONL.GZ with subset of records (e.g. non-DOI PIDs).",
    )
    ap.add_argument(
        "--output-md",
        "-o",
        required=True,
        help="Output Markdown file.",
    )
    args = ap.parse_args()

    generate_markdown(args.full_input, args.subset_input, args.output_md)


if __name__ == "__main__":
    main()

