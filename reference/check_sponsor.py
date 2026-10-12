#!/usr/bin/env python3
"""Check whether an employer can sponsor a work permit in the UK, NL, ES or LU.

    python3 reference/check_sponsor.py lendable
    python3 reference/check_sponsor.py "booking holdings" --nl
    python3 reference/check_sponsor.py adyen --nl --salary 55000
    python3 reference/check_sponsor.py "amazon" --lu --es --salary 70000

UK and NL publish sponsor registers (download with fetch_registers.py); the
company is looked up by name. Spain and Luxembourg have no register: any
compliant employer can apply, so only the route rules and salary floors are
printed. --salary is annual gross (EUR; GBP for the UK) and is checked against
each country's floor. Thresholds change every year: see RULES_AS_OF.
"""

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES_AS_OF = "2026-10-12"
SUFFIXES = {
    "bv", "nv", "ltd", "limited", "plc", "llp", "llc", "inc", "sa", "sas", "sarl",
    "sl", "slu", "gmbh", "ag", "holding", "holdings", "group", "groep", "operations",
    "services", "international", "nederland", "netherlands", "uk", "europe", "emea",
    "the", "and",
}

# Annual gross floors. Each entry: (label, amount, note).
RULES = {
    "uk": {
        "name": "United Kingdom (Skilled Worker)",
        "register": True,
        "currency": "GBP",
        "floors": [
            ("Skilled Worker, general", 41_700, "or the occupation going rate, whichever is higher"),
            ("Skilled Worker, new entrant", 33_400, "70% of going rate, £33,400 floor; under 26, recent graduate or switching from Student/Graduate visa"),
        ],
        "notes": [
            "Employer must hold a sponsor licence (in the register) AND agree to sponsor this role.",
            "HPI route needs no sponsor but requires a degree from a listed top university within 5 years; check the current HPI list for ESSEC/CentraleSupélec.",
        ],
    },
    "nl": {
        "name": "Netherlands (Highly Skilled Migrant / kennismigrant)",
        "register": True,
        "currency": "EUR",
        "floors": [
            ("HSM, 30 or older (offer excl. 8% holiday pay)", 5_942 * 12, "€5,942/month excl. 8% holiday allowance"),
            ("HSM, under 30", 4_357 * 12, "€4,357/month excl. 8% holiday allowance"),
            ("HSM, reduced (after zoekjaar / recent graduate)", 3_122 * 12, "€3,122/month excl. 8% holiday allowance"),
        ],
        "notes": [
            "Employer must be an IND recognised sponsor (in the register).",
            "Reduced floor: via the orientation year (zoekjaar hoogopgeleiden); eligibility depends on the degree-awarding institution's ranking, check ind.nl.",
        ],
    },
    "es": {
        "name": "Spain (Highly Qualified Professional / EU Blue Card, via UGE-CE)",
        "register": False,
        "currency": "EUR",
        "floors": [
            ("Highly Qualified Professional (Ley 14/2013)", 41_356, "Orden PJC/44/2026"),
            ("EU Blue Card, general", 41_356, "Orden PJC/44/2026"),
            ("EU Blue Card, reduced", 33_085, "shortage occupations / recent graduates, legally defined cases only"),
        ],
        "notes": [
            "No sponsor register or licence: the employer files with UGE-CE and must be up to date with tax and Social Security.",
            "No labour market test for the Blue Card (since 2023). Statutory decision time ~20 working days.",
        ],
    },
    "lu": {
        "name": "Luxembourg (EU Blue Card)",
        "register": False,
        "currency": "EUR",
        "floors": [
            ("EU Blue Card", 65_652, "from 3 March 2026; no reduced floor since June 2024"),
        ],
        "notes": [
            "No sponsor register: the employer declares the vacancy to ADEM; no labour market test for Blue Card hires.",
            "Below the floor: standard salaried-worker permit, which needs an ADEM labour market test (hard for a junior).",
        ],
    },
}


def normalise(name: str) -> str:
    n = name.lower().replace("&", " and ")
    n = re.sub(r"[^a-z0-9 ]+", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def tokens(name: str) -> list[str]:
    return [t for t in normalise(name).split() if t not in SUFFIXES and len(t) > 1]


def load(path: Path):
    if not path.exists():
        return None, None
    meta_path = path.with_suffix(".meta.json")
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    return rows, meta


def search(rows, query: str, name_key: str):
    q_norm, q_tokens = normalise(query), tokens(query)
    exact, partial = [], []
    for row in rows:
        name = (row.get(name_key) or "").strip()
        if not name:
            continue
        n_norm = normalise(name)
        if q_norm and re.search(rf"\b{re.escape(q_norm)}\b", n_norm):
            exact.append(row)
        elif q_tokens and all(t in n_norm.split() for t in q_tokens):
            partial.append(row)
    return exact, partial


def lookup(path: Path, query: str, name_key: str, cols: list[str]) -> None:
    rows, meta = load(path)
    if rows is None:
        print(f"  no data file ({path.name}) -- run: python3 reference/fetch_registers.py")
        return
    print(f"  register: {len(rows):,} entries, downloaded {meta.get('downloaded', '?')}")
    exact, partial = search(rows, query, name_key)
    hits = exact or partial
    if not hits:
        print(f"  NOT FOUND: '{query}' (try the legal entity name, or a shorter query)")
        return
    if not exact:
        print("  no direct match; closest by tokens:")
    for row in hits[:12]:
        print("  - " + " | ".join(str(row.get(c, "")).strip() for c in cols if row.get(c)))
    if len(hits) > 12:
        print(f"  ... and {len(hits) - 12} more")


def salary_check(rule: dict, salary: float) -> None:
    cur = rule["currency"]
    for label, floor, _ in rule["floors"]:
        mark = "OK  " if salary >= floor else "LOW "
        print(f"  {mark}{label}: floor {floor:,.0f} {cur} vs offer {salary:,.0f} {cur}")


def report(code: str, query: str, salary: float | None) -> None:
    rule = RULES[code]
    print(f"\n=== {rule['name']} ===")
    if code == "uk":
        lookup(HERE / "uk-licensed-sponsors.csv", query, "Organisation Name",
               ["Organisation Name", "Town/City", "Type & Rating", "Route"])
    elif code == "nl":
        lookup(HERE / "nl-recognised-sponsors.csv", query, "Organisation Name",
               ["Organisation Name", "KVK number"])
    else:
        print("  no public register: any compliant employer can apply")
    if salary is not None:
        salary_check(rule, salary)
    else:
        for label, floor, note in rule["floors"]:
            print(f"  floor  {label}: {floor:,.0f} {rule['currency']}/yr ({note})")
    for note in rule["notes"]:
        print(f"  note: {note}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    salary = None
    if "--salary" in argv:
        i = argv.index("--salary")
        salary = float(argv[i + 1].replace(",", "").replace("_", ""))
        del argv[i:i + 2]
    flags = {a.lstrip("-") for a in argv if a.startswith("--")}
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    codes = [c for c in RULES if c in flags] or list(RULES)
    print(f"rules as of {RULES_AS_OF} -- re-check thresholds on the official sites before relying on them")
    for code in codes:
        report(code, " ".join(args), salary)
    print("\nA register hit means the company CAN sponsor, not that it WILL for this role.\n")
