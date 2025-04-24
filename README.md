Quartiles Solver
================
A command‑line helper to crack Apple News+ **Quartiles** puzzles.

Given the 20 letter‑tiles that appear in the daily 4 × 5 grid, this tool
will:

1.  Enumerate every English word that can be formed with 1–4 tiles
    (order matters, tiles may only be used once per word).
2.  Highlight **Quartiles** (4‑tile words worth 8 pts) and attempt to find a
    set of five disjoint Quartiles that collectively use *all* 20 tiles –
    the hidden meta‑solution Apple bakes into each puzzle.
3.  If you have already found some words, you can pass them in so the
    solver only works on the remaining tiles.

Usage
-----
```bash
# basic – paste the 20 tiles in reading order
python quartile_solver.py mil ri teg ty len lan ic thro im py in art fec ally ni tion per ist phi al

# exclude tiles you have already used
python quartile_solver.py --known doublespeak heightened mil ri …
```

The script prints a summary:
* All Quartiles it can see (grouped by the 20‑tile cover if found)
* All other valid words (sorted by length/score)

Requirements
------------
```bash
pip install wordfreq rich
```
`wordfreq` supplies a decent English word list; `rich` is used for pretty
printing. Feel free to swap in a custom dictionary – just replace
`load_wordset()`.
