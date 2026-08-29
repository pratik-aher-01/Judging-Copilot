---
description: Use for all frontend UI and web development in this project. Enforces the Playful Neo-Editorial / Warm Handcrafted SaaS aesthetic (warm oat canvas, serif editorial headlines, vibrant pastel color-blocked cards, hand-drawn doodle accents, and high-contrast pill components).
---

# Frontend Design System & UI Skill: Playful Neo-Editorial (Passionfroot Style)

This skill dictates the exact visual language, component architecture, color tokens, typography, and styling rules for any frontend, landing page, dashboard, or component in this project.

---

## 1. Aesthetic DNA & Philosophy

- **Vibe**: Playful Neo-Editorial / Handcrafted SaaS. Warm, approachable, human, yet razor-sharp and high-converting.
- **Core Visual Pillars**:
  1. **Warm Parchment / Oat Base**: Never sterile pure white (`#FFFFFF`) or cold gray (`#F3F4F6`) backgrounds. Use warm oat/cream (`#FAF7F2`).
  2. **Editorial Serif Headings**: Big, expressive, elegant serif display type paired with crisp geometric sans-serif for UI/body.
  3. **Vibrant Pastel Color Blocking**: High-saturation yet soft pastel hero blocks (Lilac, Mint, Butter Yellow, Sky Blue, Terracotta Coral).
  4. **Handcrafted Doodles & Line Art**: Whimsical vector doodles, speech bubbles, scribble underlines, and playful cartoon mascots.
  5. **Tactile Pill Elements & Sharp Contrast**: Rounded-full pill tags, bold black outlines/contrasts, solid punchy CTA buttons, and elevated white UI mini-mockup cards.

---

## 2. Design Tokens & Color Palette

### CSS Variables (`styles.css` / `:root`)
```css
:root {
  /* Canvas & Ink */
  --paper: #FAF7F2;              /* Warm Oat / Cream main page background */
  --canvas-bg: #FAF7F2;          /* Warm Oat / Cream main page background */
  --canvas-subtle: #F3EFE6;      /* Slightly darker cream for cards/sections */
  --ink-primary: #191817;        /* Deep charcoal/black ink for headings & text */
  --ink-secondary: #5E5B56;      /* Muted warm charcoal for descriptions */
  --ink-muted: #8E8A83;          /* Low-emphasis label text */
  --border-ink: #191817;         /* Crisp black stroke for buttons/badges */
  --border-subtle: #E8E2D6;      /* Soft separator line */

  /* Signature Accent & Pastel Blocks */
  --accent-coral: #F47B56;       /* Terracotta Coral (Hero CTAs, FAQ block, Highlights) */
  --accent-coral-hover: #E46843;
  --pastel-lilac: #D9B8F4;       /* Section Card 1: Workflow / Booking */
  --pastel-mint: #7DD6AC;        /* Section Card 2: Metrics / Showcase */
  --pastel-yellow: #FED766;      /* Section Card 3: Invoicing / Monies */
  --pastel-sky: #9AE4FF;         /* Section Card 4: Analytics / Growth */

  /* UI Card Surfaces */
  --card-white: #FFFFFF;
  --card-shadow: 0 4px 20px rgba(25, 24, 23, 0.06);
  --brutal-shadow: 2px 3px 0px #191817;

  /* Footer */
  --footer-bg: #141413;
  --footer-ink: #FAF7F2;
  --footer-muted: #A3A09A;

  /* Typography */
  --font-serif: 'Fraunces', 'Playfair Display', Georgia, serif;
  --font-sans: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Radius Tokens */
  --radius-full: 9999px;
  --radius-xl: 24px;
  --radius-lg: 16px;
  --radius-md: 10px;
}
```

---

## 3. Typography Rules & Hierarchy

| Role | Font Family | Size / Weight | Line Height | Tracking | Purpose / Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hero Title** | `var(--font-serif)` | 56px - 72px / Bold (700) | 1.08 | `-0.02em` | *"Supercharge your sponsorships"* |
| **Section Title** | `var(--font-serif)` | 36px - 44px / SemiBold (600) | 1.15 | `-0.01em` | *"2x more fast bookings"*, *"Frequently Asked Questions"* |
| **Subheadings** | `var(--font-serif)` | 24px - 28px / Medium (500) | 1.25 | normal | Subsection highlights, block headers |
| **Body Large** | `var(--font-sans)` | 18px - 20px / Regular (400) | 1.6 | normal | Lead paragraphs below headlines |
| **Body Standard** | `var(--font-sans)` | 15px - 16px / Regular (400) | 1.5 | normal | Feature descriptions, bullet points |
| **Pill / Button Text** | `var(--font-sans)` | 14px - 15px / SemiBold (600) | 1.0 | `+0.01em` | *"Get Started"*, *"YouTubers"*, *"Podcasters"* |
| **Micro-Labels & Tags** | `var(--font-mono)` or Sans | 11px - 12px / Bold (700) | 1.0 | `+0.05em` | All-caps status badges, category tags |

---

## 4. Key Component Blueprints

### 4.1. Navigation Bar
- Transparent or frosted oat background (`#FAF7F2`).
- Brand logo on left: Bold serif wordmark in lowercase/titlecase (e.g. `passionfroot` / `judging-copilot`).
- Clean inline nav links with subtle hover underline.
- Right side: Secondary ghost button ("Log in") + Pill CTA button ("Sign up" / "Launch App").

### 4.2. Hero Section & Social Proof Cluster
- Flanked by mini decorative UI tags or doodle illustrations on the left and right.
- Massive centered serif headline with organic line breaks.
- Dual CTA row:
  - **Primary CTA**: Solid Coral (`#F47B56`) pill button, white/charcoal text, smooth hover scale.
  - **Secondary CTA**: Oat/White pill button with 1.5px ink border (`#191817`).
- **Social Proof Floating Avatars**: Horizontal overlapping avatar cluster with pill badges ("Trusted by 10,000+ top creators & judges").

### 4.3. Audience / Category Pill Switcher ("For all creators")
- Terracotta/Coral banner container with rounded top edge.
- Horizontal row of interactive pill tabs (Active tab = solid black background `#191817` with white text; Inactive = white pill with border).
- Nested clean white feature card with side-by-side split:
  - **Left**: Feature bullet list with custom colorful icon checkmarks.
  - **Right**: Grid of creator preview portrait tiles with badges.

### 4.4. The 4 Signature Pastel Block Cards
Stack of 4 full-width or oversized rounded cards (`border-radius: 28px`), each with its own signature personality:
1. **Lilac Block (`#D9B8F4`)**:
   - Focus: Workflow / Speed / Intake.
   - Embed: White floating mini-mockup of an intake form / calendar picker.
2. **Mint Block (`#7DD6AC`)**:
   - Focus: Portfolio / Live Submission Pipeline / Stats.
   - Embed: White floating mini-mockup of charts and project cards.
3. **Butter Yellow Block (`#FED766`)**:
   - Focus: Scoring / Rubrics / Automated Invoicing.
   - Embed: White floating mini-mockup of score breakdowns and payout slips.
4. **Sky Blue Block (`#9AE4FF`)**:
   - Focus: Insights / Leaderboard / Analytics.
   - Embed: White floating mini-mockup of analytics curves and progress bars.

*Note: Inside each pastel card, place a clean white nested card mockup with subtle shadows (`0 8px 30px rgba(0,0,0,0.08)`) and tiny colorful sticker badges.*

### 4.5. Testimonial Quote & 4-Column Feedback Grid
- **Hero Testimonial**:
  - Oversized opening quotation mark `“`.
  - Serif italic/bold quote text (24px).
  - Circular avatar photo accompanied by a hand-drawn doodle speech bubble or arrow.
- **Grid of Review / Tweet Cards**:
  - 4 clean white vertical cards with user handle, avatar, stars, and authentic concise review text.

### 4.6. Frequently Asked Questions (FAQ) Section
- Warm coral background block (`#F47B56`) with rounded corners.
- Left column: Serif heading "Frequently Asked Questions" + quirky character mascot illustration.
- Right column: Stack of clean white accordion cards with plus/minus toggles and smooth disclosure animation.

### 4.7. Bottom Mascot Parade & Dark Editorial Footer
- Playful line-drawing mascot parade (hand-drawn cartoon characters marching along the top border of the footer).
- Final punchy call-to-action block.
- Deep Charcoal/Black Footer (`#141413`):
  - Cream typography, 4 organized link columns (Product, Resources, Company, Legal).
  - Minimalist wordmark and copyright stamp.

---

## 5. Decorative Accents & Hand-Drawn Elements

- **Doodle SVGs**: Use clean 1.5px to 2px black stroke line-art illustrations (stars, squiggles, spirals, arrows pointing to buttons, speech bubbles).
- **Sticker Badges**: Small angled labels (`transform: rotate(-2deg)` or `rotate(3deg)`) with bright background color and 1px dark border.
- **Micro-Interactions**:
  - Buttons have a subtle tactile push (`transform: translateY(-2px)` on hover, `translateY(0)` on active).
  - Cards lift smoothly on hover (`box-shadow: 0 12px 32px rgba(25, 24, 23, 0.09)`).

---

## 6. Strict Do's and Don'ts (Banned Patterns)

- ❌ **NO Pure White / Cool Gray Grids**: Never default to Tailwind `bg-gray-50` or `bg-slate-100`. Always use warm `#FAF7F2`.
- ❌ **NO Boring Standard Sans-Only Typography**: Never use plain Inter/Roboto for all headlines. Headlines MUST use an editorial Serif (`Fraunces` or `Playfair`).
- ❌ **NO Generic Shadcn / Material UI Clones**: No floating generic gray cards with washed-out borders. Cards should be either vibrant pastel blocks or warm oat/white cards with distinct personality.
- ❌ **NO Placeholder Images**: Use real avatar photos, high-fidelity UI vector mockups, or curated SVG line-art illustrations.
- ❌ **NO Tiny Rectangular Sharp Buttons**: Buttons are tactile pills (`border-radius: 9999px`) with bold legible typography.

---

## 7. Reusable HTML & CSS Snippet Starter

```html
<!-- Import Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

<div class="page-canvas">
  <!-- Hero Section -->
  <section class="hero-container">
    <div class="badge-pill">✨ The Next-Gen Judging Co-pilot</div>
    <h1 class="hero-headline">Supercharge your <span class="highlight-serif">evaluations</span></h1>
    <p class="hero-subtext">Automated code reviews, rubric scoring, and duplicate detection wrapped in one delightful workspace.</p>
    
    <div class="cta-group">
      <button class="btn-primary-pill">Get Started Free</button>
      <button class="btn-outline-pill">Watch Demo</button>
    </div>
  </section>

  <!-- Pastel Feature Block -->
  <div class="feature-pastel-card bg-pastel-lilac">
    <div class="feature-text">
      <h2>2x faster scoring</h2>
      <p>Automate rubric calculations and eliminate manual grading bottlenecks.</p>
      <button class="btn-white-pill">Explore Rubrics →</button>
    </div>
    <div class="feature-mockup-card">
      <!-- Mini UI mockup content -->
    </div>
  </div>
</div>
```
