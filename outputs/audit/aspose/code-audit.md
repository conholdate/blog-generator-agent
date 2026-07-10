# Code Audit

## Summary
- Posts scanned: 2
- Posts with fenced code blocks: 2
- Code blocks found: 7
- Code/API issues found: 4
- SDK validation enabled: True

## API Reference Sources
The agent validates SDK classes by indexing configured product API reference repositories. For product-scoped audits, these references are derived from the selected product config where available.

| Source | Product | Path | Namespaces | Symbols Indexed |
| --- | --- | --- | --- | --- |
| pdf-net-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose.PDF-API-References/english/net | Aspose.PDF, Aspose.Pdf, aspose.pdf, com.aspose.pdf | 27015 |
| pdf-java-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose.PDF-API-References/english/java | Aspose.PDF, Aspose.Pdf, aspose.pdf, com.aspose.pdf | 11369 |
| pdf-python_net-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose.PDF-API-References/english/python-net | Aspose.PDF, Aspose.Pdf, aspose.pdf, com.aspose.pdf | 6921 |

## Per-Post Code Coverage
| Blog Post | Title | Language | Code Blocks | Code Issues | Top Code Issues |
| --- | --- | --- | --- | --- | --- |
| `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | Extract Text from Scanned PDFs with Aspose.PDF OCR in C# | en | 2 | 4 | unresolved_api_symbol; unresolved_api_symbol; unresolved_api_class; unresolved_api_class |
| `content/Aspose.Blog/pdf/2026-07-10-add-timestamped-digital-signatures-to-pdf-in-csharp/index.md` | Add Timestamped Digital Signatures to PDFs in C# | en | 5 | 0 |  |

## Class/Member Resolution Details
Missing or deprecated SDK classes, properties, and members are listed here with the closest existing indexed-symbol suggestions when the API reference data can support them.

| File | Code Line | Referenced Class/Member | Status | Suggested Existing Symbol/Fix |
| --- | --- | --- | --- | --- |
| `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | 69 | OcrTextRecognitionOptions | Missing from indexed symbols | Replace `OcrTextRecognitionOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `extraction_options`, `ExtractionOptions`, `getExtractionOptions`, `setExtractionOptions`, `TextExtractionOptions`. Otherwise add the symbol to sdk_va... |
| `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | 69 | OcrTextAbsorber | Missing from indexed symbols | Replace `OcrTextAbsorber` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TextAbsorber`, `TextabsorberIndex`, `FontAbsorber`, `absorber`, `TEXT`. Otherwise add the symbol to sdk_validation if it is valid. |
| `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | 71 | RecognizeTextWithOcr | Missing from API reference | Replace `RecognizeTextWithOcr` with the relevant existing API symbol if it fits. Nearest indexed symbols: `recognize`, `hocr`, `TEXT`, `with`, `TE_X`. |
| `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | 74 | RunExamples | Missing from API reference | Replace `RunExamples` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Examples`, `new_XmpValue`, `NewXmpValue`, `Names`, `Rename`. |

## Code/API Issues
| Severity | Issue | Policy | Rule | Evidence | Audience | File | Explanation | Recommended Fix | Effort | Impact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| High | unresolved_api_symbol |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | Code block line 69 references `OcrTextRecognitionOptions`, which is not in the configured SDK symbol allowlist. | Replace `OcrTextRecognitionOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `extraction_options`, `ExtractionOptions`, `getExtractionOptions`, `setExtractionOptions`, `TextExtractionOptions`. Otherwise add the symbol to sdk_va... | Low | High |
| High | unresolved_api_symbol |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | Code block line 69 references `OcrTextAbsorber`, which is not in the configured SDK symbol allowlist. | Replace `OcrTextAbsorber` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TextAbsorber`, `TextabsorberIndex`, `FontAbsorber`, `absorber`, `TEXT`. Otherwise add the symbol to sdk_validation if it is valid. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | Code line 71 references `RecognizeTextWithOcr` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `RecognizeTextWithOcr` with the relevant existing API symbol if it fits. Nearest indexed symbols: `recognize`, `hocr`, `TEXT`, `with`, `TE_X`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-10-extract-text-from-scanned-pdfs-in-csharp/index.md` | Code line 74 references `RunExamples` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `RunExamples` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Examples`, `new_XmpValue`, `NewXmpValue`, `Names`, `Rename`. | Low | High |

## Checks Applied
- Validates Aspose import/module names against configured SDK namespaces.
- Validates imported or fully qualified classes against symbols indexed from API reference repositories.
- Flags configured deprecated or renamed SDK symbols.
- Optionally validates Python imports at runtime when `runtime_import_check` is enabled and target SDKs are installed.

## Known Limits
- Static validation focuses on explicit imports and fully qualified symbols; it does not execute snippets.
- Method-level validation depends on how completely the API reference repository exposes method names.
- If an API reference repository cannot be cloned or opened, the audit logs the skip and continues.