#!/usr/bin/env python3
import csv
import time
import argparse
from pathlib import Path
import requests

def norm_doi(s: str) -> str:
    s = (s or "").strip().lower()
    for pref in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
        if s.startswith(pref):
            s = s[len(pref):]
    if s.startswith("doi:"):
        s = s[4:]
    return s.strip()

def read_input_dois(path: Path, col: str = "doi_norm") -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        dois = []
        for row in r:
            v = row.get(col) or row.get("doi") or ""
            v = norm_doi(v)
            if v:
                dois.append(v)
        return sorted(set(dois))

def read_done(out_path: Path) -> dict[str, int]:
    if not out_path.exists():
        return {}
    done = {}
    with out_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            d = norm_doi(row.get("doi_norm",""))
            if not d:
                continue
            try:
                done[d] = int(row.get("http_status",""))
            except:
                done[d] = 0
    return done

def append_row(out_path: Path, row: dict):
    exists = out_path.exists()
    with out_path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["doi_norm","http_status"])
        if not exists:
            w.writeheader()
        w.writerow(row)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--sleep", type=float, default=0.25)
    ap.add_argument("--sleep-404", type=float, default=None)  # pokud chceš jiné, jinak použije --sleep
    ap.add_argument("--sleep-429", type=float, default=2.5)
    ap.add_argument("--timeout", type=float, default=20.0)
    args = ap.parse_args()

    inp = Path(args.input)
    out = Path(args.output)

    dois = read_input_dois(inp, col="doi_norm")
    done = read_done(out)

    todo = [d for d in dois if d not in done]
    print(f"Vstupních DOIs: {len(dois)}")
    print(f"Již hotovo: {len(done)}")
    print(f"Zbývá: {len(todo)}")

    sess = requests.Session()
    headers = {"accept": "application/vnd.api+json"}

    for i, doi in enumerate(todo, start=1):
        url = f"https://api.datacite.org/dois/{doi}"
        print(f"[{i}/{len(todo)}] GET {url}")
        status = 0
        try:
            resp = sess.get(url, headers=headers, timeout=args.timeout)
            status = resp.status_code
            print(f"  -> HTTP {status}")
        except Exception as e:
            print(f"  -> ERROR {e}")
            status = 0

        append_row(out, {"doi_norm": doi, "http_status": status})

        # sleep vždy (i po 404), 429 delší
        if status == 429:
            time.sleep(args.sleep_429)
        elif status in (404, 410) and args.sleep_404 is not None:
            time.sleep(args.sleep_404)
        else:
            time.sleep(args.sleep)

if __name__ == "__main__":
    main()

