from agent_engine.content_gap_agent.tools.normalization import (
    FILE_FORMAT_REGISTRY,
    canonical_file_format,
    canonical_topic_key,
    normalize_sentence_text,
)
from agent_engine.content_gap_agent.tools.coverage.blogs_to_blogs import record_gap_key, record_gap_keys
from agent_engine.content_gap_agent.tools.io import IndexRecord
from agent_engine.content_indexer_agent.tools.key_maker import build_content_topic


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
    assert build_content_topic(title="C# Optical Mark Recognition (OMR) Software in .NET") == "Optical mark recognition OMR"
    assert build_content_topic(title="Create OMR sheet in PDF free and") == "Create OMR sheet in PDF"
    assert build_content_topic(title="Omr sheet reader omr sheet PNG") == "Read OMR sheet from PNG"
    assert build_content_topic(title="Omr scanner the ultimate free answer scanner") == "OMR answer scanner"
    assert build_content_topic(title="Scan survey free omr") == "Scan survey OMR"


def test_non_omr_grade_calculator_topics_are_rejected() -> None:
    assert build_content_topic(title="Calculate cgpa online grades calculator") == ""
    assert build_content_topic(title="Grade calculator free letter grading calculator") == ""


def test_omr_acronym_survives_coverage_display_normalization() -> None:
    key = canonical_topic_key("Optical mark recognition OMR")
    assert key == "optical mark recognition omr"
    assert normalize_sentence_text(key) == "Optical mark recognition OMR"
