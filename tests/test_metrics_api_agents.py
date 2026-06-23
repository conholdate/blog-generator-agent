from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent_engine.blog_keyword_analyzer import metrics_sender as keyword_metrics
from agent_engine.content_gap_agent.tools import metrics as gap_metrics
from agent_engine.content_indexer_agent.tools import metrics as indexer_metrics


def _settings(agent_name: str) -> SimpleNamespace:
    return SimpleNamespace(
        METRICS_ENABLED=True,
        METRICS_REQUIRED=False,
        METRICS_TIMEOUT_S=1,
        METRICS_WEBHOOK_URL="",
        METRICS_TOKEN="",
        METRICS_AGENT_NAME=agent_name,
        METRICS_AGENT_OWNER="Muzammil Khan",
        INT_METRICS_WEBHOOK_URL="",
        INT_METRICS_TOKEN="",
        DEBUG=False,
    )


@pytest.mark.parametrize(
    ("module", "sender_cls", "run_cls", "agent_name"),
    [
        (gap_metrics, gap_metrics.MetricsSender, gap_metrics.MetricsRun, "Content Gap Agent"),
        (indexer_metrics, indexer_metrics.MetricsSender, indexer_metrics.MetricsRun, "Content Indexer Agent"),
    ],
)
def test_metrics_run_sends_to_api_without_webhook_config(monkeypatch, module, sender_cls, run_cls, agent_name) -> None:
    calls: list[dict[str, object]] = []

    def fake_send_metrics_api(payload, log=None, *, allow_job_type_env_override=True):
        calls.append(
            {
                "payload": dict(payload),
                "allow_job_type_env_override": allow_job_type_env_override,
            }
        )
        return [{"target": "aspose_metrics_api", "sent": True, "status": "success", "reason": ""}]

    monkeypatch.setattr(module, "send_metrics_api", fake_send_metrics_api)

    sender = sender_cls(settings=_settings(agent_name))
    with run_cls(
        sender=sender,
        run_id="test-run",
        job_type="Content Indexing",
        product="Aspose.Words",
        platform=".NET",
        website="aspose.com",
        website_section="Blog",
        item_name="Articles",
    ) as metrics:
        metrics.set_counts(discovered=4, succeeded=3, failed=1)
        metrics.set_usage(token_usage=25, api_calls_count=2)

    assert len(calls) == 1
    payload = calls[0]["payload"]
    assert calls[0]["allow_job_type_env_override"] is True
    assert payload["agent_name"] == agent_name
    assert payload["agent_owner"] == "Muzammil Khan"
    assert payload["job_type"] == "Content Indexing"
    assert payload["run_id"] == "test-run"
    assert payload["status"] == "success"
    assert payload["product"] == "Aspose.Words"
    assert payload["items_discovered"] == 4
    assert payload["items_succeeded"] == 3
    assert payload["items_failed"] == 1
    assert payload["token_usage"] == 25
    assert payload["api_calls_count"] == 2
    assert "run_env" not in payload
    assert "token" not in payload


@pytest.mark.parametrize(
    ("module", "sender_cls", "run_cls"),
    [
        (gap_metrics, gap_metrics.MetricsSender, gap_metrics.MetricsRun),
        (indexer_metrics, indexer_metrics.MetricsSender, indexer_metrics.MetricsRun),
    ],
)
def test_metrics_required_raises_when_api_delivery_fails(monkeypatch, module, sender_cls, run_cls) -> None:
    def fake_send_metrics_api(payload, log=None, *, allow_job_type_env_override=True):
        return [{"target": "aspose_metrics_api", "sent": False, "status": "skipped", "reason": "missing_api_key"}]

    monkeypatch.setattr(module, "send_metrics_api", fake_send_metrics_api)
    settings = _settings("Required Metrics Agent")
    settings.METRICS_REQUIRED = True
    sender = sender_cls(settings=settings)

    with pytest.raises(RuntimeError, match="missing_api_key"):
        with run_cls(
            sender=sender,
            run_id="required-test",
            job_type="Content Gap Analysis",
            product="Aspose.Words",
            platform=".NET",
            website="aspose.com",
            website_section="Blog",
            item_name="Articles",
        ):
            pass


def test_keyword_stage_metrics_sends_to_api_without_webhook_config(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_send_metrics_api(payload, log=None, *, allow_job_type_env_override=True):
        calls.append(
            {
                "payload": dict(payload),
                "allow_job_type_env_override": allow_job_type_env_override,
            }
        )
        return [{"target": "aspose_metrics_api", "sent": True, "status": "success", "reason": ""}]

    monkeypatch.setenv("METRICS_ENABLED", "true")
    monkeypatch.setattr(keyword_metrics, "send_metrics_api", fake_send_metrics_api)

    keyword_metrics.send_stage_metrics(
        settings=_settings("Blog Keyword Analyzer"),
        run_id="keyword-run",
        stage="Keyword Clustering",
        stage_status="success",
        req=SimpleNamespace(product="Aspose.PDF"),
        platform="net",
        website="aspose.com",
        section="Blog",
        run_duration_ms=500,
        stage_duration_ms=125,
        item_name="Keywords",
        items_discovered=10,
        items_succeeded=8,
        items_failed=2,
        llm_requests=3,
        llm_total_tokens=99,
        extra_fields={"clusters_created": 4},
    )

    assert len(calls) == 1
    payload = calls[0]["payload"]
    assert calls[0]["allow_job_type_env_override"] is True
    assert payload["agent_name"] == "Blog Keyword Analyzer"
    assert payload["agent_owner"] == "Muzammil Khan"
    assert payload["job_type"] == "Keyword Clustering"
    assert payload["run_id"] == "keyword-run"
    assert payload["status"] == "success"
    assert payload["product"] == "Aspose.PDF"
    assert payload["platform"] == ".NET"
    assert payload["items_discovered"] == 10
    assert payload["items_succeeded"] == 8
    assert payload["items_failed"] == 2
    assert payload["api_calls_count"] == 3
    assert payload["token_usage"] == 99
    assert "run_env" not in payload
    assert "token" not in payload
