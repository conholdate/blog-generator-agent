# Audit Action Items

Consolidated actionable backlog for Aspose. This combines post-level, technical SEO, internal linking, multilingual, content, on-page SEO, and code/API findings from the audit output.

## Audit Run
| Field | Value |
| --- | --- |
| Blog | Aspose |
| Product | Aspose.PDF |
| Audit date | 2026-07-10 08:04:35 UTC |
| Repository | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/aspose-blog |
| Blog config | outputs/workflow-blog-config.yaml |
| Mode | report-with-fix-suggestions |
| Product filter | Aspose.blog/pdf |
| Post date filter | 2026-07-10 |
| Language filter | All |
| Include translations | false |
| Detailed outputs | true |
| LLM suggestions | true |
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
| Total action items | 14 |
| P0 action items | 0 |
| P1 action items | 8 |
| Low-effort quick wins | 13 |
| Critical issues | 0 |
| High issues | 4 |
| Medium issues | 8 |
| Low issues | 0 |
| Opportunity issues | 2 |

## Items By Area
| Area | Action Items |
| --- | --- |
| Internal Linking | 6 |
| Code/API | 4 |
| Content Quality | 3 |
| Technical SEO | 1 |

## All Action Items
Action items are grouped by affected post. The post heading carries the file path, so the tables omit the repeated file column.

### Extract Text from Scanned PDFs with Aspose.PDF OCR in C#
File: `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0001 | P1 | High | Code/API | unresolved_api_class | 71 | 100 | Replace `RecognizeTextWithOcr` with the relevant existing API symbol if it fits. Nearest indexed symbols: `recognize`, `hocr`, `TEXT`, `with`, `TE_X`. | Low | High | code-audit.md |
| AA-0002 | P1 | High | Code/API | unresolved_api_class | 74 | 100 | Replace `RunExamples` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Examples`, `new_XmpValue`, `NewXmpValue`, `Names`, `Rename`. | Low | High | code-audit.md |
| AA-0003 | P1 | High | Code/API | unresolved_api_symbol | 69 | 100 | Replace `OcrTextRecognitionOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `extraction_options`, `ExtractionOptions`, `getExtractionOptions`, `setExtractionOptions`, `TextExtractionOptions`. Otherwise add the symbol to sdk_va... | Low | High | code-audit.md |
| AA-0004 | P1 | High | Code/API | unresolved_api_symbol | 69 | 100 | Replace `OcrTextAbsorber` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TextAbsorber`, `TextabsorberIndex`, `FontAbsorber`, `absorber`, `TEXT`. Otherwise add the symbol to sdk_validation if it is valid. | Low | High | code-audit.md |
| AA-0005 | P1 | Medium | Content Quality | moderate_thin_content | Post-level | 100 | Expand with examples, screenshots, troubleshooting notes, and a stronger conclusion. | Medium | Medium | content-improvement-plan.md |
| AA-0006 | P1 | Medium | Internal Linking | too_few_outgoing_internal_links | Post-level | 100 | Add contextual links to related posts, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0007 | P1 | Medium | Internal Linking | weak_internal_links | Post-level | 100 | Add links to related tutorials, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0008 | P1 | Opportunity | Content Quality | suggest_body_output_image | Post-level | 100 | Consider adding an output screenshot or result image inside the post body if it helps readers validate the tutorial result. | Low | Medium | content-improvement-plan.md |
| AA-0012 | P2 | Medium | Internal Linking | orphan_post | Post-level | 0 | Add links to this post from related higher-traffic posts. | Low | Medium | internal-linking-audit.md |

### Add Timestamped Digital Signatures to PDFs in C#
File: `content/Aspose.Blog/pdf/2026-07-10-add-timestamped-digital-signatures-to-pdf-in-csharp/index.md`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0009 | P2 | Medium | Internal Linking | too_few_outgoing_internal_links | Post-level | 22 | Add contextual links to related posts, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0010 | P2 | Medium | Internal Linking | weak_internal_links | Post-level | 22 | Add links to related tutorials, docs, and product pages. | Low | Medium | internal-linking-audit.md |
| AA-0011 | P2 | Medium | Internal Linking | orphan_post | Post-level | 0 | Add links to this post from related higher-traffic posts. | Low | Medium | internal-linking-audit.md |
| AA-0014 | P3 | Opportunity | Content Quality | suggest_body_output_image | Post-level | 22 | Consider adding an output screenshot or result image inside the post body if it helps readers validate the tutorial result. | Low | Medium | content-improvement-plan.md |

### Sitewide / Technical
Scope: `/home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/aspose-blog`

| ID | Priority | Severity | Area | Issue | Line / Scope | Post Priority | Recommended Action | Effort | Impact | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AA-0013 | P2 | Medium | Technical SEO | missing_robots | Sitewide | 0 | Add robots.txt or confirm Hugo generates one. | Low | Medium | technical-seo-audit.md |


## LLM Suggestions
| File | Model | Cached | Summary | Suggested Title | Suggested Description | Content Actions | FAQ Questions | Risk Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `content/Aspose.Blog/pdf/2026-07-10-add-timestamped-digital-signatures-to-pdf-in-csharp/index.md` | gpt-oss | No | The post provides a solid tutorial but needs an inline output image, more internal links, and a stronger conclusion to meet content‑quality and internal‑linking policies. | How to Add Timestamped Digital Signatures to PDFs Using Aspose.PDF for .NET (C#) | Step‑by‑step guide to add TSA‑based timestamped digital signatures to PDFs in C# with Aspose.PDF for .NET, including setup, code, visual appearance, verification, and troubleshooting. | Insert an inline screenshot showing the signed PDF with the visible timestamped signature field.; Add at least two internal links: one to a related tutorial on PDF signing without timestamps, and another to the Aspose.PDF API reference page for the `PdfFileSig... | What TSA services can I use with Aspose.PDF and are there any limitations?; How do I protect my .pfx certificate password in a production application?; Can I create an invisible timestamped signature, and how does that differ from a visible one?; What licensin... | Ensure the TSA URL used (e.g., https://freetsa.org/tsr) is reachable from the deployment environment; fallback handling should be implemented for network failures.; Never hard‑code the .pfx password in source code; use secure storage mechanisms such as Azure K... |
| `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | gpt-oss | No | The post is thin, lacks inline images, contains several unresolved Aspose.PDF API symbols, and has weak internal linking; the audit recommends expanding content, adding visuals, correcting code to use verified SDK symbols, and strengthening SEO elements. | Extract Text from Scanned PDFs with Aspose.PDF OCR in C# – Step‑by‑Step Guide | A complete tutorial for .NET developers showing how to install Aspose.PDF, configure OCR, extract searchable text from scanned PDFs, and troubleshoot common issues. | Add at least two inline screenshots: one showing the OCR configuration UI (or code editor) and another showing the extracted text output file.; Replace the unresolved `OcrTextRecognitionOptions` with the verified `TextExtractionOptions` class and set its prope... | How do I extract text from a scanned PDF using Aspose.PDF OCR in C#?; Which OCR languages are supported by Aspose.PDF and how do I set them?; What licensing options are required to remove the watermark from OCR output?; How can I improve OCR accuracy for low‑r... | Changing API symbols may affect compilation; verify the exact method signatures in the version of Aspose.PDF you are using.; If `TextExtractionOptions` does not expose OCR‑specific properties in a given SDK version, consider using the documented OCR API (e.g.,... |

## Detailed Source Reports
Detailed reports are generated only when `--detailed-outputs true` is passed.

- `complete-seo-audit.md`: segment scorecard, priority roadmap, and per-post SEO score table.
- `content-improvement-plan.md`: post-level content refresh guidance.
- `code-audit.md`: SDK/API validation details.
- `technical-seo-audit.md`: Hugo config, template, robots, schema, and social metadata findings.
- `internal-linking-audit.md`: broken links, orphan posts, outgoing links, and weak anchors.
- `quick-wins.md`: low-effort issue table.
- `post-audit.csv` and `post-audit.json`: structured row-level audit data.