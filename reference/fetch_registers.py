#!/usr/bin/env python3
"""Download the UK and NL sponsor registers into reference/ as CSVs.

Spain and Luxembourg publish no sponsor register; their rules live in check_sponsor.py.

UK: GOV.UK publishes the Worker and Temporary Worker register as a CSV whose
    asset URL changes on every refresh, so the link is scraped from the
    publication page rather than hard-coded.
NL: the IND public register is a server-rendered HTML table (Organisation, KVK),
    so it is parsed straight out of the page.

Both write a sibling .meta.json recording the source URL and download date --
a stale register gives confident wrong answers, so every check reports the date.

    python3 reference/fetch_registers.py [uk|nl]
"""

import csv
import html
import json
import re
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
UK_PAGE = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
NL_PAGE = "https://ind.nl/en/public-register-recognised-sponsors/public-register-work"
UA = {"User-Agent": "Mozilla/5.0 (cv-latex sponsor-check)"}


def ssl_context() -> ssl.SSLContext:
    # python.org builds on macOS ship without CA certs; fall back to the system bundle.
    ctx = ssl.create_default_context()
    if not ctx.get_ca_certs() and Path("/etc/ssl/cert.pem").exists():
        ctx = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return ctx


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120, context=ssl_context()) as r:
        return r.read().decode("utf-8", errors="replace")


def write_meta(path: Path, source: str, rows: int, note: str = "") -> None:
    meta = {
        "source": source,
        "downloaded": date.today().isoformat(),
        "rows": rows,
    }
    if note:
        meta["note"] = note
    path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2) + "\n")


def fetch_uk() -> None:
    page = get(UK_PAGE)
    links = re.findall(
        r'https://assets\.publishing\.service\.gov\.uk/media/[^"]+\.csv', page
    )
    if not links:
        sys.exit("UK: no CSV link found on the publication page -- layout may have changed")
    url = links[0]
    body = get(url)
    out = HERE / "uk-licensed-sponsors.csv"
    out.write_text(body)
    rows = max(sum(1 for _ in body.splitlines()) - 1, 0)
    write_meta(out, url, rows, "Register says a company CAN sponsor, not that it will for a given role.")
    print(f"UK  {rows:>7,} rows -> {out.name}")


def fetch_nl() -> None:
    page = get(NL_PAGE)
    # rows look like: <tr><th scope="row">Name</th><td>KVK</td></tr>
    pairs = re.findall(
        r'<tr><th scope="row">(.*?)</th><td>(.*?)</td></tr>', page, flags=re.S
    )
    if not pairs:
        sys.exit("NL: no table rows found -- the IND page layout may have changed")
    out = HERE / "nl-recognised-sponsors.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Organisation Name", "KVK number"])
        for name, kvk in pairs:
            name = html.unescape(re.sub(r"<[^>]+>", "", name)).replace('"', "").strip()
            kvk = html.unescape(re.sub(r"<[^>]+>", "", kvk)).strip()
            w.writerow([name, kvk])
    write_meta(out, NL_PAGE, len(pairs), "Labour/HSM register. Recognition != willingness to sponsor.")
    print(f"NL  {len(pairs):>7,} rows -> {out.name}")


if __name__ == "__main__":
    which = sys.argv[1].lower() if len(sys.argv) > 1 else "both"
    if which in ("uk", "both"):
        fetch_uk()
    if which in ("nl", "both"):
        fetch_nl()
