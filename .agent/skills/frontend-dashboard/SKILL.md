---
description: Use for any UI work — the organizer dashboard showing verdicts, flags, and scores. Prevents default AI-generated UI patterns.
---

# Frontend design rules — organizer dashboard

This is a judging dashboard, not a generic admin panel. It should look like a
tool someone deliberately designed for reading verdicts fast, not a scaffolded
CRUD template.

## Banned by default (these are what "generic AI UI" means here)
- No centered white card floating on a gray page with a soft shadow.
- No default shadcn/Tailwind palette (indigo-600 primary, gray-50 background)
  used unmodified. Pick an actual palette — 1 accent color tied to the verdict
  states (pass / flagged / duplicate), everything else neutral ink/paper tones.
- No lorem-ipsum-shaped empty states. Every empty state describes what will
  appear here specifically ("No verdicts yet — submit a repo URL above").
- No icon-in-a-circle-above-a-heading pattern repeated for every section.
- No generic sans-serif default font stack left untouched — pick one
  typeface pairing and commit to it (e.g. a monospace for scores/data, a
  humanist sans for everything else).

## Required
- Verdict list is the primary view — dense, scannable, sortable by score or
  flag status. This is a working tool, not a landing page.
- Score and flag status use color + shape together (not color alone) — e.g.
  a small icon or badge shape, not just a colored dot.
- Real data shapes only: use the actual Verdict object fields
  (repo_url, score, rubric_breakdown, duplicate_flag, similarity_score,
  timestamp) in every mock/example — never invented placeholder fields.
- One deliberate layout decision stated up front before generating: e.g.
  "left rail = filter by flag status, main = verdict table, right drawer =
  rubric breakdown on row click." Don't let the agent default to a
  three-equal-columns grid.

## Before finalizing any screen
Ask: does this look like it was designed for judging code submissions
specifically, or could this exact layout be relabeled for any other app?
If the second is true, redo it.
