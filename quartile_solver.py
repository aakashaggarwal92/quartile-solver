#!/usr/bin/env python3
"""
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
"""
from __future__ import annotations

import argparse
import itertools
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

try:
    from wordfreq import zipf_frequency, top_n_list
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "wordfreq is required – run `pip install wordfreq rich`"
    ) from exc

try:
    from rich import print
    from rich.console import Console
    from rich.table import Table
except ImportError:
    # Fall back to the built‑in print if rich isn’t available
    rich_available = False
else:
    rich_available = True

console = Console() if rich_available else None

###############################################################################
# Dictionary helpers
###############################################################################

WORDSET_PATH = Path(__file__).with_suffix(".wordset")  # optional cached list


def build_wordset(min_zipf: float = 3.5) -> Set[str]:
    """Return a set of reasonably common words.

    `wordfreq.top_n_list` is scored by Zipf frequency. 3.5 ≈ appears once in
    3–10 million words – tweak if you want a larger/smaller lexicon.
    """
    words: List[str] = top_n_list("en", n_top=120_000, ranker="zipf")
    return {w.lower() for w in words if zipf_frequency(w, "en") >= min_zipf}


def load_wordset() -> Set[str]:
    """Load (or build & cache) the word list."""
    if WORDSET_PATH.exists():
        return {w.strip() for w in WORDSET_PATH.read_text().splitlines() if w}

    wordset = build_wordset()
    WORDSET_PATH.write_text("\n".join(sorted(wordset)))
    return wordset


###############################################################################
# Core combinatorics
###############################################################################

Tile = str
Word = str
Combination = Tuple[int, ...]  # tuple of tile indices used in order


def generate_candidates(
    tiles: Sequence[Tile],
    wordset: Set[str],
    max_tiles: int = 4,
) -> List[Tuple[Combination, Word]]:
    """Return [(combo, word)] for every valid word from ≤ ``max_tiles`` tiles."""
    candidates: List[Tuple[Combination, Word]] = []
    indices = range(len(tiles))

    # length‑1 combos first to help short‑circuit impossible searches later
    for r in range(1, max_tiles + 1):
        for combo in itertools.permutations(indices, r):
            word = "".join(tiles[i] for i in combo)
            if word in wordset:
                candidates.append((combo, word))
    return candidates


###############################################################################
# Finding the hidden 5 Quartiles (a perfect cover)
###############################################################################

def find_perfect_quartiles(
    tiles: Sequence[Tile],
    quartile_candidates: List[Tuple[Combination, Word]],
) -> List[List[Tuple[Combination, Word]]]:
    """Return every way to cover *all* tiles with 5 disjoint 4‑tile words."""

    solutions: List[List[Tuple[Combination, Word]]] = []
    used = [False] * len(tiles)

    def backtrack(
        start: int, stack: List[Tuple[Combination, Word]],
    ) -> None:
        if len(stack) == 5:
            # Have we consumed every tile exactly once?
            if all(used):
                solutions.append(stack.copy())
            return

        for i in range(start, len(quartile_candidates)):
            combo, word = quartile_candidates[i]
            if any(used[idx] for idx in combo):
                continue  # overlaps – skip

            # choose
            for idx in combo:
                used[idx] = True
            stack.append((combo, word))

            # explore deeper (always pick next candidate > i to avoid dupes)
            backtrack(i + 1, stack)

            # unchoose
            stack.pop()
            for idx in combo:
                used[idx] = False

    backtrack(0, [])
    return solutions


###############################################################################
# Pretty printing helpers
###############################################################################

def print_solutions(
    tiles: Sequence[Tile],
    perfect_solutions: List[List[Tuple[Combination, Word]]],
    other_quartiles: List[Tuple[Combination, Word]],
    other_words: List[Tuple[Combination, Word]],
):
    if rich_available:
        table = Table(title="Quartile solutions", show_lines=True)
        table.add_column("#", justify="right")
        table.add_column("Quartiles (use every tile once)")
        for i, sol in enumerate(perfect_solutions, 1):
            phrase = "  •  ".join(word for _, word in sol)
            table.add_row(f"{i}", phrase)
        console.print(table)

        if other_quartiles:
            console.print("[bold]Other 4‑tile words:[/bold]", 
                          ", ".join(word for _, word in other_quartiles))
        if other_words:
            console.print("[bold]Additional words:[/bold]", 
                          ", ".join(word for _, word in other_words))
    else:
        print("Quartile solutions:\n===============")
        for i, sol in enumerate(perfect_solutions, 1):
            phrase = "  •  ".join(word for _, word in sol)
            print(f"{i}. {phrase}")
        if other_quartiles:
            print("\nOther 4‑tile words:")
            print(", ".join(word for _, word in other_quartiles))
        if other_words:
            print("\nAdditional words:")
            print(", ".join(word for _, word in other_words))


###############################################################################
# CLI entrypoint
###############################################################################

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Solve Apple News+ Quartiles puzzles.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """Examples:
              python quartile_solver.py mil ri teg ty len lan ic thro …
              python quartile_solver.py --known doublespeak heightened …
            """,
        ),
    )

    parser.add_argument(
        "tiles",
        nargs="+",
        help="The 20 tiles, in any order (case‑insensitive).",
    )
    parser.add_argument(
        "--known",
        nargs="*",
        default=[],
        help="Words you have already found – their tiles will be ignored.",
    )
    parser.add_argument(
        "--all", action="store_true", help="Show every valid 1‑4 tile word."
    )
    return parser.parse_args()


def strip_known_tiles(tiles: List[Tile], known_words: Iterable[str]) -> List[Tile]:
    """Remove tiles used in *all* known_words (best‑effort)."""
    remaining = tiles.copy()
    for word in known_words:
        word = word.lower()
        # greedy match – try to peel off a tile from the left until the word is gone
        i = 0
        while i < len(remaining) and word:
            t = remaining[i]
            if word.startswith(t):
                word = word[len(t) :]
                remaining.pop(i)
            else:
                i += 1
        if word:
            # Did not fully match – give up & keep original tiles so we don't break things
            return tiles
    return remaining


def main() -> None:
    args = parse_args()
    tiles = [t.lower() for t in args.tiles]

    if len(tiles) != 20:
        raise SystemExit("Quartiles puzzles always have exactly 20 tiles.")

    tiles = strip_known_tiles(tiles, args.known)

    wordset = load_wordset()
    candidates = generate_candidates(tiles, wordset)

    quartiles = [(c, w) for c, w in candidates if len(c) == 4]
    others = [(c, w) for c, w in candidates if len(c) < 4]

    perfect = find_perfect_quartiles(tiles, quartiles)

    # sort other quartiles by length then by word
    quartiles_sorted = sorted(
        quartiles, key=lambda cw: (-len(cw[1]), cw[1])
    )
    others_sorted = sorted(
        others, key=lambda cw: (-len(cw[1]), cw[1])
    )

    print_solutions(tiles, perfect, quartiles_sorted, others_sorted if args.all else [])


if __name__ == "__main__":
    main()
