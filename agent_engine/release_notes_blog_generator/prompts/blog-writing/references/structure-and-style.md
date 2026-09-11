# Structure and style reference

Contents:

1. How AI systems decide what to quote
2. Headings
3. Answer-first sections
4. Extractable sentences
5. Key Takeaways
6. Components and visuals
7. Internal linking
8. E-E-A-T and trust signals
9. CTA placement
10. FAQ sections
11. Common failure modes

---

## 1. How AI systems decide what to quote

Six factors, in rough order of impact:

- **Directness.** Content that answers immediately gets extracted. Long build-ups get skipped.
- **Structural clarity.** Clean H2/H3 hierarchy, logical flow, generous spacing. Long undifferentiated text blocks perform badly.
- **Semantic depth.** Comprehensive coverage of a topic and its subtopics, with relationships between concepts made explicit and internal links connecting related pages.
- **Trust signals.** Author identity, credentials, publish and update dates, references, data, brand reputation.
- **Machine-friendly formatting.** Lists, numbered steps, tables, definitions, short paragraphs.
- **Standalone answers.** Models rarely lift long paragraphs. They lift single sentences that survive removal from their context.

Everything below is a consequence of these six.

---

## 2. Headings

Write H2s as the question the reader is actually asking.

**Weak:** `## Internal linking`
**Strong:** `## How does internal linking affect AI visibility?`

Question headings signal intent to the model and orient the human reader in one line.

Useful transitional H3s inside a section: `Why this matters`, `How this works`, `Example`, `Common mistakes to avoid`, `When not to use this`.

Hierarchy rules:

- One H1 per page, which is the title.
- Never skip levels (H2 → H4).
- Never pick a heading level for its font size. Use the level that reflects the structure.

---

## 3. Answer-first sections

Open every section with one or two sentences that answer the heading completely, then expand.

**Before:**

> Internal linking has been a topic of much discussion in SEO circles over the years, and opinions vary widely on how much it really matters. Some practitioners argue that it is overrated, while others build entire strategies around it. To understand the debate, it helps to look at how crawlers traverse a site...

**After:**

> Internal linking helps AI systems understand topical relationships by mapping how pages connect across a site. Sites with dense, purposeful internal links are read as authoritative on a topic; isolated pages are read as one-offs.
>
> The mechanism is straightforward. Crawlers traverse...

The second version can be lifted verbatim into an AI answer. The first cannot.

---

## 4. Extractable sentences

An extractable sentence is complete on its own. Test it by deleting everything around it — if the meaning survives, it works.

**Not extractable:** "This is why it matters so much for the reasons described above."
**Extractable:** "Key Takeaways sections improve AI visibility because they provide summarised insights that can be extracted independently."

Habits that produce extractable prose:

- One idea per sentence.
- Lead with the conclusion, not the reasoning.
- Name the subject instead of using "this", "that", or "it" to point at the previous sentence.
- Drop qualifiers and filler ("it is worth noting that", "in many cases", "generally speaking").
- Replace abstractions with specifics. "Internal linking is important" says nothing; "internal linking maps how pages connect across a site, which is how models infer topical authority" says something.

---

## 5. Key Takeaways

Place directly beneath the introduction, before the first H2.

- Three to six bullets.
- Each bullet is one sentence and makes sense in isolation.
- Each states an insight, not a table-of-contents entry.

**Weak bullet:** "We'll cover internal linking and schema."
**Strong bullet:** "Question-based headings with an immediate answer beneath them are the single strongest driver of AI citation."

This block does double duty: it is a ready-made summary for models and a decision aid for readers choosing whether to keep reading. Draft it during planning, not at the end — writing it early forces the argument into focus.

---

## 6. Components and visuals

Break density on purpose. Components signal importance to readers and structure to models.

- Bullet lists for parallel items
- Numbered steps for sequences
- Tables for comparisons and API surface
- Callout or highlight boxes for definitions and warnings
- Pull quotes for the one sentence you most want quoted
- Mini info cards for statistics
- Two-column or side-by-side blocks for pros and cons

Visuals roughly every 300–400 words. They do not need to be elaborate — a diagram, a screenshot, or a labelled code output is enough. They reduce scroll fatigue and help models detect topic boundaries.

Spacing matters too: consistent padding above H2s, separators between major sections, generous whitespace around long passages.

---

## 7. Internal linking

Plan links before drafting, not after publishing.

Link to:

- Related posts in the same topic cluster (semantic depth)
- The parent hub or category page (hierarchy)
- Deeper guides that expand a concept mentioned in passing
- Product, service, or API reference pages, at the point where reader intent shifts from learning to doing

Write descriptive anchor text that names the destination topic. Avoid "click here" and avoid stuffing the target keyword into every anchor.

Supporting structures: breadcrumbs (make page hierarchy explicit), category modules and related-article blocks at the end of posts, and a scroll-to-top control on long pages.

---

## 8. E-E-A-T and trust signals

Include on every informational post, using whatever front-matter fields the recent posts actually use:

- Author name (or brand) and, where a field exists, role or professional context
- Credentials, relevant experience, awards, or recognitions where they genuinely exist
- Publish date; last-updated date only if a recent post carries the field
- Estimated reading time only if the theme renders it
- References or data sources for factual claims (link into `docs/` for API claims)

Never fabricate any of these. Invented credentials or dates are worse than none. If the user has not supplied an author, leave a clearly marked placeholder and say so on delivery.

Freshness matters: update evergreen informational posts at least annually, and more often for regulated, financial, security, or fast-moving technical topics where a stale version number misleads the reader.

---

## 9. CTA placement

Three positions, escalating with engagement:

- **Near the top** — soft and exploratory. "Explore related insights", "See how this works in practice". Sits well beneath the intro or Key Takeaways.
- **Mid-content** — after the reader has absorbed the core solution. This is often the strongest-performing position because the reader is invested.
- **Conclusion** — the strongest, most action-oriented CTA.

Match CTA type to intent:

| Reader intent | CTA style |
|---|---|
| Informational | "Read the full guide", "Download the checklist", "See related topics" |
| Problem-solving | "Compare your options", "See how this applies to your stack" |
| High commercial | "Book a consultation", "Request a quote", "Start a free trial" |

An aggressive sales CTA on an informational post creates friction and costs trust. Keep CTAs contextual and useful.

---

## 10. FAQ sections

An FAQ block near the end captures the adjacent questions the main body did not cover, and each Q/A pair is natively extractable.

- Five to eight questions.
- Each question phrased the way a user would actually ask it.
- Each answer two to four sentences, self-contained, answering in the first sentence.
- No question that duplicates an H2 already in the post.
- Mirror the questions into front matter if the site template renders FAQ schema.

---

## 11. Common failure modes

| Symptom | Fix |
|---|---|
| Sections open with context and background | Move the answer to sentence one |
| Headings are noun phrases | Rewrite as user questions |
| Paragraphs run five-plus sentences | Split at every new idea |
| Key points rely on "this" and "that" | Name the subject explicitly |
| Terminology drifts between synonyms | Pick one term and enforce it |
| Same keyword repeated to hit density | Delete the repetitions; clarity outranks density |
| Wall of text with no components | Add lists, tables, callouts, visuals |
| Generic advice any model could write | Add real errors, numbers, tradeoffs, opinions |
| Post ends with no next step | Add a CTA matched to reader intent |
