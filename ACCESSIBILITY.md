# Accessibility Statement

Tarrant County College and the author are committed to making the
Trailblazer Trek Texas Government modules usable by everyone, including
students who rely on assistive technology. This resource aims to conform to
the **Web Content Accessibility Guidelines (WCAG) 2.1, Level AA**, and to
support obligations under **Section 508** and **Title II of the Americans
with Disabilities Act (ADA)**.

This is a living statement. It describes both what the modules already do
and the work that remains, and it is updated as items are remediated.

## What the modules do today

- Use **semantic HTML headings** in a logical order so screen-reader users
  can navigate by document structure.
- Use a **navy/teal color palette** chosen for readable contrast, and avoid
  conveying meaning through color alone.
- Present each chapter's **review-question answers using the browser's
  native disclosure control** (`<details>`/`<summary>`), which is
  keyboard-operable and announced correctly by assistive technology.
- Provide a dedicated, unscored **Chapter Review & Resources** page with a
  summary, glossary, review questions, critical-thinking prompts, and
  references, so students can study the material in an accessible,
  text-based form.

## Known limitations and roadmap

**Resolved (September 2026): keyboard and screen-reader access to all scored
activities.** Previously the reveal cards and knowledge-check options were
mouse-only `div` elements, which meant a keyboard-only or screen-reader user
could not reveal content, answer questions, or earn points. Every chapter in
this repository now provides:

- **Full keyboard operation.** Reveal cards, knowledge-check options, and the
  home-page navigation cards are reachable with Tab and activated with Enter
  or Space.
- **Correct semantics.** Reveal cards expose `role="button"` with
  `aria-expanded` and `aria-controls`; knowledge checks are labelled groups;
  answered options are marked `aria-disabled` and removed from the tab order,
  so keyboard users cannot re-answer a closed question.
- **Announcements.** Quiz feedback, reflection word counts and feedback,
  section-gate messages, and the running point total are announced politely
  via ARIA live regions.
- **Visible focus.** A high-contrast focus indicator is applied to every
  interactive element, with a `:focus` fallback for older browsers.
- **Accessible names.** Reflection textareas carry an `aria-label` derived
  from their prompt (a placeholder alone is not an accessible name), and the
  progress bar exposes `role="progressbar"` with a live `aria-valuenow`.
- **Page language.** Every chapter declares `lang="en"`.
- **Reduced motion.** Animations are suppressed for users who set the
  `prefers-reduced-motion` preference.

These behaviours are verified by an automated test (jsdom) that simulates a
keyboard-only user revealing a card and answering a knowledge check, and
confirms points are actually awarded. All 16 chapters pass.

**Still outstanding:**

1. **Verification with real assistive technology.** The automated tests
   confirm semantics and keyboard operation, but the modules have not yet been
   tested end-to-end with JAWS, NVDA, or VoiceOver by a screen-reader user.
2. **Colour-contrast audit.** The navy/teal palette was chosen for readability
   but has not been formally measured against the 4.5:1 (text) and 3:1
   (non-text) WCAG thresholds in every context.
3. **Alternative text review.** Every image has descriptive alt text; the
   descriptions would still benefit from review by a subject-matter expert for
   accuracy and concision.
4. **A formal WCAG 2.1 AA conformance report (VPAT/ACR).**

## Reporting a barrier / getting help

If you encounter an accessibility barrier in these materials, please contact
the author (Professor Jared Alan Stewart) or open an issue on the project's
GitHub repository. TCC students may also contact **TCC Student Accessibility
Resources**. Please include the chapter, the section, your browser and
assistive technology, and a description of the problem so it can be fixed
quickly.

*Last reviewed: 2026.*
