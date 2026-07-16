# Code Audit

## Summary
- Posts scanned: 3
- Posts with fenced code blocks: 3
- Code blocks found: 16
- Code/API issues found: 11
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
| `content/Aspose.Blog/pdf/2026-07-16-add-barcode-to-pdf-in-python/index.md` | Add Barcode to PDF in Python | en | 3 | 5 | unresolved_api_module; unresolved_api_module; unresolved_api_module; unresolved_api_class; unresolved_api_class |
| `content/Aspose.Blog/pdf/2026-07-16-convert-csv-to-pdf-in-java/index.md` | Convert CSV to PDF in Java | en | 6 | 3 | unresolved_api_class; unresolved_api_class; unresolved_api_symbol |
| `content/Aspose.Blog/pdf/2026-07-16-convert-epub-to-pdf-in-csharp/index.md` | Convert EPUB to PDF in C# | en | 7 | 3 | unresolved_api_class; unresolved_api_class; unresolved_api_class |

## Class/Member Resolution Details
Missing or deprecated SDK classes, properties, and members are listed here with the closest existing indexed-symbol suggestions when the API reference data can support them.

| File | Code Line | Referenced Class/Member | Status | Suggested Existing Symbol/Fix |
| --- | --- | --- | --- | --- |
| `content/Aspose.Blog/pdf/2026-07-16-add-barcode-to-pdf-in-python/index.md` | 104 | BarcodeGenerator | Missing from API reference | Replace `BarcodeGenerator` with the relevant existing API symbol if it fits. Nearest indexed symbols: `PageGenerator`, `TableGenerator`, `Generator`, `BARCODE`, `CODE`. |
| `content/Aspose.Blog/pdf/2026-07-16-add-barcode-to-pdf-in-python/index.md` | 104 | EncodeTypes | Missing from API reference | Replace `EncodeTypes` with the relevant existing API symbol if it fits. Nearest indexed symbols: `EncodingType`, `RenderModeType`, `types`, `CODE`, `Type`. |
| `content/Aspose.Blog/pdf/2026-07-16-convert-csv-to-pdf-in-java/index.md` | 93 | BufferedReader | Missing from API reference | Replace `BufferedReader` with the relevant existing API symbol if it fits. Nearest indexed symbols: `buffer`, `reader`, `Read`, `RED`, `FdfReader`. |
| `content/Aspose.Blog/pdf/2026-07-16-convert-csv-to-pdf-in-java/index.md` | 93 | FileReader | Missing from API reference | Replace `FileReader` with the relevant existing API symbol if it fits. Nearest indexed symbols: `filerelated`, `reader`, `FdfReader`, `XmlReader`, `File`. |
| `content/Aspose.Blog/pdf/2026-07-16-convert-csv-to-pdf-in-java/index.md` | 171 | A4 | Missing from indexed symbols | Replace `A4` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `getA4`, `PDF_A_4`, `PDFA4`, `A4Plus`, `PDF_A_4E`. Otherwise add the symbol to sdk_validation if it is valid. |
| `content/Aspose.Blog/pdf/2026-07-16-convert-epub-to-pdf-in-csharp/index.md` | 127 | FontEmbeddingModes | Missing from API reference | Replace `FontEmbeddingModes` with the relevant existing API symbol if it fits. Nearest indexed symbols: `PartsEmbeddingModes`, `font_embedding_options`, `FontEmbeddingOptions`, `parts_embedding_mode`, `PartsEmbeddingMode`. |
| `content/Aspose.Blog/pdf/2026-07-16-convert-epub-to-pdf-in-csharp/index.md` | 164 | FontEmbeddingModes | Missing from API reference | Replace `FontEmbeddingModes` with the relevant existing API symbol if it fits. Nearest indexed symbols: `PartsEmbeddingModes`, `font_embedding_options`, `FontEmbeddingOptions`, `parts_embedding_mode`, `PartsEmbeddingMode`. |
| `content/Aspose.Blog/pdf/2026-07-16-convert-epub-to-pdf-in-csharp/index.md` | 194 | PdfCompliance | Missing from API reference | Replace `PdfCompliance` with the relevant existing API symbol if it fits. Nearest indexed symbols: `getPdfACompliance`, `RemovePdfaCompliance`, `is_pdfa_compliant`, `IsPdfaCompliant`, `RemovePdfUaCompliance`. |

## Code/API Issues
| Severity | Issue | Policy | Rule | Evidence | Audience | File | Explanation | Recommended Fix | Effort | Impact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| High | unresolved_api_module |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-add-barcode-to-pdf-in-python/index.md` | Code block line 96 imports `asposebarcode`, which does not match configured SDK namespaces: Aspose.PDF, Aspose.Pdf, aspose.pdf, com.aspose.pdf. | Replace `asposebarcode` with the relevant configured SDK module/namespace if it fits. Possible namespace options: `aspose.pdf`, `Aspose.PDF`, `Aspose.Pdf`, `com.aspose.pdf`. Otherwise update sdk_validation namespaces if this module is valid. | Low | High |
| High | unresolved_api_module |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-add-barcode-to-pdf-in-python/index.md` | Code block line 96 imports `asposebarcode.generator`, which does not match configured SDK namespaces: Aspose.PDF, Aspose.Pdf, aspose.pdf, com.aspose.pdf. | Replace or verify unresolved module `asposebarcode.generator` using current SDK documentation, or update sdk_validation namespaces if `asposebarcode.generator` is valid. | Low | High |
| High | unresolved_api_module |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-add-barcode-to-pdf-in-python/index.md` | Code block line 96 imports `asposepdf`, which does not match configured SDK namespaces: Aspose.PDF, Aspose.Pdf, aspose.pdf, com.aspose.pdf. | Replace `asposepdf` with the relevant configured SDK module/namespace if it fits. Possible namespace options: `aspose.pdf`, `Aspose.PDF`, `Aspose.Pdf`, `com.aspose.pdf`. Otherwise update sdk_validation namespaces if this module is valid. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-add-barcode-to-pdf-in-python/index.md` | Code line 104 references `BarcodeGenerator` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `BarcodeGenerator` with the relevant existing API symbol if it fits. Nearest indexed symbols: `PageGenerator`, `TableGenerator`, `Generator`, `BARCODE`, `CODE`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-add-barcode-to-pdf-in-python/index.md` | Code line 104 references `EncodeTypes` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `EncodeTypes` with the relevant existing API symbol if it fits. Nearest indexed symbols: `EncodingType`, `RenderModeType`, `types`, `CODE`, `Type`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-convert-csv-to-pdf-in-java/index.md` | Code line 93 references `BufferedReader` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `BufferedReader` with the relevant existing API symbol if it fits. Nearest indexed symbols: `buffer`, `reader`, `Read`, `RED`, `FdfReader`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-convert-csv-to-pdf-in-java/index.md` | Code line 93 references `FileReader` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `FileReader` with the relevant existing API symbol if it fits. Nearest indexed symbols: `filerelated`, `reader`, `FdfReader`, `XmlReader`, `File`. | Low | High |
| High | unresolved_api_symbol |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-convert-csv-to-pdf-in-java/index.md` | Code block line 171 references `A4`, which is not in the configured SDK symbol allowlist. | Replace `A4` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `getA4`, `PDF_A_4`, `PDFA4`, `A4Plus`, `PDF_A_4E`. Otherwise add the symbol to sdk_validation if it is valid. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-convert-epub-to-pdf-in-csharp/index.md` | Code line 127 references `FontEmbeddingModes` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `FontEmbeddingModes` with the relevant existing API symbol if it fits. Nearest indexed symbols: `PartsEmbeddingModes`, `font_embedding_options`, `FontEmbeddingOptions`, `parts_embedding_mode`, `PartsEmbeddingMode`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-convert-epub-to-pdf-in-csharp/index.md` | Code line 164 references `FontEmbeddingModes` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `FontEmbeddingModes` with the relevant existing API symbol if it fits. Nearest indexed symbols: `PartsEmbeddingModes`, `font_embedding_options`, `FontEmbeddingOptions`, `parts_embedding_mode`, `PartsEmbeddingMode`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/pdf/2026-07-16-convert-epub-to-pdf-in-csharp/index.md` | Code line 194 references `PdfCompliance` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `PdfCompliance` with the relevant existing API symbol if it fits. Nearest indexed symbols: `getPdfACompliance`, `RemovePdfaCompliance`, `is_pdfa_compliant`, `IsPdfaCompliant`, `RemovePdfUaCompliance`. | Low | High |

## Checks Applied
- Validates Aspose import/module names against configured SDK namespaces.
- Validates imported or fully qualified classes against symbols indexed from API reference repositories.
- Flags configured deprecated or renamed SDK symbols.
- Optionally validates Python imports at runtime when `runtime_import_check` is enabled and target SDKs are installed.

## Known Limits
- Static validation focuses on explicit imports and fully qualified symbols; it does not execute snippets.
- Method-level validation depends on how completely the API reference repository exposes method names.
- If an API reference repository cannot be cloned or opened, the audit logs the skip and continues.