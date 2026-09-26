# Smart Meter Power Consumption Forecasting — Term Project

## Course context
UNB Data Analytics, Fall 2026. Team term project, 5 biweekly phases (Problem Definition →
Data Collection/Prep → EDA/Feature Engineering → Modeling → Insights/Final Report).
Phase 1 proposal due **Sept 29, 2026**. Full grading breakdown and phase rubrics are in
`docs/spec/` (see Reference docs below) — check them before finalizing any phase deliverable.

Topic #24: **Power Consumption Forecasting Using Smart Meter Data**.

## Dataset
Kaggle "Smart meters in London" (half-hourly household consumption) — **confirmed**: team
agreed, and instructor's "must be messy" requirement is satisfied.

## Problem statement
**Locked**: household usage / bill forecasting. This is a prediction task — regression on
future consumption (and/or projected bill amount), not classification or clustering. Folder
structure and modeling code below assume this.

## Working style / what "done" looks like
This project is also a data-engineering learning exercise, not just a grade target. Priorities,
in order:
1. **Reproducibility** — anyone should be able to re-run the pipeline from raw data to results
   with one command per stage. No manual, unrecorded steps.
2. **Clean project structure** — clear separation of raw data, processing code, and outputs
   (see layout below).
3. **Defensible modeling choices** — every method choice should have a stated reason, not just
   "it worked." Flag assumptions and limitations explicitly in code comments / notebooks.

When implementing something, prefer scripts/modules over one-off notebook cells for anything
that needs to be re-run. Notebooks are fine for exploration; promote reusable logic into `src/`.

## Repo layout
```
data/
  raw/            # untouched source data, never edited in place
  interim/        # partially cleaned intermediate data
  processed/      # analysis-ready datasets
notebooks/        # exploration, EDA, one-off analysis
src/
  data/           # ingestion + cleaning scripts
  features/       # feature engineering
  models/         # training + evaluation code
  viz/            # reusable plotting helpers
reports/
  phase1/ phase2/ ... # phase deliverables (proposal, EDA report, etc.)
docs/
  spec/           # course spec + phase requirement PDFs/notes
```

## Conventions
- Python, standard data stack (pandas, numpy, scikit-learn, matplotlib/seaborn as needed).
- Config (file paths, params) lives in one place, not hardcoded across scripts.
- Commit raw data pointers/scripts, not large raw files, unless the team agrees otherwise.
- Document every cleaning/preprocessing decision (what was dropped/imputed and why) — this is
  an explicit Phase 2 deliverable requirement.

## How to work with me on this
- Explain reasoning, don't just hand over finished code, unless explicitly asked to "just write it."
- Flag anywhere an approach diverges from how this would be done in an industry data
  engineering/analytics setting, and why.
- Check deliverables against the phase rubric before calling something done.
- I have a backend dev background (Java/Spring, SQL) — comfortable with code and databases,
  newer to the applied ML/analytics side, so lean into that gap rather than the coding basics.

## Current status
Phase 1 (problem definition) in progress. Dataset and problem statement (bill forecasting)
are locked. Next: draft the Phase 1 proposal (problem statement, objectives, data source
description, feasibility, scope) — due Sept 29, 2026. No pipeline code yet.