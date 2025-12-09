#!/usr/bin/env python3
"""
Analyze records whose instances[].hostedBy is 'Unknown Repository'
in the CZ datasets harvest.

Outputs:
- JSONL subset with all such records
- Markdown summary with:
  - counts and share
  - breakdown by collectedFrom and sources
  - breakdown by URL hostname (from instances[].urls)
"""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


UNKNOWN_REPO_KEY = "openaire____::55045bd2a65019fd8e6741a755395c8c"


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


def is_unknown_repo_instance(inst: Dict) -> bool:
    """Return True if this instance is hosted by 'Unknown Repository' in OpenAIRE."""
    hb = inst.get("hostedBy") or {}
    key = (hb.get("key") or "").strip()
    val = (hb.get("value") or "").strip().lower()

    if key == UNKNOWN_REPO_KEY:
        return True
    if "unknown repository" in val:
        return True
    return False


def record_has_unknown_repo(rec: Dict) -> bool:
    for inst in rec.get("instances") or []:
        if is_unknown_repo_instance(inst):
            return True
    return False


def collect_hostnames(rec: Dict) -> List[str]:
    """Collect hostnames from instances[].urls."""
    hostnames: List[str] = []
    for inst in rec.get("instances") or []:
        for u in inst.get("urls") or []:
            u = str(u).strip()
            if not u:
                continue
            parsed = urlparse(u)
            host = parsed.netloc or ""
            host = host.strip().lower()
            if not host:
                continue
            hostnames.append(host)

    # unique, preserving order
    seen = set()
    unique: List[str] = []
    for h in hostnames:
        if h not in seen:
            seen.add(h)
            unique.append(h)
    return unique


def generate_report(input_path: str, out_md: str, out_jsonl: str) -> None:
    total_records = 0
    unknown_records = 0

    by_collected_from: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    by_hostname: Counter[str] = Counter()

    # open outputs
    subset_fh = Path(out_jsonl).open("w", encoding="utf-8")

    fh = open_maybe_gzip(input_path, "rt", encoding="utf-8")
    try:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total_records += 1
            rec = json.loads(line)

            if not record_has_unknown_repo(rec):
                continue

            unknown_records += 1

            # write to subset JSONL
            subset_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

            # collectedFrom (record level)
            for cf in rec.get("collectedFrom") or []:
                val = (cf.get("value") or "").strip()
                if val:
                    by_collected_from[val] += 1

            # sources (record level)
            for src in rec.get("sources") or []:
                s = (src or "").strip()
                if s:
                    by_source[s] += 1

            # hostnames from URLs
            for host in collect_hostnames(rec):
                by_hostname[host] += 1

    finally:
        fh.close()
        subset_fh.close()

    # write markdown
    out = Path(out_md).open("w", encoding="utf-8")
    try:
        out.write("# Records with 'Unknown Repository' as hostedBy\n\n")
        out.write(f"- Input file: `{input_path}`\n")
        out.write(f"- Total CZ dataset records: **{total_records}**\n")
        out.write(
            f"- Records with `Unknown Repository`: **{unknown_records}** "
            f"({(100.0 * unknown_records / total_records if total_records else 0.0):.2f} %)\n"
        )
        out.write(f"- Subset JSONL written to: `{out_jsonl}`\n\n")

        # collectedFrom
        out.write("## Breakdown by `collectedFrom.value`\n\n")
        out.write("| collectedFrom value | records |\n")
        out.write("|---------------------|---------|\n")
        if by_collected_from:
            for val, count in by_collected_from.most_common():
                out.write(f"| {escape_md(val)} | {count} |\n")
        else:
            out.write("| *(none)* | 0 |\n")
        out.write("\n\n")

        # sources
        out.write("## Breakdown by `sources`\n\n")
        out.write("| source | records |\n")
        out.write("|--------|---------|\n")
        if by_source:
            for val, count in by_source.most_common():
                out.write(f"| {escape_md(val)} | {count} |\n")
        else:
            out.write("| *(none)* | 0 |\n")
        out.write("\n\n")

        # hostnames
        out.write("## Breakdown by URL hostname (instances[].urls)\n\n")
        out.write("| hostname | records |\n")
        out.write("|----------|---------|\n")
        if by_hostname:
            for host, count in by_hostname.most_common():
                out.write(f"| {escape_md(host)} | {count} |\n")
        else:
            out.write("| *(none)* | 0 |\n")
        out.write("\n")
    finally:
        out.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Analyze CZ dataset records that have instances[].hostedBy = 'Unknown Repository'."
        )
    )
    ap.add_argument(
        "--input",
        "-i",
        required=True,
        help="JSONL/JSONL.GZ with full CZ dataset harvest "
             "(e.g. openaire_cz_data/chatgpt/cz_datasets_countryCZ.jsonl)",
    )
    ap.add_argument(
        "--output-md",
        "-o",
        required=True,
        help="Output Markdown report file.",
    )
    ap.add_argument(
        "--output-jsonl",
        required=True,
        help="Output JSONL subset with only 'Unknown Repository' records.",
    )
    args = ap.parse_args()

    generate_report(args.input, args.output_md, args.output_jsonl)


if __name__ == "__main__":
    main()

