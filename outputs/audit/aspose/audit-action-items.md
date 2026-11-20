# Audit Action Items

Consolidated actionable backlog for Aspose. This combines post-level, technical SEO, internal linking, multilingual, content, on-page SEO, and code/API findings from the audit output.

## Audit Run
| Field | Value |
| --- | --- |
| Blog | Aspose |
| Product | Aspose.SVG |
| Audit date | 2026-11-20 06:45:30 UTC |
| Repository | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/aspose-blog |
| Blog config | outputs/workflow-blog-config.yaml |
| Mode | report |
| Product filter | Aspose.blog/svg |
| Post date filter | 2026-11-18 |
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
| Total action items | 9 |
| P0 action items | 0 |
| P1 action items | 0 |
| Low-effort quick wins | 9 |
| Critical issues | 0 |
| High issues | 0 |
| Medium issues | 7 |
| Low issues | 0 |
| Opportunity issues | 2 |

## Items By Area
| Area | Action Items |
| --- | --- |
| Internal Linking | 6 |
| Content Quality | 2 |
| Technical SEO | 1 |

## All Action Items
Action items are grouped by affected post. The post heading carries the file path, so the tables omit the repeated file column.

### Convert SVG Text to Path in Python
File: `content/Aspose.Blog/svg/2026-11-18-convert-svg-text-to-path-in-python/index.md`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0001 | P2 | Medium | Internal Linking | too_few_outgoing_internal_links | Post-level | 24 | Add contextual links to related posts, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0002 | P2 | Medium | Internal Linking | weak_internal_links | Post-level | 24 | Add links to related tutorials, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0005 | P2 | Medium | Internal Linking | orphan_post | Post-level | 0 | Add links to this post from related higher-traffic posts. | Low | Medium | internal-linking-audit.md |
| AA-0008 | P3 | Opportunity | Content Quality | suggest_body_output_image | Post-level | 24 | Consider adding an output screenshot or result image inside the post body if it helps readers validate the tutorial result. | Low | Medium | content-improvement-plan.md |

### Convert SVG to JPG in Python using Aspose.SVG
File: `content/Aspose.Blog/svg/2026-11-18-convert-svg-to-jpg-in-python/index.md`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0003 | P2 | Medium | Internal Linking | too_few_outgoing_internal_links | Post-level | 24 | Add contextual links to related posts, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0004 | P2 | Medium | Internal Linking | weak_internal_links | Post-level | 24 | Add links to related tutorials, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0006 | P2 | Medium | Internal Linking | orphan_post | Post-level | 0 | Add links to this post from related higher-traffic posts. | Low | Medium | internal-linking-audit.md |
| AA-0009 | P3 | Opportunity | Content Quality | suggest_body_output_image | Post-level | 24 | Consider adding an output screenshot or result image inside the post body if it helps readers validate the tutorial result. | Low | Medium | content-improvement-plan.md |

### Sitewide / Technical
Scope: `/home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/aspose-blog`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0007 | P2 | Medium | Technical SEO | missing_robots | Sitewide | 0 | Add robots.txt or confirm Hugo generates one. | Low | Medium | technical-seo-audit.md |


## Detailed Source Reports
Detailed reports are generated only when `--detailed-outputs true` is passed.

- `complete-seo-audit.md`: segment scorecard, priority roadmap, and per-post SEO score table.
- `content-improvement-plan.md`: post-level content refresh guidance.
- `code-audit.md`: SDK/API validation details.
- `technical-seo-audit.md`: Hugo config, template, robots, schema, and social metadata findings.
- `internal-linking-audit.md`: broken links, orphan posts, outgoing links, and weak anchors.
- `quick-wins.md`: low-effort issue table.
- `post-audit.csv` and `post-audit.json`: structured row-level audit data.