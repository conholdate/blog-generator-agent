from agent_engine.content_gap_agent.tools.normalization import (
    FILE_FORMAT_REGISTRY,
    canonical_file_format,
    canonical_topic_key,
    normalize_sentence_text,
)
from agent_engine.content_indexer_agent.tools.normalization import canonical_topic_key as indexer_canonical_topic_key
from agent_engine.content_gap_agent.tools.coverage.blogs_to_blogs import (
    compute_blogs_to_blogs,
    record_gap_key,
    record_gap_keys,
)
from agent_engine.content_gap_agent.tools.io import IndexRecord
from agent_engine.content_gap_agent.tools.sheets_export import build_payload
from agent_engine.content_indexer_agent.tools.key_maker import build_content_topic
import json


def test_gis_conversion_topic_keys_collapse_to_primary_pair() -> None:
    expected_pairs = [
        ("Geojson to topojson", "Geojson to topojson and vice versa"),
        ("Gpx to CSV", "Gpx to CSV conversion guide"),
        ("Kml to CSV", "Kml to CSV and CSV to kml"),
        ("Kml to gpx", "Kml to gpx and gpx to kml"),
        ("Shapefile to JSON", "Shapefile to JSON geospatial"),
        ("Shapefile to SVG", "Shapefile to SVG gis"),
    ]

    for primary, duplicate in expected_pairs:
        assert canonical_topic_key(duplicate) == canonical_topic_key(primary)


def test_bidirectional_blog_record_matches_both_conversion_directions() -> None:
    record = IndexRecord(
        id="blog::gis/kml-gpx/index.md",
        repo_key="blog",
        repo_type="blog",
        platform="net",
        title="Convert KML to GPX and GPX to KML using C#",
        topic="KML to GPX and GPX to KML",
        category="",
        sub_category="",
        key="kml to gpx and gpx to kml",
    )

    assert record_gap_key(record) == "kml-to-gpx"
    assert record_gap_keys(record) == ["kml-to-gpx", "gpx-to-kml"]


def test_file_format_registry_loads_gis_formats_from_config() -> None:
    assert "geojson" in FILE_FORMAT_REGISTRY
    assert "topojson" in FILE_FORMAT_REGISTRY
    assert "gpx" in FILE_FORMAT_REGISTRY
    assert "kml" in FILE_FORMAT_REGISTRY
    assert "shapefile" in FILE_FORMAT_REGISTRY
    assert canonical_file_format("shape file") == "shapefile"


def test_image_callout_topic_keys_collapse_to_same_key() -> None:
    titles = [
        "Add Image Callouts in Java",
        "Add Callout to images in C#",
    ]
    topics = [build_content_topic(title=title) for title in titles]

    assert topics == ["Add image callout", "Add image callout"]
    assert {canonical_topic_key(topic) for topic in topics} == {"add image callout"}
    assert canonical_topic_key("Add Image Callouts in Java") == "add image callout"
    assert canonical_topic_key("Add Callout to images in C#") == "add image callout"


def test_format_is_preserved_when_used_as_action() -> None:
    title = "Draw and Format Text in Java Using Aspose.Drawing for Java"
    topic = build_content_topic(title=title)

    assert topic == "Draw and format text using aspose drawing"
    assert canonical_topic_key(topic) == "draw and format text using aspose drawing"


def test_omr_topics_drop_platform_and_seo_noise() -> None:
    assert build_content_topic(title="C# Optical Mark Recognition (OMR) Software in .NET") == "Optical mark recognition"
    assert build_content_topic(title="Create OMR sheet in PDF free and") == "Create OMR sheet in PDF"
    assert build_content_topic(title="Omr sheet reader omr sheet PNG") == "Read OMR sheet from PNG"
    assert build_content_topic(title="Omr scanner the ultimate free answer scanner") == "OMR answer scanner"
    assert build_content_topic(title="Scan survey free omr") == "Scan OMR survey"


def test_non_omr_grade_calculator_topics_are_rejected() -> None:
    assert build_content_topic(title="Calculate cgpa online grades calculator") == ""
    assert build_content_topic(title="Grade calculator free letter grading calculator") == ""


def test_omr_acronym_survives_coverage_display_normalization() -> None:
    key = canonical_topic_key("Optical mark recognition OMR")
    assert key == "optical mark recognition"
    assert normalize_sentence_text("Create OMR sheet in PDF") == "Create OMR sheet in PDF"
    assert normalize_sentence_text("Recognize OMR image from memorystream") == "Recognize OMR image from MemoryStream"


def test_omr_topics_are_canonicalized_to_readable_developer_titles() -> None:
    cases = {
        "OMR": "",
        "OMR answer scanner": "OMR answer scanner",
        "Create answer sheet OMR sheet": "Create OMR answer sheet",
        "Create OMR survey or answer sheet": "Create OMR survey and answer sheet",
        "Recognize image from memorystream using OMR": "Recognize OMR image from MemoryStream",
        "Scan bubble answer sheet OMR sheet JPG": "Scan OMR bubble answer sheet from JPG",
    }
    for raw, expected in cases.items():
        assert build_content_topic(title=raw) == expected


def test_barcode_topics_are_canonicalized_to_readable_developer_titles() -> None:
    cases = {
        "2d barcode generator generate 2d barcodes or QR codes": "Generate 2D barcodes or QR codes",
        "Barcode": "",
        "Aspose.Barcode solution for all your barcode needs": "",
        "Launch of Aspose.Barcode": "",
        "Barcode generator generate barcode": "Generate barcode",
        "Generate barcodes barcode": "Generate barcodes",
        "Build barcode 93 generator barcode": "Build Code 93 barcode generator",
        "Create micro QR code using QR code": "Create micro QR code",
        "Develop datamatrix barcode generator": "Develop DataMatrix barcode generator",
        "Generate pdf417 barcode using Aspose.Barcode": "Generate PDF417 barcode",
        "JPG QR code reader barcode": "Read QR code from JPG",
        "TXT to QR": "TXT to QR code",
        "Text QR code generator create QR code for text": "Create text QR code",
    }
    for raw, expected in cases.items():
        assert build_content_topic(title=raw) == expected


def test_barcode_acronyms_survive_coverage_display_normalization() -> None:
    assert normalize_sentence_text("generate 2d barcodes or qr codes") == "Generate 2D barcodes or QR codes"
    assert normalize_sentence_text("generate datamatrix barcode") == "Generate DataMatrix barcode"
    assert normalize_sentence_text("generate pdf417 barcode") == "Generate PDF417 barcode"
    assert normalize_sentence_text("generate gs1 128 barcode") == "Generate GS1 128 barcode"


def test_excel_casing_survives_topic_normalization() -> None:
    assert normalize_sentence_text("add comments in excel") == "Add comments in Excel"
    assert build_content_topic(title="Add comments in excel") == "Add comments in Excel"


def test_autofit_excel_rows_and_columns_topics_collapse() -> None:
    expected_topic = "Autofit Excel rows and columns"
    variants = [
        "Auto FIT rows and columns in excel",
        "Auto-Fit Rows and Columns in Excel in Python",
        "Autofit excel rows and columns",
    ]

    assert normalize_sentence_text("Auto FIT rows and columns in excel") == expected_topic
    assert normalize_sentence_text("Autofit excel rows and columns") == expected_topic

    for variant in variants:
        assert canonical_topic_key(variant) == "autofit excel rows and columns"
        assert indexer_canonical_topic_key(variant) == "autofit excel rows and columns"

    assert build_content_topic(title="Auto-Fit Rows and Columns in Excel in Python") == expected_topic
    assert build_content_topic(title="AutoFit Excel Rows and Columns in Java") == expected_topic


def test_fit_image_to_cell_topic_uses_readable_verb_casing() -> None:
    expected_topic = "Fit image to cell width and height"

    assert normalize_sentence_text("FIT image to CELL width and height") == expected_topic
    assert canonical_topic_key("FIT image to CELL width and height") == "fit image to cell width and height"
    assert indexer_canonical_topic_key("FIT image to CELL width and height") == "fit image to cell width and height"
    assert build_content_topic(title="Fit Image to Cell Width and Height using C#") == expected_topic


def test_ml_to_oz_unit_topic_uses_unit_acronyms() -> None:
    expected_topic = "ML to OZ free unit"

    assert normalize_sentence_text("ml to oz free unit") == expected_topic
    assert canonical_topic_key("ML to oz free unit") == "ml to oz free unit"
    assert indexer_canonical_topic_key("ML to oz free unit") == "ml to oz free unit"
    assert build_content_topic(title="Convert ml to oz - Free Unit Converter") == "ML to OZ unit"


def test_best_excel_library_topic_keeps_product_noun() -> None:
    topic = "Aspose.Cells best Excel library for developers"

    assert canonical_topic_key(topic) == "aspose cells best excel library for developers"
    assert indexer_canonical_topic_key(topic) == "aspose cells best excel library for developers"
    assert canonical_topic_key("Aspose.Cells best Excel for developers") != canonical_topic_key(topic)


def test_text_qr_code_is_not_collapsed_to_txt_file_topic() -> None:
    assert canonical_topic_key("Create text QR code") == "create text qr code"
    assert indexer_canonical_topic_key("Create text QR code") == "create text qr code"
    assert canonical_topic_key("Create TXT file") == "create txt"
    assert indexer_canonical_topic_key("Create TXT file") == "create txt"


def test_generic_generate_barcode_topics_collapse_without_losing_specific_topics() -> None:
    duplicate_topics = [
        "Generate barcode",
        "Generate barcodes",
        "Generate barcodes barcode",
        "Generate barcodes barcode API",
    ]

    for topic in duplicate_topics:
        assert canonical_topic_key(topic) == "generate barcodes"
        assert indexer_canonical_topic_key(topic) == "generate barcodes"

    assert canonical_topic_key("Generate barcode 39") == "generate barcode 39"
    assert canonical_topic_key("Generate barcode and QR code with logo") == "generate barcode and qr code with logo"
    assert canonical_topic_key("Generate barcodes with UTF 8 encoding") == "generate barcodes with utf 8 encoding"


def test_pdf_merge_topic_keys_collapse_action_variants() -> None:
    variants = [
        "Merging PDF files programmatically",
        "Merging Multiple PDF Files with Python",
        "Merge Multiple PDF Files in Python",
        "Merge Multiple PDF in Python",
        "How to Merge Multiple PDF Files in C#",
        "Merge Multiple PDF Files into a Single PDF using Java",
        "Merge Two PDF Files in JavaScript",
    ]

    for topic in variants:
        assert canonical_topic_key(topic) == "merge pdf"
        assert indexer_canonical_topic_key(topic) == "merge pdf"

    assert canonical_topic_key("Merge JPG Images to PDF in C#") != "merge pdf"
    assert indexer_canonical_topic_key("Merge JPG Images to PDF in C#") != "merge pdf"


def test_pdf_merge_blog_records_match_across_topic_wording() -> None:
    net_record = IndexRecord(
        id="blog::pdf/merge-multiple-pdf-files-in-csharp-net/index.md",
        repo_key="blog",
        repo_type="blog",
        platform="net",
        title="How to Merge Multiple PDF Files in C#",
        topic="Merging PDF files programmatically",
        category="",
        sub_category="",
    )
    python_record = IndexRecord(
        id="blog::pdf/merge-pdf-files-in-python/index.md",
        repo_key="blog",
        repo_type="blog",
        platform="python",
        title="Merge Multiple PDF Files in Python",
        topic="Merging Multiple PDF Files with Python",
        category="",
        sub_category="",
    )

    assert record_gap_key(net_record) == "merge-pdf"
    assert record_gap_key(python_record) == "merge-pdf"
    assert "merge-pdf" in record_gap_keys(python_record)


def test_blogs_to_blogs_infers_dates_from_blog_slug_for_matching(tmp_path) -> None:
    index_path = tmp_path / "indexes" / "blog" / "all.jsonl"
    index_path.parent.mkdir(parents=True)
    records = [
        {
            "id": "blog::pdf/2020-01-16-merge-multiple-pdf-files-in-csharp-net/index.md",
            "repo_key": "blog",
            "repo_type": "blog",
            "platform": "net",
            "title": "How to Merge Multiple PDF Files in C#",
            "topic": "Merging PDF files programmatically",
            "category": "Document Processing",
            "sub_category": "Pdf Merge",
            "source_path": "pdf/2020-01-16-merge-multiple-pdf-files-in-csharp-net/index.md",
            "url": "https://blog.aspose.com/pdf/merge-multiple-pdf-files-in-csharp-net/",
        },
        {
            "id": "blog::pdf/2023-05-04-merge-pdf-files-in-python/index.md",
            "repo_key": "blog",
            "repo_type": "blog",
            "platform": "python",
            "title": "Merge Multiple PDF Files in Python",
            "topic": "Merging Multiple PDF Files with Python",
            "category": "File Processing",
            "sub_category": "PDF Merging",
            "source_path": "pdf/2023-05-04-merge-pdf-files-in-python/index.md",
            "url": "https://blog.aspose.com/pdf/merge-pdf-files-in-python/",
        },
    ]
    index_path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    result = compute_blogs_to_blogs(
        brand_key="aspose",
        product_key="pdf",
        outputs_product_root=tmp_path,
        baseline_platform=None,
    )

    row = next(row for row in result.rows if row.key == "merge-pdf")
    assert row.coverage["net"]["matched"] is True
    assert row.coverage["python"]["matched"] is True


def test_text_qr_records_match_create_text_qr_key() -> None:
    record = IndexRecord(
        id="blog::barcode/text-to-qr-code-generator-in-csharp/index.md",
        repo_key="blog",
        repo_type="blog",
        platform="net",
        title="Text to QR Code Generator in C#",
        topic="Text to QR code generator",
        category="Barcode",
        sub_category="QR Code Generation",
        key="txt to qr",
    )

    assert record_gap_key(record) == "txt-to-qr"
    assert "create-text-qr-code" in record_gap_keys(record)
    assert "txt-to-qr" in record_gap_keys(record)


def test_omr_sheet_export_skips_generic_acronym_topic(tmp_path) -> None:
    coverage_json = tmp_path / "coverage.json"
    coverage_json.write_text(
        json.dumps(
            {
                "brand_key": "aspose",
                "product_key": "omr",
                "product_name": "Aspose.OMR",
                "baseline_platform": "all",
                "rows": [
                    {
                        "category": "",
                        "sub_category": "",
                        "topic": "OMR",
                        "coverage": {"net": {"matched": True}, "java": {"matched": False}},
                    },
                    {
                        "category": "",
                        "sub_category": "",
                        "topic": "Recognize OMR image from MemoryStream",
                        "coverage": {"net": {"matched": True}, "java": {"matched": False}},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = build_payload(coverage_json=coverage_json, sheet_name="All Missing Topics", replace=False)

    assert payload["meta"]["row_count"] == 1
    assert payload["rows"][0][5] == "Recognize OMR image from MemoryStream"


def test_barcode_sheet_export_skips_generic_and_normalizes_casing(tmp_path) -> None:
    coverage_json = tmp_path / "coverage.json"
    coverage_json.write_text(
        json.dumps(
            {
                "brand_key": "aspose",
                "product_key": "barcode",
                "product_name": "Aspose.BarCode",
                "baseline_platform": "all",
                "rows": [
                    {
                        "category": "",
                        "sub_category": "",
                        "topic": "Barcode",
                        "coverage": {"net": {"matched": True}, "java": {"matched": False}},
                    },
                    {
                        "category": "",
                        "sub_category": "",
                        "topic": "Aspose.Barcode solution for all your barcode needs",
                        "coverage": {"net": {"matched": True}, "java": {"matched": False}},
                    },
                    {
                        "category": "",
                        "sub_category": "",
                        "topic": "generate 2d barcodes or qr codes",
                        "coverage": {"net": {"matched": True}, "java": {"matched": False}},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = build_payload(coverage_json=coverage_json, sheet_name="All Missing Topics", replace=False)

    assert payload["meta"]["row_count"] == 1
    assert payload["rows"][0][5] == "Generate 2D barcodes or QR codes"


def test_cloud_brand_key_is_exported_as_display_name(tmp_path) -> None:
    coverage_json = tmp_path / "coverage.json"
    coverage_json.write_text(
        json.dumps(
            {
                "brand_key": "aspose_cloud",
                "product_key": "pdf",
                "product_name": "Aspose.PDF",
                "baseline_platform": "net",
                "rows": [
                    {
                        "category": "Documents",
                        "sub_category": "PDF",
                        "topic": "Convert PDF to DOCX",
                        "coverage": {"net": {"matched": True}, "java": {"matched": False}},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = build_payload(coverage_json=coverage_json, sheet_name="All Missing Topics", replace=False)

    assert payload["rows"][0][0] == "Aspose.Cloud"
