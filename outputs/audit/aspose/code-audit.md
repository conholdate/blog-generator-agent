# Code Audit

## Summary
- Posts scanned: 2
- Posts with fenced code blocks: 2
- Code blocks found: 9
- Code/API issues found: 13
- SDK validation enabled: True

## API Reference Sources
The agent validates SDK classes by indexing configured product API reference repositories. For product-scoped audits, these references are derived from the selected product config where available.

| Source | Product | Path | Namespaces | Symbols Indexed |
| --- | --- | --- | --- | --- |
| html-net-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose | Aspose.HTML, aspose.html, com.aspose.html | 67868 |
| html-java-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose | Aspose.HTML, aspose.html, com.aspose.html | 67868 |
| html-python_net-api-reference |  | /home/runner/work/blog-generator-agent/blog-generator-agent/outputs/_repos/_api_references/Aspose | Aspose.HTML, aspose.html, com.aspose.html | 67868 |

## Per-Post Code Coverage
| Blog Post | Title | Language | Code Blocks | Code Issues | Top Code Issues |
| --- | --- | --- | --- | --- | --- |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Create Read and Edit HTML in Python | en | 8 | 10 | unresolved_api_symbol; unresolved_api_class; unresolved_api_class; unresolved_api_symbol; unresolved_api_class; unresolved_api_class; unresolved_api_class; unresolved_api_class; unresolved_api_class; unresolved_api_class |
| `content/Aspose.Blog/html/2026-08-05-convert-html-to-txt-in-python/index.md` | Convert HTML to TXT in Python | en | 1 | 3 | unresolved_api_class; unresolved_api_class; unresolved_api_class |

## Class/Member Resolution Details
Missing or deprecated SDK classes, properties, and members are listed here with the closest existing indexed-symbol suggestions when the API reference data can support them.

| File | Code Line | Referenced Class/Member | Status | Suggested Existing Symbol/Fix |
| --- | --- | --- | --- | --- |
| `content/Aspose.Blog/html/2026-08-05-convert-html-to-txt-in-python/index.md` | 54 | FileNotFoundError | Missing from API reference | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. |
| `content/Aspose.Blog/html/2026-08-05-convert-html-to-txt-in-python/index.md` | 84 | FileNotFoundError | Missing from API reference | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. |
| `content/Aspose.Blog/html/2026-08-05-convert-html-to-txt-in-python/index.md` | 90 | ValueError | Missing from API reference | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 56 | HtmlLoadOptions | Missing from indexed symbols | Replace `HtmlLoadOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. Otherwise add the symbol to sdk_validation if it is valid. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 70 | HtmlLoadOptions | Missing from API reference | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 71 | HtmlLoadOptions | Missing from API reference | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 140 | HtmlLoadOptions | Missing from indexed symbols | Replace `HtmlLoadOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. Otherwise add the symbol to sdk_validation if it is valid. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 180 | HtmlLoadOptions | Missing from API reference | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 182 | HtmlLoadOptions | Missing from API reference | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 222 | ValueError | Missing from API reference | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 224 | ValueError | Missing from API reference | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 228 | ValueError | Missing from API reference | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. |
| `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | 246 | FileNotFoundError | Missing from API reference | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. |

## Code/API Issues
| Severity | Issue | Policy | Rule | Evidence | Audience | File | Explanation | Recommended Fix | Effort | Impact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-convert-html-to-txt-in-python/index.md` | Code line 54 references `FileNotFoundError` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-convert-html-to-txt-in-python/index.md` | Code line 84 references `FileNotFoundError` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-convert-html-to-txt-in-python/index.md` | Code line 90 references `ValueError` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. | Low | High |
| High | unresolved_api_symbol |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code block line 56 references `HtmlLoadOptions`, which is not in the configured SDK symbol allowlist. | Replace `HtmlLoadOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. Otherwise add the symbol to sdk_validation if it is valid. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code line 70 references `HtmlLoadOptions` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code line 71 references `HtmlLoadOptions` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. | Low | High |
| High | unresolved_api_symbol |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code block line 140 references `HtmlLoadOptions`, which is not in the configured SDK symbol allowlist. | Replace `HtmlLoadOptions` with a verified existing SDK symbol if one fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. Otherwise add the symbol to sdk_validation if it is valid. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code line 180 references `HtmlLoadOptions` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code line 182 references `HtmlLoadOptions` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `HtmlLoadOptions` with the relevant existing API symbol if it fits. Nearest indexed symbols: `TemplateLoadOptions`, `HTMLSaveOptions`, `MHTMLSaveOptions`, `Options`, `OPTION`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code line 222 references `ValueError` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code line 224 references `ValueError` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code line 228 references `ValueError` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `ValueError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `Error`, `Value`, `TypeError`, `value_type`, `ValueType`. | Low | High |
| High | unresolved_api_class |  |  |  |  | `content/Aspose.Blog/html/2026-08-05-create-read-and-edit-html-in-python/index.md` | Code line 246 references `FileNotFoundError` as an SDK class/member, but it was not found in the indexed API reference symbols. | Replace `FileNotFoundError` with the relevant existing API symbol if it fits. Nearest indexed symbols: `NOT_FOUND_ERR`, `NOTFOUNDERR`, `NOT_FOUND`, `NOTFOUND`, `Error`. | Low | High |

## Checks Applied
- Validates Aspose import/module names against configured SDK namespaces.
- Validates imported or fully qualified classes against symbols indexed from API reference repositories.
- Flags configured deprecated or renamed SDK symbols.
- Optionally validates Python imports at runtime when `runtime_import_check` is enabled and target SDKs are installed.

## Known Limits
- Static validation focuses on explicit imports and fully qualified symbols; it does not execute snippets.
- Method-level validation depends on how completely the API reference repository exposes method names.
- If an API reference repository cannot be cloned or opened, the audit logs the skip and continues.