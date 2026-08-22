#!/usr/bin/env python3
"""
TCC Trailblazer Trek — Chapter Feature Parity Audit

Companion to audit_points.py. That script checks the arithmetic; this one
checks that every chapter actually ships the student- and instructor-facing
machinery, so a chapter can't silently lose a feature the others have.

Checks performed on every Chapter*.html in the target directory:

  1. PRINT BUTTON      A window.print() control exists on the report page.
                       (Chapter 2 shipped without one until Aug 2026.)

  2. INTEGRITY ANCHOR  The report page carries an id/class that
                       findReportContainer() in the injected extensions block
                       can actually resolve. If it can't, injectIntegrityHash()
                       returns early and the PDF prints with NO integrity code
                       — silently. Chapters 1 and 2 used id="page-report",
                       which was not in the probe list until Aug 2026.

  3. PROBE LIST        findReportContainer()'s own id list is a superset of the
                       anchors actually in use across the corpus, so adding a
                       chapter with a known-good anchor can't regress.

  4. TITLE VERIFIABLE  document.title matches one of the variants that
                       tools/integrity_verifier.html reconstructs. The title is
                       part of the hash payload, so a mismatch means every PDF
                       from that chapter fails verification. Chapter 6 carried
                       a " (Complete Edition)" suffix the verifier didn't know.

  5. REFLECTION RENDER The chapter prints reflections into the report by some
                       means — either the shared renderReflectionReport() or a
                       chapter-native renderer writing into the report page.

  6. NAME RESOLVABLE   getStudentName()'s probe list can find a name field, so
                       the hash payload isn't built from an empty name.

  7. SECTION PARITY    Reflection count equals section count (a section with no
                       reflection can never be completed).

Exits non-zero on any failure, so it is safe to run in CI.
"""
from __future__ import annotations

import glob
import os
import re
import sys

# Probe lists mirrored from the injected extensions block. Keep in sync.
REPORT_CONTAINER_IDS = [
    "reportPage", "page-report", "section-report",
    "reportSection", "completionReport", "report",
]
REPORT_CONTAINER_CLASSES = ["report-page", "report", "completion-report"]
STUDENT_NAME_IDS = ["studentName", "studentNameInput", "reportName", "nameInput", "name"]

VERIFIER = os.path.join("tools", "integrity_verifier.html")


def chapter_number(path):
    m = re.search(r"Chapter (\d+)", os.path.basename(path))
    return int(m.group(1)) if m else 0


def has_id(html, el_id):
    return re.search(r'id\s*=\s*"%s"' % re.escape(el_id), html) is not None


def has_class(html, cls):
    for attr in re.findall(r'class\s*=\s*"([^"]*)"', html):
        if cls in attr.split():
            return True
    return False


def doc_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def verifier_titles(root):
    """Rebuild every title string the verifier will try, exactly as it does."""
    path = os.path.join(root, VERIFIER)
    if not os.path.exists(path):
        return None
    v = open(path, encoding="utf-8").read()
    out = set()
    for var, kind in (("CHAPTER_BASES_FED", "Federal"), ("CHAPTER_BASES_TX", "Texas")):
        m = re.search(var + r"\s*=\s*\[(.*?)\];", v, re.S)
        if not m:
            continue
        bases = re.findall(r'"([^"]+)"', m.group(1))
        # Suffixes appended after "... Government Trailblazer Trek" in expandVariants
        suffixes = set(re.findall(
            r"base \+ ' - (?:TCC|Tarrant County College) ' \+ kind"
            r" \+ ' Government Trailblazer Trek([^']*)'", v))
        suffixes.add("")
        for b in bases:
            for prefix in ("TCC", "Tarrant County College"):
                for suf in suffixes:
                    out.add("%s - %s %s Government Trailblazer Trek%s" % (b, prefix, kind, suf))
    return out


def audit_file(path, titles):
    html = open(path, encoding="utf-8").read()
    n = chapter_number(path)
    problems = []

    # 1. print button
    if "window.print()" not in html:
        problems.append("no window.print() control — students cannot download the report PDF")

    # 2. integrity anchor resolvable
    anchor = next((i for i in REPORT_CONTAINER_IDS if has_id(html, i)), None)
    if anchor is None:
        anchor = next((c for c in REPORT_CONTAINER_CLASSES if has_class(html, c)), None)
    if anchor is None:
        problems.append(
            "report page has no id/class that findReportContainer() can resolve — "
            "the integrity code will never be injected")

    # 3. this file's own probe list covers the corpus-wide anchor set
    m = re.search(r"function findReportContainer\s*\(\s*\)\s*\{.*?var ids = \[([^\]]*)\]",
                  html, re.S)
    if m:
        declared = set(re.findall(r"'([^']+)'", m.group(1)))
        missing = [i for i in REPORT_CONTAINER_IDS if i not in declared]
        if missing:
            problems.append("findReportContainer() probe list is missing: %s" % ", ".join(missing))

    # 4. title verifiable
    t = doc_title(html)
    if titles is not None and t not in titles:
        problems.append(
            "document.title is not a string the verifier reconstructs, so every PDF "
            "from this chapter will fail verification: %r" % t)

    # 5. reflections reach the report
    shared = "function renderReflectionReport" in html
    native = re.search(r"getElementById\('(reflectionReportList|studentReflectionsReport)'\)", html)
    if not (shared or native):
        problems.append("reflections are never rendered into the completion report")

    # 6. name resolvable
    if not any(has_id(html, i) for i in STUDENT_NAME_IDS):
        problems.append("getStudentName() cannot find a name field — hash payload would be nameless")

    # 7. section parity
    reflections = {int(x) for x in re.findall(r'id="reflectionInput(\d+)"', html)}
    sections = {int(x) for x in re.findall(r'id="(?:page-)?[Ss]ection[-_]?(\d+)"', html)}
    if sections and reflections != sections:
        problems.append("section/reflection mismatch: sections %s vs reflections %s"
                        % (sorted(sections), sorted(reflections)))

    return n, problems


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    root = os.path.abspath(root)
    files = sorted(glob.glob(os.path.join(root, "Chapter*.html")), key=chapter_number)

    print("TCC Trailblazer Trek — Feature Parity Audit")
    print("Scanning: %s" % root)
    if not files:
        print("No chapter files found.")
        return 1
    print("Found %d chapter file(s)\n" % len(files))

    titles = verifier_titles(root)
    if titles is None:
        print("  note: %s not found — skipping the title-verifiability check\n" % VERIFIER)

    failures = 0
    for path in files:
        n, problems = audit_file(path, titles)
        if problems:
            failures += 1
            print("  ✗ Chapter %s" % n)
            for p in problems:
                print("      - %s" % p)
        else:
            print("  ✓ Chapter %s" % n)

    print()
    if failures:
        print("✗ %d of %d chapter(s) have feature gaps." % (failures, len(files)))
        return 1
    print("✓ All %d chapters have full feature parity." % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
