# Phase 1: project proposal

LaTeX source for the Phase 1 deliverable (2–3 page proposal, due Sep 29, 2026).

- `proposal.tex`: the proposal. Its headings match the five components in the Phase 1 brief.
- `smartmeter-report.cls`: all styling (colours, title block, headers, tables, callouts).
- `references.bib`: cited sources (biblatex + biber, author–year).
- `figures/`: images, referenced as `\includegraphics{name}`.

## Building

Needs `latexmk` and `biber` (TeX Live or MiKTeX), or upload this folder to Overleaf.

```bash
cd reports/phase1
latexmk proposal.tex      # PDF lands in build/
latexmk -c                # remove auxiliary files
```

## Conventions

- Mark unfinished text with `\placeholder{...}`; it shows in orange. For the submitted build use
  `\documentclass[final]{smartmeter-report}`, which turns any leftover placeholder into an error.
- Tables: `\smrows` before the table for striped rows; `\headrow \hd{A} & \hd{B} \\` for the header.
- Callouts: `summarybox`, `keyfinding`.
- Inline: `\code{file_or_column}`, `\kwh`, `\kwhhh`, `\num{167817021}`.
- Before submitting, check against the Phase 1 rubric: 2–3 pages excluding references,
  team names present, all sources cited, confirmed vs. planned data access distinguished.
