from __future__ import annotations

from pathlib import Path

from hugo_blog_audit_agent.api_validation import hydrate_sdk_validation_from_references
from hugo_blog_audit_agent.auditor import audit_content
from hugo_blog_audit_agent.hugo import detect_hugo_project
from hugo_blog_audit_agent.models import AuditResult, BlogConfig
from hugo_blog_audit_agent.reports import write_code_audit
from hugo_blog_audit_agent.scanner import scan_markdown
from tests.helpers import make_repo

def test_sdk_validation_flags_wrong_import_module_and_deprecated_symbol(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "bad-api-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Read Barcodes in Python and C#"
description: "Learn to read and generate barcodes with code examples."
---

Intro paragraph that explains the reader promise and outcome in enough detail to be useful for tests.

## Python

```python
from asposebarcode import BarCodeReader, DecodeType
```

## C#

```csharp
var builder = new BarCodeBuilder();
builder.SymbologyType = Symbology.QR;
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "aspose-barcode",
                    "applies_to": ["barcode"],
                    "namespaces": ["aspose.barcode", "Aspose.BarCode"],
                    "known_symbols": ["BarCodeReader", "DecodeType", "BarcodeGenerator", "EncodeTypes"],
                    "deprecated_symbols": {"BarCodeBuilder": "BarcodeGenerator", "Symbology": "EncodeTypes"},
                }
            ],
        },
    )
    issues = audit_content(post, config)
    issue_types = [issue.issue_type for issue in issues]
    assert "unresolved_api_module" in issue_types
    module_issue = next(issue for issue in issues if issue.issue_type == "unresolved_api_module")
    assert "asposebarcode" in module_issue.recommended_fix
    assert "Possible namespace options" in module_issue.recommended_fix
    assert "aspose.barcode" in module_issue.recommended_fix
    assert issue_types.count("deprecated_api_symbol") == 2

def test_sdk_validation_allows_known_python_support_modules(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "support-module-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Code 39 Barcode in Python"
description: "Learn to generate Code 39 barcodes in Python."
---

```python
from aspose.barcode import generation
from aspose.pydrawing import Color
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "aspose-barcode",
                    "applies_to": ["barcode"],
                    "namespaces": ["aspose.barcode", "Aspose.BarCode", "com.aspose.barcode"],
                    "known_symbols": ["BarcodeGenerator", "EncodeTypes", "BarCodeImageFormat"],
                }
            ],
        },
    )
    issues = audit_content(post, config)
    assert not any(issue.issue_type == "unresolved_api_module" for issue in issues)

def test_unresolved_api_module_fallback_names_bad_module(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "unknown-module-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Code 39 Barcode in Python"
description: "Learn to generate Code 39 barcodes in Python."
---

```python
from aspose.unknown import Widget
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "aspose-barcode",
                    "applies_to": ["barcode"],
                    "namespaces": ["aspose.barcode"],
                    "known_symbols": ["BarcodeGenerator"],
                }
            ],
        },
    )
    issues = audit_content(post, config)
    module_issue = next(issue for issue in issues if issue.issue_type == "unresolved_api_module")
    assert "aspose.unknown" in module_issue.recommended_fix

def test_sdk_validation_uses_api_reference_repo_symbols(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    api_ref = tmp_path / "api-reference"
    api_ref.mkdir()
    (api_ref / "BarcodeGenerator.md").write_text("# BarcodeGenerator\n\nAspose.BarCode.Generation.BarcodeGenerator", encoding="utf-8")
    (api_ref / "BarCodeReader.md").write_text("# BarCodeReader\n\nclass BarCodeReader", encoding="utf-8")
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "reference-api-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Barcodes in Python"
description: "Learn to generate barcodes with the API."
---

```python
from aspose.barcode.generation import BarcodeGenerator, BarCodeBuilder
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    sdk_validation = hydrate_sdk_validation_from_references(
        {
            "enabled": True,
            "api_reference_repositories": [
                {
                    "repo_key": "barcode-ref",
                    "product_key": "barcode",
                    "repo_path": str(api_ref),
                    "applies_to": ["barcode"],
                    "namespaces": ["aspose.barcode"],
                }
            ],
        },
        tmp_path / "work",
        False,
    )
    config = BlogConfig("Test", str(repo), sdk_validation=sdk_validation)
    issues = audit_content(post, config)
    unresolved = [issue for issue in issues if issue.issue_type == "unresolved_api_symbol"]
    assert len(unresolved) == 1
    assert "BarCodeBuilder" in unresolved[0].explanation
    assert "Nearest indexed symbols" in unresolved[0].recommended_fix
    assert "BarcodeGenerator" in unresolved[0].recommended_fix
    post.issues = issues
    report = AuditResult(config, repo, detect_hugo_project(repo), [post], [], [], [])
    out = tmp_path / "code-audit.md"
    write_code_audit(report, out)
    code_audit = out.read_text(encoding="utf-8")
    assert "## Class/Member Resolution Details" in code_audit
    assert "BarCodeBuilder" in code_audit
    assert "BarcodeGenerator" in code_audit

def test_sdk_validation_flags_blog_prose_and_code_class_mentions(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "2026-06-05-generate-barcode-for-healthcare-applications-in-net"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Barcode for Healthcare Applications in .NET"
description: "Learn to generate healthcare barcodes in .NET."
---

Intro paragraph that explains the reader promise and outcome in enough detail to be useful for tests.

2. **Create a BarCodeBuilder instance** - Initialize the builder and select a symbology that matches your use case.

```csharp
BarCodeBuilder qrBuilder = new BarCodeBuilder();
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "aspose-barcode",
                    "applies_to": ["barcode"],
                    "namespaces": ["Aspose.BarCode"],
                    "known_symbols": ["BarCodeReader", "BarcodeGenerator", "EncodeTypes"],
                }
            ],
        },
    )
    issues = audit_content(post, config)
    class_issues = [issue for issue in issues if issue.issue_type == "unresolved_api_class"]
    assert len(class_issues) == 2
    assert any("Markdown line" in issue.explanation for issue in class_issues)
    assert any("Code line" in issue.explanation for issue in class_issues)
    assert all("BarCodeBuilder" in issue.explanation for issue in class_issues)
    assert all("BarcodeGenerator" in issue.recommended_fix for issue in class_issues)
    post.issues = issues
    report = AuditResult(config, repo, detect_hugo_project(repo), [post], [], [], [])
    out = tmp_path / "code-audit.md"
    write_code_audit(report, out)
    code_audit = out.read_text(encoding="utf-8")
    assert "unresolved_api_class" in code_audit
    assert "Missing from API reference" in code_audit
    assert "BarCodeBuilder" in code_audit
    assert "BarcodeGenerator" in code_audit

def test_sdk_validation_flags_missing_property_assignments(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "property-validation-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Barcode with Custom Properties in .NET"
description: "Learn to configure barcode properties in .NET."
---

```csharp
BarcodeGenerator builder = new BarcodeGenerator();
builder.CodeLocation = CodeLocation.None;
builder.BarHeight = 50;
builder.XDimension = 2;
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "aspose-barcode",
                    "applies_to": ["barcode"],
                    "namespaces": ["Aspose.BarCode"],
                    "known_symbols": ["BarcodeGenerator", "BarHeight", "XDimension", "CodeTextLocation"],
                }
            ],
        },
    )
    issues = audit_content(post, config)
    member_issues = [issue for issue in issues if issue.issue_type == "unresolved_api_member"]
    assert len(member_issues) == 1
    assert "CodeLocation" in member_issues[0].explanation
    assert "CodeTextLocation" in member_issues[0].recommended_fix
    assert not any("BarHeight" in issue.explanation for issue in member_issues)
    assert not any("XDimension" in issue.explanation for issue in member_issues)
    post.issues = issues
    report = AuditResult(config, repo, detect_hugo_project(repo), [post], [], [], [])
    out = tmp_path / "code-audit.md"
    write_code_audit(report, out)
    code_audit = out.read_text(encoding="utf-8")
    assert "unresolved_api_member" in code_audit
    assert "CodeLocation" in code_audit
    assert "CodeTextLocation" in code_audit

def test_sdk_validation_indexes_nested_api_reference_properties(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    api_ref = tmp_path / "api-reference"
    api_ref.mkdir()
    (api_ref / "BarcodeGenerator.md").write_text(
        "# BarcodeGenerator\n\n"
        "BarcodeGenerator.Parameters.Barcode.BarHeight\n"
        "BarcodeGenerator.Parameters.Barcode.XDimension\n"
        "BarcodeGenerator.Parameters.Barcode.CodeTextLocation\n"
        "# QREncodeMode\n"
        "# QRErrorLevel\n",
        encoding="utf-8",
    )
    for relative in [
        "barcode-generator/parameters/barcode/qr/encode-mode.md",
        "barcode-generator/parameters/barcode/qr/error-level.md",
        "barcode-generator/parameters/barcode/bar-height.md",
    ]:
        target = api_ref / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# API Reference\n", encoding="utf-8")
    (api_ref / "QrParameters.md").write_text(
        """# QrParameters

| Name | Description |
| :- | :- |
|encode_mode|QR symbology type of BarCode's encoding mode. Default value: QREncodeMode.Auto.|
|error_level|Level of Reed-Solomon error correction for QR. See QRErrorLevel.|
""",
        encoding="utf-8",
    )
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "nested-property-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Barcode with Nested Properties in .NET"
description: "Learn to configure barcode properties in .NET."
---

```csharp
BarcodeGenerator builder = new BarcodeGenerator();
builder.Parameters.Barcode.BarHeight = 50;
builder.XDimension = 2;
builder.Parameters.Barcode.QR.EncodeMode = QREncodeMode.Auto;
builder.Parameters.Barcode.QR.ErrorLevel = QRErrorLevel.LevelM;
builder.CodeLocation = CodeLocation.None;
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    sdk_validation = hydrate_sdk_validation_from_references(
        {
            "enabled": True,
            "api_reference_repositories": [
                {
                    "repo_key": "barcode-ref",
                    "product_key": "barcode",
                    "repo_path": str(api_ref),
                    "applies_to": ["barcode"],
                    "namespaces": ["Aspose.BarCode"],
                }
            ],
        },
        tmp_path / "work",
        False,
    )
    known_symbols = sdk_validation["packages"][0]["known_symbols"]
    assert "BarHeight" in known_symbols
    assert "XDimension" in known_symbols
    assert "EncodeMode" in known_symbols
    assert "ErrorLevel" in known_symbols
    assert "encode_mode" in known_symbols
    assert "error_level" in known_symbols
    assert "CodeTextLocation" in known_symbols
    config = BlogConfig("Test", str(repo), sdk_validation=sdk_validation)
    issues = audit_content(post, config)
    api_issues = [issue for issue in issues if issue.issue_type in {"unresolved_api_class", "unresolved_api_member"}]
    assert not any("BarHeight" in issue.explanation for issue in api_issues)
    assert not any("XDimension" in issue.explanation for issue in api_issues)
    assert not any("EncodeMode" in issue.explanation for issue in api_issues)
    assert not any("ErrorLevel" in issue.explanation for issue in api_issues)
    member_issues = [issue for issue in api_issues if issue.issue_type == "unresolved_api_member"]
    assert len(member_issues) == 1
    assert "CodeLocation" in member_issues[0].explanation
    assert "CodeTextLocation" in member_issues[0].recommended_fix

def test_sdk_validation_uses_union_of_applicable_reference_symbols(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "merged-reference-symbols-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate QR Barcode with Error Level in .NET"
description: "Learn to configure QR barcode error level in .NET."
---

```csharp
BarcodeGenerator generator = new BarcodeGenerator(EncodeTypes.QR);
generator.Parameters.Barcode.QR.ErrorLevel = QRErrorLevel.LevelH;
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "barcode-net",
                    "applies_to": ["barcode"],
                    "namespaces": ["Aspose.BarCode"],
                    "known_symbols": ["BarcodeGenerator", "EncodeTypes", "QRErrorLevel"],
                },
                {
                    "id": "barcode-python",
                    "applies_to": ["barcode"],
                    "namespaces": ["aspose.barcode"],
                    "known_symbols": ["ErrorLevel"],
                },
            ],
        },
    )
    issues = audit_content(post, config)
    assert not any(issue.issue_type == "unresolved_api_member" and "ErrorLevel" in issue.explanation for issue in issues)

def test_sdk_validation_does_not_treat_backticked_properties_as_classes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "backticked-property-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Barcode with Property Guidance in .NET"
description: "Learn to configure barcode property values in .NET."
---

Set `BarHeight` to at least 50 points and `XDimension` to 2 points for reliable scanning.
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "aspose-barcode",
                    "applies_to": ["barcode"],
                    "namespaces": ["Aspose.BarCode"],
                    "known_symbols": ["BarcodeGenerator", "QREncodeMode", "QRErrorLevel"],
                }
            ],
        },
    )
    issues = audit_content(post, config)
    assert not any(issue.issue_type == "unresolved_api_class" and "BarHeight" in issue.explanation for issue in issues)
    assert not any(issue.issue_type == "unresolved_api_class" and "XDimension" in issue.explanation for issue in issues)

def test_sdk_validation_does_not_treat_output_filenames_as_classes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    post_dir = repo / "content" / "Aspose.blog" / "barcode" / "filename-output-post"
    post_dir.mkdir(parents=True)
    (post_dir / "index.md").write_text(
        """---
title: "Generate Healthcare Barcode Output in .NET"
description: "Learn to generate a healthcare barcode output file in .NET."
---

Use PatientHL7_QR.png as the generated output image.

```csharp
generator.Save("PatientHL7_QR.png");
```
""",
        encoding="utf-8",
    )
    post = next(p for p in scan_markdown(repo, product="Aspose.blog/barcode", include_translations=False))
    config = BlogConfig(
        "Test",
        str(repo),
        sdk_validation={
            "enabled": True,
            "packages": [
                {
                    "id": "aspose-barcode",
                    "applies_to": ["barcode"],
                    "namespaces": ["Aspose.BarCode"],
                    "known_symbols": ["BarcodeGenerator", "Optional"],
                }
            ],
        },
    )
    issues = audit_content(post, config)
    assert not any("PatientHL7_QR" in issue.explanation for issue in issues)
    assert not any("PatientHL7_QR" in issue.recommended_fix for issue in issues)
