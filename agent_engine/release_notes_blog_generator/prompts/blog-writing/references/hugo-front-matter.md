# Hugo front matter and metadata

Posts ship as Hugo page bundles with complete front matter. A draft without front matter is not a deliverable.

## Bundle structure

```
<post-slug>/
├── index.md
└── images/
    ├── cover.png
    └── <figure>.png
```

One `index.md` per folder, one `images/` folder beside it. No other files, no subfolders under `images/`.

This repo names bundle folders with a `YYYY-MM-DD-<slug>` prefix (e.g. `2026-09-02-monitor-project-load-progress-net`). The public URL is set by the `url` field in front matter, not the folder name. Copy the folder-naming style from the most recent existing bundle in `content/blog/`. The `<slug>` part should be short, lowercase, hyphenated, and match the question the post answers.

Because this is a leaf bundle, every image path in front matter and in the body is relative to the bundle:

```markdown
![Tokenizer output compared across three models](images/tokenizer-comparison.png)
```

Site-absolute paths like `/images/blog/cover.png` do not resolve inside a bundle. Use them only if the repo demonstrably stores blog images outside the bundle, which contradicts this structure and should be raised with the user rather than assumed.

Name image files descriptively and in the same slug style as the folder (`di-lifetime-error.png`, not `screenshot-3.png`). Every image needs alt text that describes the content, not the filename.

## Before writing front matter

Field names vary between Hugo sites, and this site has no archetypes to copy from. Take the field set from the most recently published post instead: read the `index.md` of an existing bundle in the blog content directory and match its fields exactly — same names, same order, same casing, same date format.

Prefer a recent post over an old one, since older posts may use fields the theme no longer reads. If the posts disagree with each other, follow the newest and mention the inconsistency.

Use the template below only when no existing post is readable, and say on delivery that the field names are unverified. It mirrors the field set of the most recent bundle at the time of writing (`content/blog/2026-09-02-monitor-project-load-progress-net/index.md`) — still confirm against the newest post.

## Template

```yaml
---
title: 'How to <Do the Thing> in <Context>'
seoTitle: <Under 60 characters, answers the query directly>
description: <140-160 characters. States the answer, not a slogan.>
date: Wed, 02 Sep 2026 04:07:37 +0000
draft: true
url: /<product>/<short-slug>/
author: <Name>
summary: <2-3 sentences. The pain point, the solution, and what the reader will be able to do.>
tags: ['<specific tag>', '<specific tag>', '<specific tag>', '<specific tag>']
categories: ["<Product Family>"]
showtoc: true
cover:
  image: images/<slug>.jpg
  alt: 'How to <Do the Thing> in <Context>'
  caption: 'How to <Do the Thing> in <Context>'
  hidden: false
steps:
- <Imperative step, one line.>
- <Imperative step, one line.>
faqs:
- q: <Question as a user would ask it?>
  a: <Two to four self-contained sentences.>
- q: <...>
  a: <...>
---
```

Notes on this site's fields: `date` is an RFC-1123 string, not a bare date. There is no `lastmod`, `authorRole`, or `readingTime` field — do not invent them. `tags` is an inline list; `cover` is a map (not a flat `image`); FAQ entries use `q`/`a`, not `question`/`answer`. `steps` is a site-specific list of imperative one-liners for the how-to schema. New posts start `draft: true`.

## Field rules

**title** — The human-facing headline. Descriptive beats clever. "Ten must-sees from my Europe trip" earns the click that "My trip to Europe" does not, but never let the hook outrun what the post delivers.

**seoTitle** — Under 60 characters. Answers the core query in plain words. No vague slogans, no creative phrasing that hides the topic.

**description** — 140–160 characters. State the answer and set expectations. This is often what a model reads first to decide whether the page is relevant, so it should read like a direct answer rather than a teaser.

**url** — The real permalink in this repo, since the folder name carries a date prefix. Short, lowercase, hyphenated, keyword-bearing but not stuffed, matching the primary question. Copy the shape from a recent post (e.g. `/tasks/monitor-project-load-progress-net/`). Once published, do not change it without a redirect.

**date** — RFC-1123 string (`Wed, 02 Sep 2026 04:07:37 +0000`), matching the format of recent posts. This site has no `lastmod` field; if a recent post has since added one, follow the newest post and mention it.

**draft** — New posts are `draft: true` until reviewed. Only set `draft: false` when the user says to publish.

**author** — Required as an E-E-A-T signal. Never invent a name or credentials. Default to the user's own name only when they are the author. This site has no `authorRole` or `readingTime` field — do not add them unless a recent post does.

**summary** — Two to three sentences: the pain point, the solution, and what the reader will be able to do. Longer and more narrative than `description`.

**categories / tags** — `categories` is one broad product-family label (e.g. `["Aspose.Tasks Product Family"]`). `tags` is an inline list of specific, reusable terms. Reuse existing terms from the site rather than minting near-duplicates — inconsistent taxonomy weakens the topical clustering that internal linking is meant to build.

**cover** — A map with `image`, `alt`, `caption`, `hidden`. `image` is bundle-relative (`images/<slug>.jpg`). Verify the file exists inside `images/`; a path to a nonexistent asset is a common silent breakage because the build still succeeds. If the cover has not been produced yet, still create `images/`, keep the reference, and say on delivery that the asset is outstanding.

**steps** — Site-specific list of imperative one-liners that feed HowTo structured data. Each step is a single concrete action, in order.

**faqs** — Mirror the FAQ block from the body so the template can emit FAQPage schema. This site uses `q`/`a` keys. Keep the wording identical in both places.

## Schema markup

Informational posts should carry Article or BlogPosting schema with:

- headline
- description
- author
- datePublished
- dateModified
- image
- publisher

Most Hugo themes generate this from front matter, so complete front matter usually is the schema work. If the theme does not, note it for the user rather than hand-rolling JSON-LD into the body.

## Open Graph

The theme should emit og:title, og:description, og:image, and og:url. These affect how the post previews when shared and give models additional metadata. If the theme derives them from the fields above, no extra work is needed.

## Body structure

Standard order for the markdown body:

1. Introduction — two to four short paragraphs. Open with the problem and the outcome in plain, reader-facing language: the pain point, who hits it, and what the reader will be able to do after reading. Name the solution (product or feature) but keep API surface out — no class, method, interface, property, or namespace names in the intro. The first API name appears no earlier than the first H2.
2. Key Takeaways — three to six standalone bullets
3. Main sections — H2s as questions, each opening with its answer
4. Conclusion — what the reader can now do, plus the strongest CTA
5. FAQ — five to eight Q/A pairs, mirrored into front matter

The H1 comes from `title` in front matter, so the body starts at H2. Do not add a second H1.
