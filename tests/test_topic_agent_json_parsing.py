from agent_engine.blog_keyword_analyzer.agents.base_topic_agent import KeywordResearchAgent


def test_parse_topics_payload_accepts_fenced_json_object() -> None:
    payload = KeywordResearchAgent._parse_topics_payload(
        '```json\n{"topics":[{"title":"Create Surveys in .NET"}]}\n```'
    )

    assert payload == {"topics": [{"title": "Create Surveys in .NET"}]}


def test_parse_topics_payload_extracts_object_from_prose() -> None:
    payload = KeywordResearchAgent._parse_topics_payload(
        'Here is the result:\n{"topics":[{"title":"Create Survey Forms in .NET"}]}'
    )

    assert payload == {"topics": [{"title": "Create Survey Forms in .NET"}]}


def test_parse_topics_payload_wraps_bare_topics_array() -> None:
    payload = KeywordResearchAgent._parse_topics_payload(
        '[{"title":"Generate OMR Sheets in .NET"}]'
    )

    assert payload == {"topics": [{"title": "Generate OMR Sheets in .NET"}]}


def test_parse_topics_payload_rejects_non_json_text() -> None:
    assert KeywordResearchAgent._parse_topics_payload("I cannot complete that request.") is None
