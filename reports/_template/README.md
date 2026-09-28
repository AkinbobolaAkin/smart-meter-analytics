# Report template

1. New phase: `mkdir reports/phaseN`, copy `_template/main.tex` into it, and create an empty `references.bib`.
2. Set the metadata macros (`\projecttitle`, `\phaselabel`, `\authors`, `\course`, `\reportdate`) at the top of `main.tex`.
3. Build from the phase folder: `latexmk -pdf -outdir=build main.tex` (pdfLaTeX + biber; output in `build/`, gitignored).
4. Clean: `latexmk -C -outdir=build`. Styling lives only in `_template/preamble.tex`; ask before changing it.
5. Overleaf: upload the whole `reports/` folder, set `phaseN/main.tex` as the main document, and choose the pdfLaTeX compiler.
