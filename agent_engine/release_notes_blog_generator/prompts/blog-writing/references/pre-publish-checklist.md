# Pre-publish checklist

Run this before delivering any post. Report failures rather than shipping past them. After the checklist, score the post on the 100-point QA scorecard in `aspose-article-brief.md` (target 85+, no critical technical error).

## Brief

- [ ] Every row of the article brief was filled before drafting, not guessed
- [ ] The article type matches the feature (not every feature becomes "What is X?")
- [ ] New vs update vs consolidate was decided — this is not a near-duplicate of an existing post

## Answer quality

- [ ] The post answers one clear question, stated in the first two sentences
- [ ] Every H2 is phrased as a question a real user would ask
- [ ] Every section opens with a direct answer to its own heading
- [ ] Key Takeaways sits under the introduction, with 3–6 standalone bullets
- [ ] The most important sentences survive being read out of context
- [ ] The post contains specifics — real numbers, errors, versions, tradeoffs — not only generalities

## Structure and readability

- [ ] Paragraphs are one to three sentences
- [ ] Heading hierarchy is clean: one H1, no skipped levels, no headings used for styling
- [ ] Lists, tables, or callouts break up every long stretch of prose
- [ ] Visual or component roughly every 300–400 words
- [ ] Terminology is consistent throughout, including headings, CTAs, and metadata
- [ ] No keyword stuffing; nothing reads as written for a crawler

## Technical accuracy (developer posts)

- [ ] Every class, method, property, enum, namespace, and package name traces to `docs/`
- [ ] The sample uses the correct Aspose product, and the stated language and namespace
- [ ] Code samples include imports/usings and would compile as written
- [ ] Input and output formats in the code match the article's stated task
- [ ] No invented APIs, no unexplained placeholders, no `// ...` hiding the important part
- [ ] The described output matches what the code actually produces
- [ ] The article does not claim a feature the code does not demonstrate
- [ ] An explicit input/output/product/language block appears near the top of the solution
- [ ] Each important API call is explained (method → action → result), not just pasted
- [ ] Version numbers are stated where behaviour depends on them
- [ ] Error handling and failure modes are covered, not just the happy path
- [ ] Anything unverified is flagged to the user rather than asserted

## Trust signals

- [ ] Author name present and real
- [ ] Publish date set in the site's date format; last-updated / reading-time only if recent posts use those fields
- [ ] Factual claims and data have sources; API claims trace to `docs/`
- [ ] No fabricated credentials, awards, statistics, quotes, or links

## Links and navigation

- [ ] Internal links to parent hub and related posts, with descriptive anchor text
- [ ] Links to product, API, or service pages placed where reader intent shifts
- [ ] No broken or placeholder URLs left in the body
- [ ] Related-content or category module accounted for, if the template uses one

## Conversion

- [ ] Soft CTA near the top
- [ ] Mid-article CTA after the core solution
- [ ] Strongest CTA at the conclusion
- [ ] CTA type matches reader intent — no hard sell on an informational post

## Bundle and metadata

- [ ] Post is a folder containing one `index.md` and one `images/` folder, nothing else
- [ ] Bundle is under `content/blog/`, folder-named like the most recent existing bundle
- [ ] `url` field set and correct — it, not the folder name, is the public permalink
- [ ] Front matter complete, field names copied from a recent existing post — or flagged as unverified if none was readable
- [ ] seoTitle under 60 characters, description 140–160 characters
- [ ] Every image path is bundle-relative (`images/x.png`), never site-absolute (`/images/...`)
- [ ] Every image referenced in front matter or body exists in `images/` — flag any that do not
- [ ] Every image has descriptive alt text
- [ ] Image filenames are descriptive and slug-style
- [ ] FAQ block present in body and mirrored into front matter
- [ ] `index.md` presented first in the reply
- [ ] Structured data (e.g. FAQ schema) added only if it accurately represents the page, not by default

## Delivery note

Alongside the file, tell the user:

- What was restructured, cut, or added, and why
- Anything that still needs a human: missing assets, unverified claims, placeholder links, author details
