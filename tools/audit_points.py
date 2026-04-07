#!/usr/bin/env python3
"""
TCC Trailblazer Trek — Point Total Audit

Walks every Chapter*.html file in the current directory and verifies that the
declared maximum score equals the sum of points actually earnable from reveal
cards and knowledge-check correct answers (plus any per-section completion
bonuses).

Exits non-zero if any chapter is mismatched, so this script is safe to run
in CI to block bad commits.

Handles all 8 scoring patterns currently in use across the Trailblazer Trek
modules:
  A: gameState ... maxScore: NNN
  B: const/var/let maxPoints = NNN
  C: sectionPoints: { N: { earned: 0, max: NNN } }   (+ optional +50 bonus)
  D: const/var/let totalPoints = NNN
  E: gameState ... maxPoints: NNN
  F: const/var/let totalPossiblePoints = NNN
  G: gameState ... totalPossible: NNN
  H: maxSectionPoints: {...} + completionBonus: {...}
"""
from __future__ import annotations

import re
import os
import sys
import glob
from typing import Optional, Tuple, Dict, List


def compute_actual_earnable(html):
    """Sum reveal-card points + best-correct-answer points per question.
    Returns (total, info_dict)."""
    reveals = re.findall(
        r"revealCard\([^,]+,\s*'([^']+)',\s*(\d+)", html
    )
    quizzes = re.findall(
        r"handleAnswer\([^,]+,\s*(true|false),\s*'([^']+)',\s*(\d+)", html
    )

    # For each question id, take the maximum point value across its options
    # (this is the points the student earns by answering correctly).
    q_max: dict[str, int] = {}
    for ok, qid, pts in quizzes:
        q_max[qid] = max(q_max.get(qid, 0), int(pts))

    reveal_total = sum(int(p) for _, p in reveals)
    quiz_total = sum(q_max.values())
    return reveal_total + quiz_total, {
        "n_reveals": len(reveals),
        "reveal_total": reveal_total,
        "n_questions": len(q_max),
        "quiz_total": quiz_total,
    }


def detect_declared(html):
    """Detect the chapter's declared max-score pattern.
    Returns (pattern_letter, declared_total, completion_bonus_total)."""
    bonus_total = 0

    # Pattern C: sectionPoints: { N: { earned, max: NNN } }
    if re.search(r"\d+\s*:\s*\{\s*earned\s*:\s*\d+\s*,\s*max\s*:\s*\d+", html):
        section_maxes = [
            int(m.group(1))
            for m in re.finditer(r"max\s*:\s*(\d+)\s*\}", html)
        ]
        # Heuristic: per-section +50 completion bonus
        if re.search(r"sectionPoints\[\w+\]\.earned\s*\+=\s*50", html):
            bonus_total = 50 * len(section_maxes)
        return "C", sum(section_maxes), bonus_total

    # Pattern H: maxSectionPoints + completionBonus
    if re.search(r"maxSectionPoints\s*:\s*\{", html):
        msp_block = re.search(
            r"maxSectionPoints\s*:\s*\{([^}]*)\}", html
        ).group(1)
        declared = sum(
            int(m.group(2)) for m in re.finditer(r"(\d+)\s*:\s*(\d+)", msp_block)
        )
        cb_match = re.search(r"completionBonus\s*:\s*\{([^}]*)\}", html)
        if cb_match:
            bonus_total = sum(
                int(m.group(2))
                for m in re.finditer(r"(\d+)\s*:\s*(\d+)", cb_match.group(1))
            )
        return "H", declared, bonus_total

    # Single-denominator patterns
    single_patterns = [
        ("A", r"maxScore\s*:\s*(\d+)"),
        ("E", r"maxPoints\s*:\s*(\d+)"),
        ("B", r"(?:const|var|let)\s+maxPoints\s*=\s*(\d+)"),
        ("D", r"(?:const|var|let)\s+totalPoints\s*=\s*(\d+)"),
        ("F", r"(?:const|var|let)\s+totalPossiblePoints\s*=\s*(\d+)"),
        ("G", r"totalPossible\s*:\s*(\d+)"),
    ]
    for letter, pat in single_patterns:
        m = re.search(pat, html)
        if m:
            return letter, int(m.group(1)), 0

    return None, None, 0


def audit_file(path):
    html = open(path, encoding="utf-8").read()
    pattern, declared, bonus = detect_declared(html)
    actual, info = compute_actual_earnable(html)
    actual_with_bonus = actual + bonus
    return {
        "file": os.path.basename(path),
        "pattern": pattern,
        "declared": declared,
        "actual": actual_with_bonus,
        "diff": (actual_with_bonus - declared) if declared is not None else None,
        **info,
    }


def main(argv):
    chapter_dir = argv[1] if len(argv) > 1 else "."
    files = sorted(glob.glob(os.path.join(chapter_dir, "Chapter*.html")))
    if not files:
        print(f"No Chapter*.html files found in {chapter_dir}", file=sys.stderr)
        return 2

    print(f"TCC Trailblazer Trek — Point Audit")
    print(f"Scanning: {os.path.abspath(chapter_dir)}")
    print(f"Found {len(files)} chapter file(s)\n")
    print(
        f"  {'Chapter':50s} {'Pat':4s} {'Declared':>9s} {'Actual':>8s} {'Diff':>7s}"
    )
    print("  " + "-" * 84)

    failures = []
    unrecognized = []
    for f in files:
        r = audit_file(f)
        name = r["file"][:50]
        if r["pattern"] is None:
            print(f"  {name:50s} ???     —         —        —    NO PATTERN DETECTED")
            unrecognized.append(r)
            continue
        diff_str = f"{r['diff']:+d}" if r["diff"] != 0 else "0"
        flag = "" if r["diff"] == 0 else "  ❌ MISMATCH"
        print(
            f"  {name:50s} {r['pattern']:4s} {r['declared']:>9d} {r['actual']:>8d} {diff_str:>7s}{flag}"
        )
        if r["diff"] != 0:
            failures.append(r)

    print()
    if failures or unrecognized:
        if failures:
            print(f"❌ {len(failures)} chapter(s) have mismatched point totals:")
            for r in failures:
                print(
                    f"   • {r['file']}: declared={r['declared']}, "
                    f"actual={r['actual']} (off by {r['diff']:+d})"
                )
        if unrecognized:
            print(
                f"❌ {len(unrecognized)} chapter(s) have an unrecognized scoring pattern:"
            )
            for r in unrecognized:
                print(f"   • {r['file']}")
        print(
            "\nThese mismatches will cause students to receive incorrect "
            "percentages and grades."
        )
        return 1

    print(f"✓ All {len(files)} chapters balanced. Point totals look good.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
