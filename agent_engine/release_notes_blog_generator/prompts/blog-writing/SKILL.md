---
name: blog-writing
description: Write, restructure, or review blog posts so they work for human readers and get quoted by AI search (ChatGPT, Claude, Gemini, Perplexity, Google AI Overviews). Use this whenever the user asks for a blog post, article, guide, tutorial, product introduction, or post outline, and also when they ask to rewrite, edit, expand, restructure, add FAQs, write a meta description, or make existing copy "rank better" or "work with AI search". Covers the pre-writing article brief, choosing the right article type from an SDK feature, answer-first structure, extractable phrasing, E-E-A-T signals, code-quality gates, internal linking, CTAs, Hugo front matter, the pre-publish checklist, and the QA scorecard. Use it even for short posts, even for developer documentation-style content, and even when the user never mentions SEO or AI search.
---

# Blog writing

Blog posts now have two audiences that have to be satisfied at the same time.

**Human readers** want clarity, depth, and low friction. They scan before they read.

**AI systems** — search engines and assistants — do not rank whole pages the way they used to. They scan, extract, summarise, and cite. They lift short, self-contained passages that answer a specific question. Content they cannot cleanly extract simply does not appear.

The good news is that these audiences want mostly the same thing: a clear question, an immediate answer, and evidence. Structure serves the machine. Substance serves the human. A post needs both — formulaic content that any model could have generated gets ignored by readers, and unstructured content that cannot be extracted gets ignored by machines.

The central rule for this project: **search intent + working technical solution + original explanation + verifiable evidence + clear structure.** A technically incorrect post never ships, however good its SEO.

## Workflow

Work through these in order. Skip steps only when the user is asking for one narrow piece (e.g. just a meta description).

SEO and LLM optimisation are not a final polish pass. They start in the brief, in step 1.

### 1. Write the article brief

Before outlining, fill in the brief. If any row is blank or guessed, stop and get it from the user or the docs — do not draft around a gap.

| Field | What to define |
|---|---|
| Primary task | The one thing the developer wants to accomplish, phrased as a task ("Convert CDR to PNG"), not a topic ("CDR files") |
| Target audience | .NET / Java / Python / C++ developer, etc. — one primary language |
| Product + SDK | Exact Aspose product and platform, e.g. Aspose.Imaging for .NET |
| Input → output | The file or data that goes in, and the result that comes out |
| Search intent | Definition, how-to, comparison, troubleshooting, or decision-making |
| Primary question + answer | The exact question a reader would type, and its definitive one-to-two-sentence answer |
| Related questions | 3–8 questions users actually ask around this task |
| Unique value | What this post explains, demonstrates, or simplifies better than the ten posts that already exist |
| Evidence | The specific docs pages, API reference entries, examples, or tests that back every claim |
| New / update / consolidate | Whether this is a new post, an update to an existing one, or a consolidation of near-duplicates |

The primary answer becomes the intro, the Key Takeaways, and the extractable snippet. If it is hard to write, the post is not ready to draft. See `references/aspose-article-brief.md` for the brief template, the keyword map, and the feature-to-article matrix.

### 1b. Choose the article type from the feature

Do not turn every SDK feature into a "What is X?" post. Match the feature to the developer's task:

| Feature / capability | Article type | Working title shape |
|---|---|---|
| New API method | How-to | "How to Add Recipients to an Email in .NET" |
| New supported format | How-to / feature | "How to Read <format> Files in .NET" |
| New conversion capability | Tutorial | "Convert <A> to <B> in .NET" |
| API behaviour change | Technical update | "What Changed in <feature> and How to Use It" |
| Performance improvement | Technical guide | "How to Speed Up <operation> in .NET" |
| Bug fix / known limitation | Troubleshooting | "How to Fix <error> in .NET" |

"How to Add Recipients to an Email in .NET" beats "What Is Email Recipient Management?" — it matches the task and forces an implementation-focused post.

### 2. Build the content map

Outline before drafting. The map should include:

- H2s phrased as the questions real users ask
- H3s that break each subtopic down
- Where examples, definitions, and code go
- Where components break up density (lists, tables, callouts, comparison blocks)
- Visual opportunities roughly every 300–400 words
- Internal links, with the anchor text planned
- CTA placement matched to the reader's intent at that point

Confirm the map with the user before drafting anything long. Restructuring a finished draft is expensive; restructuring an outline is free.

### 3. Draft answer-first sections

Every section opens with one or two sentences that answer its heading and make sense in isolation. Detail, nuance, and caveats come after. This is the single highest-leverage habit in the whole workflow — see `references/structure-and-style.md` for the patterns and before/after examples.

### 4. Add what only this author can add

Generic how-to content is exactly what models generate for free, so it has no reason to be cited or read. Reach for specifics:

- Real error messages, real version numbers, real configuration
- Concrete tradeoffs, including where the recommended approach is the wrong choice
- Benchmarks, measurements, case details, or first-hand experience
- Opinionated recommendations, stated plainly

One specific, lived detail is worth a page of well-organised generality.

### 5. Add trust and structure signals

Author name and role, publish date, updated date, reading time, credentials or awards where they exist. Internal links to the parent topic and related posts. Correct heading hierarchy (H1 → H2 → H3, one H1, never skipped for styling). Details are in `references/structure-and-style.md`.

### 6. Produce the publishable file

Deliver a complete file with front matter filled in, not a chat-window draft. Read `references/hugo-front-matter.md` before writing it. Flag any asset that does not exist yet, such as a cover image path.

### 7. Run the checklist and score the post

Read `references/pre-publish-checklist.md` and verify each item before delivering. Then run the 100-point QA scorecard in `references/aspose-article-brief.md`. Aim for 85+ with no critical technical error. Report anything that fails and cannot be fixed, rather than quietly shipping it.

## The rules that do most of the work

Apply these to every post, whether drafting fresh or editing existing copy:

- **Question-format H2s.** "How does gold purity affect resale value?" beats "Gold purity". Headings are how machines read intent.
- **Direct answer in the first one or two sentences of every section.** No build-up, no throat-clearing.
- **One to three sentences per paragraph.** New idea, new paragraph.
- **Every key point stands alone.** If a sentence only makes sense with the paragraph above it, it will not be quoted.
- **Key Takeaways sits directly under the introduction.** Three to six short, self-contained statements.
- **Consistent terminology.** Pick one term per concept and keep it across headings, body, CTAs, and metadata. Synonym-swapping confuses semantic classification.
- **No keyword stuffing.** Repetition damages clarity and reads as low quality to both audiences. Clarity is the ranking strategy now.
- **Word count is not a target.** A well-structured 1,200-word post beats a padded 3,000-word one.
- **One strong page per task, not many keyword variants.** "AI automation tools", "best AI automation tools", and "AI automation tools for startups" as separate near-identical pages is sprawl, not coverage. When a new topic overlaps an existing post, decide in the brief: new post, update, or consolidate.
- **Separate facts from opinions.** Mark which claims are measured, which are documented, and which are your recommendation. Date any claim that changes over time (version numbers, format support, pricing).
- **No AI bait.** Never add text telling AI systems to cite the page, and never embed hidden instructions. Search engines treat this as abuse.

## Technical and developer posts

This project's content is largely developer-facing, so accuracy outranks polish. Technical correctness is the non-negotiable quality gate.

- Never invent API surface. Class names, method signatures, namespaces, package names, and options must come from the source material in `docs/`. If something is unverified, flag it rather than guessing.
- Code samples should compile as written, with usings/imports included and versions pinned where behaviour depends on them.
- State the input, output, product, and language explicitly at the top of the solution section, e.g. `Input: input.cdr` · `Output: output.png` · `Library: Aspose.Imaging for .NET` · `Language: C#`. This is the fact an AI system most often needs to extract.
- Explain what each important API call does (method → action → result) rather than pasting code and moving on. Never invent an explanation to sound authoritative.
- Add at least one contribution beyond the docs: a common mistake, a real use case, an API-choice rationale, a format limitation, a "what this means for your app" note, or a tested example that is not a copy of the documentation sample.
- Lead with the pain point the developer already has, then introduce the solution. Developers skip product framing that arrives before the problem.
- Keep the introduction free of API surface. No class, method, interface, property, or namespace names before the first H2. The intro states the problem, who it affects, and what the post delivers; the body carries the API detail. Answer-first still applies — say what the guide enables, not how the internals are wired.
- Cover the failure modes: real exception names, lifetime and dependency-injection gotchas, thread-safety, resource disposal, and what to do when the happy path breaks.
- Keep structural and editorial changes separate from factual claims. When rewriting someone else's technical post, restructure freely but leave the technical assertions intact, and say explicitly what changed and why.

### Code-quality gate

Before delivering, verify every item:

- The sample uses the correct Aspose product and the article's stated language and namespace.
- Every API method, property, and enum used exists in that SDK, checked against `docs/`.
- Imports/usings are included and the sample would compile as written.
- Input and output formats match the article's stated task.
- No invented APIs, no unexplained placeholders, no `// ...` standing in for the part that matters.
- The described output matches what the code actually produces.
- The article does not claim a feature the code does not demonstrate.
- Version numbers are stated wherever behaviour depends on them.

## Output conventions

Posts are Hugo page bundles. Each post is a folder containing exactly one `index.md` and an `images/` folder — nothing else:

```
<post-slug>/
├── index.md
└── images/
    ├── cover.png
    └── <figure>.png
```

- Build the whole folder, not a loose markdown file. Create `images/` even when the assets do not exist yet, so the structure is ready to drop files into.
- Reference every image with a bundle-relative path (`images/cover.png`), never a site-absolute one (`/images/blog/...`). Absolute paths break page bundles.
- Create the bundle under `content/blog/`. Match the folder-naming of the most recent existing bundle; this repo uses a `YYYY-MM-DD-<slug>` prefix, and the public URL is set by the `url` field in front matter, not the folder name.
- The `url` field is the real permalink. Get it right the first time — changing it after publish breaks inbound links.
- Present `index.md` first in your reply.
- Include the FAQ block in the body and in front matter if the site's template consumes it both ways — check `references/hugo-front-matter.md`.
- Alongside the file, give a short summary of the editorial decisions made: what was restructured, what was cut, what was added, and anything that still needs a human (missing assets, unverified claims, links that need real URLs).

## Reference files

- `references/aspose-article-brief.md` — the article brief template, keyword map, feature-to-article matrix, input/output declaration, and the 100-point QA scorecard. Read at step 1, before outlining.
- `references/structure-and-style.md` — extraction patterns, heading and paragraph craft, components, internal linking, CTA placement, E-E-A-T signals, with before/after examples. Read when drafting or restructuring a full post.
- `references/hugo-front-matter.md` — front matter template, FAQ block, metadata and schema rules. Read before producing the publishable file.
- `references/pre-publish-checklist.md` — the final gate. Read before delivering anything.
- `references/editorial-review-prompt.md` — the SEO + LLM editorial review to run against a finished or third-party draft. Use for review-only requests.
