# Audit Action Items

Consolidated actionable backlog for Aspose. This combines post-level, technical SEO, internal linking, multilingual, content, on-page SEO, and code/API findings from the audit output.

## Audit Run
| Field | Value |
| --- | --- |
| Blog | Aspose |
| Product | Aspose.HTML |
| Audit date | 2026-08-05 12:30:28 UTC |
| Repository | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/aspose-blog |
| Blog config | outputs/workflow-blog-config.yaml |
| Mode | report |
| Product filter | Aspose.blog/html |
| Post date filter | 2026-08-05 |
| Language filter | All |
| Include translations | false |
| Detailed outputs | true |
| LLM suggestions | false |
| LLM model |  |
| Draft fixes | false |
| Max draft fixes | All |
| Priority only | false |
| Send metrics | true |
| Output directory | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/audit/aspose |
| Workdir | outputs/_repos |
| Keep workdir | false |

## Summary
| Metric | Count |
| --- | --- |
| Total scanned blog posts | 2 |
| Total action items | 24 |
| P0 action items | 0 |
| P1 action items | 21 |
| Low-effort quick wins | 24 |
| Critical issues | 0 |
| High issues | 13 |
| Medium issues | 9 |
| Low issues | 0 |
| Opportunity issues | 2 |

## Items By Area
| Area | Action Items |
| --- | --- |
| Code/API | 13 |
| Internal Linking | 6 |
| On-Page SEO | 2 |
| Content Quality | 2 |
| Technical SEO | 1 |

## All Action Items
Action items are grouped by affected post. The post heading carries the file path, so the tables omit the repeated file column.

### Convert HTML to TXT in Python
File: `content/Aspose.Blog/html/2026-08-05-convert-html-to-txt-in-python/index.md`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0001 | P1 | High | Code/API | unresolved_api_class | 54 | 100 | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. | Low | High | code-audit.md |
| AA-0002 | P1 | High | Code/API | unresolved_api_class | 84 | 100 | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. | Low | High | code-audit.md |
| AA-0003 | P1 | High | Code/API | unresolved_api_class | 90 | 100 | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. | Low | High | code-audit.md |
| AA-0014 | P1 | Medium | Internal Linking | too_few_outgoing_internal_links | Post-level | 100 | Add contextual links to related posts, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0015 | P1 | Medium | Internal Linking | weak_internal_links | Post-level | 100 | Add links to related tutorials, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0018 | P1 | Medium | On-Page SEO | short_title | Post-level | 100 | Expand the title with topic, audience, file format, or outcome. | Low | Medium | complete-seo-audit.md |
| AA-0019 | P1 | Medium | On-Page SEO | title_length | Post-level | 100 | Keep the title around 30-70 characters while preserving clarity. | Low | Medium | complete-seo-audit.md |
| AA-0020 | P1 | Opportunity | Content Quality | suggest_body_output_image | Post-level | 100 | Consider adding an output screenshot or result image inside the post body if it helps readers validate the tutorial result. | Low | Medium | content-improvement-plan.md |
| AA-0022 | P2 | Medium | Internal Linking | orphan_post | Post-level | 0 | Add links to this post from related higher-traffic posts. | Low | Medium | internal-linking-audit.md |

### Create Read and Edit HTML in Python
File: `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0004 | P1 | High | Code/API | unresolved_api_class | 70 | 100 | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. | Low | High | code-audit.md |
| AA-0005 | P1 | High | Code/API | unresolved_api_class | 71 | 100 | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. | Low | High | code-audit.md |
| AA-0006 | P1 | High | Code/API | unresolved_api_class | 180 | 100 | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. | Low | High | code-audit.md |
| AA-0007 | P1 | High | Code/API | unresolved_api_class | 182 | 100 | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. | Low | High | code-audit.md |
| AA-0008 | P1 | High | Code/API | unresolved_api_class | 222 | 100 | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. | Low | High | code-audit.md |
| AA-0009 | P1 | High | Code/API | unresolved_api_class | 224 | 100 | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. | Low | High | code-audit.md |
| AA-0010 | P1 | High | Code/API | unresolved_api_class | 228 | 100 | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. | Low | High | code-audit.md |
| AA-0011 | P1 | High | Code/API | unresolved_api_class | 246 | 100 | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. | Low | High | code-audit.md |
| AA-0012 | P1 | High | Code/API | unresolved_api_symbol | 56 | 100 | Replace `HtmlLoadOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. Otherwise add the symbol to sdk_validation if it is valid. | Low | High | code-audit.md |
| AA-0013 | P1 | High | Code/API | unresolved_api_symbol | 140 | 100 | Replace `HtmlLoadOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. Otherwise add the symbol to sdk_validation if it is valid. | Low | High | code-audit.md |
| AA-0016 | P1 | Medium | Internal Linking | too_few_outgoing_internal_links | Post-level | 100 | Add contextual links to related posts, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0017 | P1 | Medium | Internal Linking | weak_internal_links | Post-level | 100 | Add links to related tutorials, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0021 | P1 | Opportunity | Content Quality | suggest_body_output_image | Post-level | 100 | Consider adding an output screenshot or result image inside the post body if it helps readers validate the tutorial result. | Low | Medium | content-improvement-plan.md |
| AA-0023 | P2 | Medium | Internal Linking | orphan_post | Post-level | 0 | Add links to this post from related higher-traffic posts. | Low | Medium | internal-linking-audit.md |

### Sitewide / Technical
Scope: `/home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/aspose-blog`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0024 | P2 | Medium | Technical SEO | missing_robots | Sitewide | 0 | Add robots.txt or confirm Hugo generates one. | Low | Medium | technical-seo-audit.md |


## Detailed Source Reports
Detailed reports are generated only when `--detailed-outputs true` is passed.

- `complete-seo-audit.md`: segment scorecard, priority roadmap, and per-post SEO score table.
- `content-improvement-plan.md`: post-level content refresh guidance.
- `code-audit.md`: SDK/API validation details.
- `technical-seo-audit.md`: Hugo config, template, robots, schema, and social metadata findings.
- `internal-linking-audit.md`: broken links, orphan posts, outgoing links, and weak anchors.
- `quick-wins.md`: low-effort issue table.
- `post-audit.csv` and `post-audit.json`: structured row-level audit data.