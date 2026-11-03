import json
from pathlib import Path

from agent_engine.capabilities.extract import (
    STOPWORDS,
    build_format_owners,
    content_hash,
    detect_input_format,
    features_from_spec,
    features_from_words_sdk,
    formats_from_spec,
    load_known_formats,
)

ROOT = Path(__file__).resolve().parents[1]
FORMATS = {"pdf", "docx", "doc", "png", "jpg", "json", "csv", "xlsx", "excel", "pptx", "powerpoint", "dwg", "in", "go"}


# --- detect_input_format -------------------------------------------------

def test_english_word_in_is_never_a_format():
    # POC regression: "in" was read as a format owned by Slides.
    assert detect_input_format("How to handle Conditional formatting in Excel using REST API", FORMATS) == "excel"
    assert detect_input_format("Highlight or Strikeout Text in PDF using Java", FORMATS) == "pdf"


def test_x_to_y_returns_input_format():
    assert detect_input_format("Convert DOCX to PNG in Java", FORMATS) == "docx"
    assert detect_input_format("DWG to PDF Conversion in Java", FORMATS) == "dwg"


def test_unknown_source_format_falls_back_to_first_known():
    # "tsv" isn't a known format here, so the first known one wins.
    assert detect_input_format("Convert TSV to JSON Using C# .NET", FORMATS) == "json"


def test_programming_language_names_are_not_formats():
    assert detect_input_format("Resize images in Go", FORMATS) is None


def test_no_format_returns_none():
    assert detect_input_format("Send emails via SMTP", FORMATS) is None
    assert detect_input_format("", FORMATS) is None


# --- spec parsing --------------------------------------------------------

SPEC = {
    "paths": {
        "/imaging/{name}/grayscale": {"get": {"operationId": "GrayscaleImage", "summary": "Grayscale an image."}},
        "/imaging/{name}/convert": {"get": {"operationId": "ConvertImage", "summary": "Convert image to another format, e.g. PNG or JPG.",
                                            "parameters": [{"name": "format", "enum": ["Bmp", "Tiff"]}]}},
        "/imaging/storage/file/{path}": {"get": {"operationId": "DownloadFile", "summary": "Download file"}},
        "/imaging/storage/exist/{path}": {"get": {"operationId": "ObjectExists"}},
        "/imaging/in/{name}": {"get": {"operationId": "Odd", "summary": "works in any case"}},
    }
}


def test_features_skip_storage_endpoints():
    ids = [f["id"] for f in features_from_spec(SPEC, "imaging")]
    assert "imaging:GrayscaleImage" in ids and "imaging:ConvertImage" in ids
    assert "imaging:DownloadFile" not in ids and "imaging:ObjectExists" not in ids


def test_feature_text_has_operation_summary_and_path():
    feat = next(f for f in features_from_spec(SPEC, "imaging") if f["id"] == "imaging:GrayscaleImage")
    assert feat["text"] == "GrayscaleImage: Grayscale an image. (GET /imaging/{name}/grayscale)"


def test_spec_formats_use_enums_and_uppercase_only():
    known = {"png", "jpg", "bmp", "tiff", "any", "image", "in"}
    fmts = formats_from_spec(SPEC, known)
    assert set(fmts) == {"png", "jpg", "bmp", "tiff"}  # "any"/"in" prose and path segment ignored


# --- Words SDK parsing ---------------------------------------------------

SDK_SOURCE = '''
class WordsApi(object):
    def __init__(self, api_client):
        pass

    def convert_document(self, request, **kwargs):  # noqa: E501
        """Converts a document on a local drive to the specified format.  # noqa: E501

        More text.
        """
        pass

    def convert_document_with_http_info(self, request, **kwargs):
        """Converts (variant)."""

    def insert_watermark_online(self, request, **kwargs):
        """Online variant."""

    def insert_watermark(self, request, **kwargs):
        """Insert a watermark to the document."""

    def copy_file(self, request, **kwargs):
        """Copy file."""
'''


def test_words_sdk_methods_parsed_without_variants_or_storage():
    feats = features_from_words_sdk(SDK_SOURCE)
    assert [f["id"] for f in feats] == ["words:convert_document", "words:insert_watermark"]
    assert feats[0]["text"] == "convert_document: Converts a document on a local drive to the specified format."


# --- ownership / hash / real config --------------------------------------

def test_format_owners_drop_stopwords_and_sort():
    owners = build_format_owners({"slides": ["pptx", "in", "pdf"], "pdf": ["pdf", "docx"], "cells": ["xlsx", "pdf"]})
    assert "in" not in owners
    assert owners["pdf"] == ["cells", "pdf", "slides"]
    assert owners["pptx"] == ["slides"]


def test_content_hash_is_stable_and_sensitive():
    feats = [{"id": "a:b", "text": "x"}]
    assert content_hash(feats, ["pdf"]) == content_hash([{"text": "x", "id": "a:b"}], ["pdf"])
    assert content_hash(feats, ["pdf"]) != content_hash(feats, ["pdf", "png"])


def test_real_known_formats_exclude_stopwords():
    known = load_known_formats(json.loads((ROOT / "configs" / "file_formats.json").read_text()))
    assert {"pdf", "docx", "xlsx", "pptx"} <= known
    assert not (known & STOPWORDS)


# --- reference links (formats confirmed in a real browser 2026-11-04) ------

from agent_engine.capabilities.extract import operation_reference_url  # noqa: E402
from agent_engine.capabilities.spec_sources import parse_reference_page, url_version  # noqa: E402

IMAGING_REF = "https://reference.aspose.cloud/imaging/"
CELLS_REF = "https://reference.aspose.cloud/cells/"


def test_deep_link_single_spec_page():
    assert operation_reference_url(IMAGING_REF, None, "Resize", "CreateResizedImage") == \
        "https://reference.aspose.cloud/imaging/#/Resize/CreateResizedImage"


def test_deep_link_multi_spec_page_selects_spec():
    assert operation_reference_url(CELLS_REF, "API v4", "Conversion", "ConvertSpreadsheet") == \
        "https://reference.aspose.cloud/cells/?urls.primaryName=API%20v4#/Conversion/ConvertSpreadsheet"


def test_no_tag_or_operation_id_falls_back_to_page():
    assert operation_reference_url(IMAGING_REF, None, "", "CreateResizedImage") == IMAGING_REF
    assert operation_reference_url("", None, "Resize", "X") == ""


def test_spec_features_keep_tag_for_links():
    spec = {"paths": {"/imaging/resize": {"post": {"operationId": "CreateResizedImage", "tags": ["Resize"], "summary": "Resize"}}}}
    feat = features_from_spec(spec, "imaging")[0]
    assert (feat["_tag"], feat["_operationId"]) == ("Resize", "CreateResizedImage")


def test_parse_reference_page_multi_spec():
    html = '''deepLinking: true,
        urls: [
          { url: "https://api.aspose.cloud/v4.0/barcode/swagger/spec", name: "Aspose.BarCode.Cloud v4.0" },
          { url: "https://api.aspose.cloud/v3.0/barcode/swagger/spec", name: "Aspose.BarCode.Cloud v3.0" }
        ],'''
    page = parse_reference_page(html, "https://reference.aspose.cloud/barcode/")
    assert page.deep_linking is True
    assert page.specs[0] == ("https://api.aspose.cloud/v4.0/barcode/swagger/spec", "Aspose.BarCode.Cloud v4.0")


def test_parse_reference_page_single_spec_and_no_deeplink():
    html = 'url: "https://api.aspose.cloud/v5.1/ocr/swagger/v5/swagger.json", dom_id: "#swagger-ui"'
    page = parse_reference_page(html, "https://reference.aspose.cloud/ocr/")
    assert page.deep_linking is False
    assert page.specs == [("https://api.aspose.cloud/v5.1/ocr/swagger/v5/swagger.json", None)]


def test_url_version():
    assert url_version("https://api.aspose.cloud/v5.1/omr/swagger.json") == "v5.1"
    assert url_version("https://api.aspose.cloud/v4.0/cells/swagger/spec") == "v4.0"
