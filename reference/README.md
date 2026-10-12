# reference/ — work-permit sponsor checks

Can this employer hire me on a work permit, and does the salary clear the floor?
Covers the UK, the Netherlands, Spain and Luxembourg.

## Use

```bash
python3 reference/fetch_registers.py                       # refresh UK + NL registers (or: uk | nl)
python3 reference/check_sponsor.py adyen                   # all four countries
python3 reference/check_sponsor.py adyen --nl --salary 55000
python3 reference/check_sponsor.py "amazon" --lu --es --salary 70000
```

`--salary` is annual gross (GBP for the UK, EUR elsewhere). For NL, compare the
salary **excluding** the 8% holiday allowance.

## Countries

| Country | Register? | Route | Annual floor (2026) |
|---|---|---|---|
| UK | yes, GOV.UK licensed sponsors (~143k rows) | Skilled Worker | £41,700, new entrant £33,400 |
| NL | yes, IND recognised sponsors (~13k rows) | Highly Skilled Migrant | €5,942/m (30+), €4,357/m (<30), €3,122/m (after zoekjaar) |
| ES | **no**: any employer up to date with tax/Social Security can file with UGE-CE | HQP or EU Blue Card | €41,356; Blue Card reduced €33,085 |
| LU | **no**: employer declares the vacancy to ADEM | EU Blue Card | €65,652 (from 3 Mar 2026) |

Sources: [GOV.UK register](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers),
[IND register](https://ind.nl/en/public-register-recognised-sponsors/public-register-work),
[IND income requirements](https://ind.nl/en/required-amounts-income-requirements),
[ES Orden PJC/44/2026 summary](https://www.arc-legal.es/en/eu-blue-card-salary-thresholds-updated-for-2026-in-spain/),
[Guichet.lu Blue Card](https://guichet.public.lu/en/entreprises/ressources-humaines/recrutement/ressortissant-pays-tiers/plus-3-mois/salarie-hautement-qualifie.html).
Thresholds change every year: update `RULES` and `RULES_AS_OF` in `check_sponsor.py`.

## What a hit means

Registers list the **legal entity**, not the brand ("Adyen N.V.", "LVMH Services Limited"),
so matching strips legal suffixes and falls back to token overlap. A hit means the company
**can** sponsor, not that it **will** for this role: ask early.

The register CSVs are gitignored (bulky, stale within days). Every check prints the
download date; refresh before a check that matters.
