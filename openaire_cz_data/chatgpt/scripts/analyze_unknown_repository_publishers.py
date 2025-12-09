#!/usr/bin/env python3
"""
Combine Unknown Repository analyses into a single Markdown report:

- At the top, include the full content of unknown_repository_analysis.md
  (or any other analysis Markdown you provide via --analysis-md).

- Then add:
  - breakdown by publisher (from unknown_repository_records.jsonl),
  - detailed per-record table (2 rows per record), sorted by mainTitle:

    1) | mainTitle | mainTitle | publicationDate | publisher | collectedFrom | schemes |
    2) | all URLs as clickable links in column 1 | ...empty columns... |

mainTitle is wrapped at word boundaries so that each line is at most ~60+ chars
(řádek končí za slovem, které poprvé překročí hranici 60 znaků);
line breaks are rendered as <br> in Markdown.

URLs:
- clickable link is [TRUNCATED_TEXT](FULL_URL)
- TRUNCATED_TEXT is shortened to first 60 characters + "..." if longer.
"""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


def wrap_at_word_boundary(text: str, max_len: int = 60) -> str:
    """
    Zalomí text po slovech tak, že:

    - jde po slovech zleva doprava,
    - jakmile délka aktuálního řádku *poprvé* přesáhne max_len díky dalšímu slovu,
      nechá dané slovo na tom řádku a za něj vloží zalomení (\n),
    - poté pokračuje na nový řádek se stejnou logikou.

    Výsledkem je text s \n, které se pak v escape_md převedou na <br>.
    """
    text = text or ""
    words = text.split(" ")
    if not words:
        return text

    lines: List[str] = []
    current_words: List[str] = []
    current_len = 0

    for w in words:
        if not current_words:
            # první slovo na řádku
            current_words.append(w)
            current_len = len(w)
            continue

        # +1 kvůli mezeře
        new_len = current_len + 1 + len(w)

        # pokud jsme zatím pod prahem a tímto slovem ho poprvé překročíme
        if current_len < max_len and new_len > max_len:
            # přidáme slovo, ukončíme řádek
            current_words.append(w)
            current_len = new_len
            lines.append(" ".join(current_words))
            current_words = []
            current_len = 0
        else:
            # jinak slovo jen přidáme na aktuální řádek
            current_words.append(w)
            current_len = new_len

    if current_words:
        lines.append(" ".join(current_words))

    return "\n".join(lines)


def shorten_url_display(url: str, max_len: int = 60) -> str:
    """
    Zkrátí viditelný text odkazu na max_len znaků.
    - pokud je URL kratší nebo rovna max_len, vrátí ji celou
    - jinak vrátí prvních max_len znaků + "..."
    (cílový odkaz v ( ) zůstává vždy plný)
    """
    url = url or ""
    if len(url) <= max_len:
        return url
    return url[:max_len] + "..."


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
    """Return distinct collectedFrom.value (or key) strings, in order of appearance."""
    vals: List[str] = []
    for cf in rec.get("collectedFrom") or []:
        v = (cf.get("value") or "").strip()
        if not v:
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


def generate_markdown(
    input_jsonl: str,
    output_md: str,
    analysis_md: Optional[str] = None,
) -> None:
    # načti záznamy + počty publisherů
    records, publisher_counter = load_records_and_publishers(input_jsonl)

    # seřadit záznamy podle mainTitle (case-insensitive) a v rámci toho podle data
    records.sort(
        key=lambda r: (
            str(r.get("mainTitle") or "").lower(),
            str(r.get("publicationDate") or ""),
        )
    )

    out = Path(output_md).open("w", encoding="utf-8")

    try:
        # 1) Předehra: celý obsah unknown_repository_analysis.md (pokud je k dispozici)
        if analysis_md is not None:
            analysis_path = Path(analysis_md)
            if analysis_path.is_file():
                with analysis_path.open("r", encoding="utf-8") as f:
                    out.write(f.read())
                # oddělíme další část dvěma novými řádky a horizontální čárou
                out.write("\n\n---\n\n")
            else:
                # fallback – kdyby soubor neexistoval, aspoň krátká poznámka
                out.write(
                    f"> **Note:** Analysis file `{analysis_md}` not found; "
                    "publisher breakdown is still generated below.\n\n"
                )

        else:
            # Pokud nebyl předán analysis_md, přidej krátký úvod
            out.write("# Unknown Repository records – extended report\n\n")
            out.write(
                f"- Records JSONL input: `{input_jsonl}`\n"
                f"- Total records: **{len(records)}**\n\n"
            )
            out.write("---\n\n")

        # 2) Breakdown podle publisher
        out.write("## Breakdown by publisher\n\n")
        out.write("| publisher | records |\n")
        out.write("|-----------|---------|\n")
        if publisher_counter:
            for pub, count in publisher_counter.most_common():
                out.write(f"| {escape_md(pub)} | {count} |\n")
        else:
            out.write("| *(none)* | 0 |\n")
        out.write("\n\n")

        # 3) Detailní tabulka záznamů (2 řádky na záznam)
        out.write("## Records (sorted by mainTitle)\n\n")
        out.write(
            "| mainTitle | mainTitle | publicationDate | publisher | collectedFrom | schemes |\n"
        )
        out.write(
            "|-----------|-----------|-----------------|-----------|---------------|---------|\n"
        )

        for rec in records:
            raw_title = rec.get("mainTitle") or ""
            wrapped_title = wrap_at_word_boundary(raw_title, max_len=60)
            title = escape_md(wrapped_title)

            pub_date = escape_md(rec.get("publicationDate"))
            publisher = escape_md(rec.get("publisher") or "")
            cf_vals = collect_collected_from_values(rec)
            cf_str = ", ".join(cf_vals)
            schemes = ", ".join(collect_all_pid_schemes(rec))

            urls = collect_urls(rec)
            if urls:
                url_links: List[str] = []
                for u in urls:
                    display = shorten_url_display(u, max_len=60)
                    display_escaped = escape_md(display)
                    url_links.append(f"[{display_escaped}]({u})")
                urls_md = "<br>".join(url_links)
            else:
                urls_md = ""

            # 1. řádek: metadata (2× mainTitle, jak jsi chtěl)
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
            "Combine unknown_repository_analysis.md and unknown_repository_records.jsonl "
            "into a single Markdown report with publisher breakdown and a detailed table."
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
        "--analysis-md",
        "-a",
        required=False,
        help="Existing Markdown analysis file to prepend "
             "(e.g. unknown_repository_analysis.md).",
    )
    ap.add_argument(
        "--output-md",
        "-o",
        required=True,
        help="Output combined Markdown file.",
    )
    args = ap.parse_args()

    generate_markdown(
        input_jsonl=args.input_jsonl,
        output_md=args.output_md,
        analysis_md=args.analysis_md,
    )


if __name__ == "__main__":
    main()

