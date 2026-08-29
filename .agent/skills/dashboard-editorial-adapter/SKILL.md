---
description: Use together with passionfruit-editorial when building the Judging Copilot dashboard specifically. Translates that skill's marketing-page visual language into a working internal tool — no hero, no testimonials, no footer. Load both skills for any dashboard UI work.
---

# Applying passionfruit-editorial to a working dashboard

The base skill (`passionfruit-editorial`) describes a marketing site. This dashboard is **not** a marketing
site — it's an internal working tool an organizer uses to scan verdicts fast. Apply the visual
system (color, type, cards, pills, borders, shadows) from `passionfruit-editorial`, but skip everything that assumes a landing page.

---

## 1. Keep from the Base Skill
- **Paper Background**: `--paper` (`#FAF7F2`) used consistently as the backdrop throughout (do not band full-page rows in different colors like a landing page).
- **Ink & Typography**: Deep ink text/borders (`#191817`), `Fraunces` editorial serif for title/counts + `Plus Jakarta Sans` / `Inter` for functional UI and `JetBrains Mono` for scores/timestamps.
- **Card Style**: Clean white background (`#FFFFFF`), thin ink border (`1px solid #191817`), hard offset shadow (`2px 3px 0px #191817`), `border-radius: 10px` (`rx 10px`).
- **Pill Filters**: Rounded pill tabs (`border-radius: 9999px`) — maps directly onto the flag-status filter rail.
- **Flat Color Fields**: Flat, high-contrast colors, never gradients.
- **Decorative Imperfection**: In tiny doses only (slight rotation on non-functional accent badges/doodles in empty states — never on tables, filters, or drawers).
- **Motion & Accessibility**: Crisp micro-transitions (`150ms ease`), respected `prefers-reduced-motion`.

---

## 2. Skip Entirely (Marketing Elements)
- ❌ Hero sections, marketing pitch headlines, "Supercharge your..."
- ❌ Marketing nav links ("Pricing", "Features", "About")
- ❌ CTA buttons ("Get started free", "Sign up", "Book a demo")
- ❌ Testimonials, social proof quote blocks, review carousels
- ❌ FAQ accordion blocks
- ❌ Multi-column footer link grids and marketing storytelling blocks

---

## 3. Translate, Don't Copy (Dashboard UI Semantics)

### Top Navigation Bar
- Slim, utilitarian top bar:
  - App name in serif (`Judging Copilot`).
  - Small pill badge showing live count of flagged verdicts (e.g. `⚠️ 3 Flagged`).
  - Active submission intake input / status indicator.

### Color as Verdict State (Not Page Rhythm)
- **Mint (`#7DD6AC` / `#80D8B4`)**: Clean / Passed verdict (Score >= threshold, no duplicate).
- **Coral (`#F47B56` / `#EE6C4D`)**: Flagged verdict (Low rubric score, missing criteria, prompt injection).
- **Yellow (`#FED766` / `#FFE277`)**: Duplicate warning / high code similarity detected.
- **Paper (`#FAF7F2`)**: Uniform canvas background across the entire dashboard.

### Real Product Data (No Mockups / No Placeholders)
- This is the real working product. Use actual `Verdict` object fields everywhere:
  - `doc_id` / `id`
  - `repo_url`
  - `score` (e.g. `88/100`)
  - `rubric_breakdown` (criteria: elegance, correctness, novelty, execution)
  - `duplicate_flag` (boolean)
  - `similarity_score` (e.g. `0.12` or `0.87`)
  - `timestamp`
- **Never** use lorem ipsum, never use fake metrics.

### Table Rows & Rubric Drawer
- Table rows use the tactile white card style with ink border and subtle hover state.
- **Do NOT rotate** table rows, filters, or drawer controls. Rotation is strictly reserved for decorative empty-state accents.
- **Illustration Budget**: Exactly 1 small hand-drawn style doodle in the empty state (e.g., `"No verdicts yet — submit a repo URL above"`), never scattered throughout a data table.

---

## 4. Fixed 3-Part Layout Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│ [Judging Copilot]                      [ ⚠️ 3 Flagged ] [ + Submit Repo]│
├──────────────┬──────────────────────────────────────────┬──────────────┤
│ LEFT RAIL    │ MAIN VERDICT TABLE                       │ RIGHT DRAWER │
│ (Filters)    │ (Dense, Scannable, Sortable)             │ (Rubric &    │
│              │                                          │  Reasoning)  │
│ [ All ] (18) │ Repo | Score | Flags | Similarity | Time │ Criteria     │
│ [ Flagged ]3 │ ---------------------------------------- │ Breakdown    │
│ [ Duplicate] │ org/repo1  [92]  [PASS]     0.04    12m  │ Reasoning    │
│ [ Clean ] 14 │ org/repo2  [41]  [FLAG] ⚠️  0.89    1h   │ Gemini Log   │
│              │                                          │              │
└──────────────┴──────────────────────────────────────────┴──────────────┘
```

1. **Left Rail**: Pill filters by flag status (`All`, `Flagged`, `Duplicate`, `Clean`).
2. **Main Canvas**: Verdict table, sortable by score, timestamp, and flag status. Dense and scannable.
3. **Right Drawer**: Rubric breakdown + reasoning + duplicate diffs; opens smoothly on row click.

---

## 5. Non-Negotiable Rules & Anti-Patterns (Merged from Core Dashboard Spec)

### Banned Default Patterns
- ❌ **No Centered Floating White Card on Gray**: Avoid generic AI-generated floating card templates.
- ❌ **No Default Shadcn/Tailwind Palette**: Never default to `indigo-600` on `gray-50`. Use the defined `--paper` and state palette.
- ❌ **No Generic Empty States**: Empty states must be specific: *"No verdicts yet — submit a repo URL above"*.
- ❌ **No Generic Sans-Only Stacks**: Use the paired Serif (`Fraunces`) for headers/counts, Sans for table text, Mono for hashes/scores.
- ❌ **No Icon-in-a-Circle Patterns**: Do not put generic icons in colored circles above every heading.

### Required Rules
- **Color + Shape Together**: Score and flag status must always use color **and** shape/icon together (e.g., `⚠️ Flagged` badge with warning icon + coral bg, `✓ Clean` with check + mint bg)—never color alone.
- **Dense & Scannable**: Optimized for speed of evaluation. Judges need to scan 50+ submissions quickly.
- **Screen Validation Check**: Before finalizing any view, ask: *"Does this look like it was purpose-built for judging hackathon code submissions, or could it be a generic admin template?"* If generic, refactor immediately.
