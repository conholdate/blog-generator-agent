from agent_engine.content_gap_agent.tools.normalization import (
    FILE_FORMAT_REGISTRY,
    canonical_file_format,
    canonical_topic_key,
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
