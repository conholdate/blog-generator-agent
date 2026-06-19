# Code Audit

## Summary
- Posts scanned: 1
- Posts with fenced code blocks: 1
- Code blocks found: 1
- Code/API issues found: 0
- SDK validation enabled: True

## API Reference Sources
The agent validates SDK classes by indexing configured product API reference repositories. For product-scoped audits, these references are derived from the selected product config where available.

| Source | Product | Path | Namespaces | Symbols Indexed |
| --- | --- | --- | --- | --- |
| barcode-net-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose/english/net | Aspose.BarCode, aspose.barcode, com.aspose.barcode | 6703 |
| barcode-java-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose/english/java | Aspose.BarCode, aspose.barcode, com.aspose.barcode | 2249 |
| barcode-cpp-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose/english/cpp | Aspose.BarCode, aspose.barcode, com.aspose.barcode | 7663 |
| barcode-python_net-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose/english/python-net | Aspose.BarCode, aspose.barcode, com.aspose.barcode | 2083 |

## Per-Post Code Coverage
| Blog Post | Title | Language | Code Blocks | Code Issues | Top Code Issues |
| --- | --- | --- | --- | --- | --- |
| `content/Aspose.Blog/barcode/2026-06-18-build-code-93-barcode-generator-in-python/index.md` | Build Code 93 Barcode Generator in Python | en | 1 | 0 |  |

## Class/Member Resolution Details
Missing or deprecated SDK classes, properties, and members are listed here with the closest existing indexed-symbol suggestions when the API reference data can support them.

| File | Code Line | Referenced Class/Member | Status | Suggested Existing Symbol/Fix |
| --- | --- | --- | --- | --- |
| None |  |  |  |  |

## Code/API Issues
No issues detected.

## Checks Applied
- Validates Aspose import/module names against configured SDK namespaces.
- Validates imported or fully qualified classes against symbols indexed from API reference repositories.
- Flags configured deprecated or renamed SDK symbols.
- Optionally validates Python imports at runtime when `runtime_import_check` is enabled and target SDKs are installed.

## Known Limits
- Static validation focuses on explicit imports and fully qualified symbols; it does not execute snippets.
- Method-level validation depends on how completely the API reference repository exposes method names.
- If an API reference repository cannot be cloned or opened, the audit logs the skip and continues.