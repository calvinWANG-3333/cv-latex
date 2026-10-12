# cv-latex

Ruihang (Calvin) Wang's CV in LaTeX, plus one analysis per job description.

## Layout

| Path | What |
|---|---|
| `resume_base.tex` | the base CV (one source of truth; old wording is kept commented out rather than deleted) |
| `jd-analyses/` | one Markdown file per JD: fit, tailoring instructions, cover-letter angle, prep gaps, raw JD (`_TEMPLATE.md`) |
| `reference/` | work-permit sponsor checks for UK, NL, ES, LU (see `reference/README.md`) |
| `build/`, `output/` | compiled PDFs (gitignored) |

Tailored versions for a role family live on their own branch (e.g. `variant-bi`, `variant-ae`).

## Build

```bash
latexmk resume_base.tex        # -> build/resume_base.pdf
```

Needs a TeX distribution (MacTeX / TeX Live) with `pdflatex` and `latexmk`.
