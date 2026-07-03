import json

from agent_engine.blog_keyword_analyzer.agents.base_topic_agent import KeywordResearchAgent
from agent_engine.blog_keyword_analyzer.schemas import Cluster, ClusterMetrics, KeywordRecord
from agent_engine.blog_keyword_analyzer.tools.normalization import seo_platform_label


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


def test_net_topic_generation_uses_csharp_in_seo_title(monkeypatch) -> None:
    def fake_call(self, request_kwargs, *, metrics, attempt_label):
        return json.dumps(
            {
                "topics": [
                    {
                        "cluster_id": "c1",
                        "title": "Convert PDF to DOCX in .NET",
                        "angle": "Developer tutorial",
                        "outline": ["Overview", "Setup", "Implementation", "Validation"],
                        "target_persona": ".NET developers",
                        "primary_keyword": "convert pdf to docx in .net",
                        "supporting_keywords": [
                            "pdf to docx conversion",
                            "convert pdf files",
                            "docx export workflow",
                        ],
                        "keyword_groups": {
                            "core_seo_keywords": ["pdf to docx conversion"],
                            "long_tail_keywords": ["convert pdf files to docx"],
                            "context_keywords": ["document conversion"],
                        },
                        "editorial_notes": [],
                        "internal_links": [],
                    }
                ]
            }
        )

    monkeypatch.setattr(KeywordResearchAgent, "_call_topic_llm", fake_call)
    monkeypatch.setattr(
        "agent_engine.blog_keyword_analyzer.agents.base_topic_agent.polish_title",
        lambda *args, **kwargs: None,
    )

    agent = KeywordResearchAgent()
    topics = agent.generate_topics(
        brand="Aspose",
        product="Aspose.PDF",
        locale="en-US",
        clusters=[
            Cluster(
                cluster_id="c1",
                label="PDF conversion",
                metrics=ClusterMetrics(score=1.0),
                members=[
                    KeywordRecord(
                        keyword="convert pdf to docx in .net",
                        source="upload",
                        locale="en-US",
                    )
                ],
            )
        ],
        top_n=1,
        platform="net",
        include_product_in_title=False,
    )

    assert seo_platform_label("net") == "C#"
    assert len(topics) == 1
    assert "C#" in topics[0].title
    assert ".NET" not in topics[0].title
    assert topics[0].primary_keyword.endswith("in C#")
