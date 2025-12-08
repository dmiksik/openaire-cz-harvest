#!/usr/bin/env python3
"""
Harvest all OpenAIRE Graph research products of type=dataset and countryCode=CZ
via the Graph v2 API and store them as JSON Lines (one JSON per line).

Usage examples:

  # prostý JSONL
  python harvest_openaire_cz_datasets.py --output cz_datasets_countryCZ.jsonl

  # gzip-comprimovaný JSONL
  python harvest_openaire_cz_datasets.py --output cz_datasets_countryCZ.jsonl.gz --gzip

Parametry type a countryCode jsou ve skriptu defaultně nastavené na:
  type=dataset
  countryCode=CZ

Skript stránkuje přes `cursor` tak dlouho, dokud API vrací výsledky.
"""

import argparse
import json
import sys
import time
from typing import Optional

import requests

BASE_URL = "https://api.openaire.eu/graph/v2/researchProducts"


def harvest_datasets_country_cz(
    output_path: str,
    gzip_output: bool = False,
    page_size: int = 100,
    max_retries: int = 5,
    retry_backoff: float = 5.0,
) -> int:
    """
    Stáhne všechny researchProducts s type=dataset a countryCode=CZ
    a uloží je jako JSONL (případně gzipovaný JSONL).

    Vrací počet stažených záznamů.
    """
    if page_size <= 0 or page_size > 100:
        raise ValueError("page_size musí být v rozmezí 1–100 (limit OpenAIRE API).")

    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            # trochu slušnosti vůči API, ať je vidět, co to je
            "User-Agent": "cz-harvest-script/1.0 (contact: your-email@example.com)",
        }
    )

    # základní parametry – filtr na datasets z CZ
    base_params = {
        "type": "dataset",
        "countryCode": "CZ",
    }

    # výstupní soubor (plain nebo gzip)
    if gzip_output:
        import gzip

        out_fh = gzip.open(output_path, "wt", encoding="utf-8")
    else:
        out_fh = open(output_path, "w", encoding="utf-8")

    cursor: Optional[str] = "*"
    total = 0

    try:
        while cursor:
            params = dict(base_params)
            params["cursor"] = cursor
            params["pageSize"] = page_size

            data = None
            for attempt in range(1, max_retries + 1):
                try:
                    resp = session.get(BASE_URL, params=params, timeout=60)
                    if resp.status_code >= 500 or resp.status_code == 429:
                        # server error nebo rate-limit → zkusíme znovu
                        sys.stderr.write(
                            f"[warn] HTTP {resp.status_code}, attempt {attempt}/{max_retries}, "
                            f"waiting {retry_backoff} s...\n"
                        )
                        sys.stderr.flush()
                        time.sleep(retry_backoff)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except requests.RequestException as e:
                    sys.stderr.write(
                        f"[warn] Request error on attempt {attempt}/{max_retries}: {e}\n"
                    )
                    sys.stderr.flush()
                    if attempt == max_retries:
                        raise
                    time.sleep(retry_backoff)

            if data is None:
                # nemělo by nastat, ale pro jistotu
                sys.stderr.write("[error] API nevrátilo žádná data.\n")
                break

            results = data.get("results", [])
            if not results:
                sys.stderr.write("[info] Žádné další výsledky, končím.\n")
                break

            for rp in results:
                # zapíšeme celý objekt tak, jak přišel z API
                out_fh.write(json.dumps(rp, ensure_ascii=False))
                out_fh.write("\n")
            out_fh.flush()

            batch_count = len(results)
            total += batch_count

            header = data.get("header", {})
            next_cursor = header.get("nextCursor")

            sys.stderr.write(
                f"[info] Staženo {batch_count} záznamů v této stránce, celkem {total}.\n"
            )
            sys.stderr.flush()

            # ochrana proti „zacyklení“ – kdyby API vracelo stále stejný cursor
            if not next_cursor or next_cursor == cursor:
                sys.stderr.write(
                    "[info] nextCursor není k dispozici nebo je stejný jako aktuální, končím.\n"
                )
                break

            cursor = next_cursor

    finally:
        out_fh.close()
        session.close()

    return total


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Sklidí všechny OpenAIRE Graph v2 researchProducts "
            "s type=dataset a countryCode=CZ a uloží je jako JSONL."
        )
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Výstupní soubor (např. cz_datasets_countryCZ.jsonl nebo .jsonl.gz)",
    )
    parser.add_argument(
        "--gzip",
        action="store_true",
        help="Pokud je nastaveno, výstup bude gzipovaný (.gz).",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Počet záznamů na stránku (1–100, default 100).",
    )
    args = parser.parse_args()

    total = harvest_datasets_country_cz(
        output_path=args.output,
        gzip_output=args.gzip,
        page_size=args.page_size,
    )

    sys.stderr.write(f"[done] Celkem staženo {total} datasetů.\n")
    sys.stderr.flush()


if __name__ == "__main__":
    main()

