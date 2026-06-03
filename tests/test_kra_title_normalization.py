from agent_engine.blog_keyword_analyzer.tools.normalization import KeywordRefiner
from agent_engine.blog_keyword_analyzer.tools.topic_acceptance import finalize_topic_acceptance


def test_kra_title_case_preserves_omr_and_step_by_step() -> None:
    refiner = KeywordRefiner()

    assert (
        refiner.to_title_case("STEP-by-STEP Guide to Read Omr Sheet from PNG in .NET")
        == "Step-by-Step Guide to Read OMR Sheet from PNG in .NET"
    )
    assert (
        refiner.to_title_case("STEP-by-STEP Parse Omr Image from Memorystream in Java")
        == "Step-by-Step Parse OMR Image from MemoryStream in Java"
    )


def test_kra_acceptance_fixes_malformed_platform_developer_guide() -> None:
    result = finalize_topic_acceptance(
        title="Parse Omr Survey Results in .NET-a Developer Guide",
        primary_keyword="Parse Omr Survey Results in .NET",
        platform=".NET",
    )

    assert result.title == "Parse OMR Survey Results in .NET: A Developer Guide"


def test_kra_acceptance_adds_missing_omr_answer_sheet_format_preposition() -> None:
    result = finalize_topic_acceptance(
        title="How to Parse Omr Answer Sheet JPG in .NET",
        primary_keyword="Parse Omr Answer Sheet JPG in .NET",
        platform=".NET",
    )

    assert result.title == "How to Parse OMR Answer Sheet from JPG in .NET"


def test_kra_barcode_title_cleanup_rewrites_weak_wrappers_and_casing() -> None:
    cases = [
        (
            "Reader and Generator in .NET Guide",
            "Reader and Generator in .NET",
            ".NET",
            "Barcode Reader and Generator in .NET Guide",
        ),
        (
            "How to Convert Reader and Generator in C++",
            "Reader and Generator in C++",
            "C++",
            "Build Barcode Reader and Generator in C++",
        ),
        (
            "Barcode Generator and Reader Generate and Scan Barcodes-C++",
            "Barcode Generator and Reader Generate and Scan Barcodes in C++",
            "C++",
            "Generate and Scan Barcodes in C++",
        ),
        (
            "Barcode Reader Scan Barcode in .NET: STEP-by-STEP Tutorial",
            "Barcode Reader Scan Barcode in .NET",
            ".NET",
            "Scan Barcode with Barcode Reader in .NET: Step-by-Step Tutorial",
        ),
        (
            "How to Convert Barcode Reader Scan Barcode in C++",
            "Barcode Reader Scan Barcode in C++",
            "C++",
            "Scan Barcode with Barcode Reader in C++",
        ),
        (
            "Build Barcode 93 Generator Barcode in Java-Quick Tutorial",
            "Build Barcode 93 Generator Barcode in Java",
            "Java",
            "Build Code 93 Barcode Generator in Java: Quick Tutorial",
        ),
        (
            "SCRIPT for Wpf Barcode Image in Python-Complete Guide",
            "Wpf Barcode Image in Python",
            "Python",
            "Generate WPF Barcode Image in Python: Complete Guide",
        ),
    ]

    for title, primary_keyword, platform, expected in cases:
        result = finalize_topic_acceptance(
            title=title,
            primary_keyword=primary_keyword,
            platform=platform,
        )
        assert result.title == expected


def test_kra_barcode_title_cleanup_normalizes_barcode_acronyms() -> None:
    cases = [
        (
            "Automate Dotcode Barcode Generation using Ci/CD in .NET",
            "Automate Dotcode Barcode Generation using Ci/CD in .NET",
            ".NET",
            "Automate DotCode Barcode Generation using CI/CD in .NET",
        ),
        (
            "Generate 2d Barcodes or QR Codes using Java: Code Sample",
            "Generate 2d Barcodes or QR Codes in Java",
            "Java",
            "Generate 2D Barcodes or QR Codes using Java: Code Sample",
        ),
        (
            "Generate Barcodes with Utf 8 Encoding in C++",
            "Generate Barcodes with Utf 8 Encoding in C++",
            "C++",
            "Generate Barcodes with UTF-8 Encoding in C++",
        ),
        (
            "Code to Create Gs1-128 Barcode in C++",
            "Create Gs1-128 Barcode in C++",
            "C++",
            "Create GS1-128 Barcode in C++",
        ),
        (
            "Read QR Code from Image FILE in .NET",
            "Read QR Code from Image FILE in .NET",
            ".NET",
            "Read QR Code from Image File in .NET",
        ),
    ]

    for title, primary_keyword, platform, expected in cases:
        result = finalize_topic_acceptance(
            title=title,
            primary_keyword=primary_keyword,
            platform=platform,
        )
        assert result.title == expected


def test_kra_barcode_title_cleanup_handles_remaining_bad_wrappers() -> None:
    cases = [
        (
            "Barcode Generator Guide for Developers using .NET Tutorial",
            "Barcode Generator Guide for Developers in .NET",
            ".NET",
            "Barcode Generator Guide for Developers in .NET",
        ),
        (
            "How to Convert Barcode Generator Guide for Developers in C++",
            "Barcode Generator Guide for Developers in C++",
            "C++",
            "Barcode Generator Guide for Developers in C++",
        ),
        (
            "Complete SCRIPT to Generate Data Matrix Barcode in Python",
            "Generate Data Matrix Barcode in Python",
            "Python",
            "Generate DataMatrix Barcode in Python",
        ),
        (
            "SCRIPT to Batch Generate Hibc LIC Barcodes in Python",
            "Generate Hibc LIC Barcodes in Python",
            "Python",
            "Batch Generate HIBC LIC Barcodes in Python",
        ),
        (
            "QR Code Reader How to Build High Performance QR Code in .NET",
            "QR Code Reader How to Build High Performance QR Code in .NET",
            ".NET",
            "Build High-Performance QR Code Reader in .NET",
        ),
        (
            "How to Convert Read QR Code from Image Buffer in C++",
            "Read QR Code from Image Buffer in C++",
            "C++",
            "Read QR Code from Image Buffer in C++",
        ),
        (
            "How to Convert Read Barcodes Applications in Python",
            "Read Barcodes Applications in Python",
            "Python",
            "Read Barcodes from Images in Python",
        ),
        (
            "How to Convert Wpf Barcode Generator in Java",
            "Wpf Barcode Generator in Java",
            "Java",
            "Build WPF Barcode Generator in Java",
        ),
        (
            "How to Rotate Barcode Image in .NET: A",
            "Rotate Barcode Image in .NET",
            ".NET",
            "How to Rotate Barcode Image in .NET",
        ),
    ]

    for title, primary_keyword, platform, expected in cases:
        result = finalize_topic_acceptance(
            title=title,
            primary_keyword=primary_keyword,
            platform=platform,
        )
        assert result.title == expected


def test_kra_barcode_title_cleanup_handles_remaining_casing_and_context() -> None:
    cases = [
        (
            "Implementing Barcode Reader High Dpi Image Scanning in C++",
            "Barcode Reader High Dpi Image Scanning in C++",
            "C++",
            "Implementing Barcode Reader High DPI Image Scanning in C++",
        ),
        (
            "Guide to Gs1-128 Barcode Image Generation in C++",
            "Gs1-128 Barcode Image Generation in C++",
            "C++",
            "Guide to GS1-128 Barcode Image Generation in C++",
        ),
        (
            "Generate 2d Barcodes or QR Codes using .NET: Step-by-Step",
            "Generate 2d Barcodes or QR Codes in .NET",
            ".NET",
            "Generate 2D Barcodes or QR Codes using .NET: Step-by-Step",
        ),
        (
            "Generate Barcodes with Utf-8 Encoding in Java",
            "Generate Barcodes with Utf-8 Encoding in Java",
            "Java",
            "Generate Barcodes with UTF-8 Encoding in Java",
        ),
        (
            "Create Wi Fi QR Code in Python",
            "Create Wi Fi QR Code in Python",
            "Python",
            "Create Wi-Fi QR Code in Python",
        ),
        (
            "Create QR Code from TXT FILE in Java",
            "Create QR Code from TXT FILE in Java",
            "Java",
            "Create QR Code from TXT file in Java",
        ),
        (
            "Control Ratio of Wide to Narrow in Python",
            "Control Ratio of Wide to Narrow in Python",
            "Python",
            "Control Code 39 Wide-to-Narrow Ratio in Python",
        ),
        (
            "Generate Barcode Applications in C++",
            "Generate Barcode Applications in C++",
            "C++",
            "Generate Barcodes for Applications in C++",
        ),
        (
            "Read Barcode from TIFF Image-Complete Tutorial in .NET",
            "Read Barcode from TIFF Image in .NET",
            ".NET",
            "Read Barcode from TIFF Image: Complete Tutorial in .NET",
        ),
    ]

    for title, primary_keyword, platform, expected in cases:
        result = finalize_topic_acceptance(
            title=title,
            primary_keyword=primary_keyword,
            platform=platform,
        )
        assert result.title == expected
