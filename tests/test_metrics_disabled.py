from types import SimpleNamespace

from agent_engine.content_gap_agent.tools.metrics import MetricsRun as GapMetricsRun
from agent_engine.content_gap_agent.tools.metrics import MetricsSender as GapMetricsSender
from agent_engine.content_indexer_agent.tools.metrics import MetricsRun as IndexerMetricsRun
from agent_engine.content_indexer_agent.tools.metrics import MetricsSender as IndexerMetricsSender


def _disabled_settings() -> SimpleNamespace:
    return SimpleNamespace(
        METRICS_ENABLED=False,
        METRICS_REQUIRED=False,
        METRICS_TIMEOUT_S=1,
        METRICS_WEBHOOK_URL="https://example.invalid/metrics",
        METRICS_TOKEN="token",
        METRICS_AGENT_NAME="Test Agent",
        METRICS_AGENT_OWNER="Test Owner",
        INT_METRICS_WEBHOOK_URL="",
        INT_METRICS_TOKEN="",
    )


def _run_disabled_metrics_context(run_cls, sender_cls) -> None:
    sender = sender_cls(settings=_disabled_settings())
    with run_cls(
        sender=sender,
        run_id="test-run",
        job_type="Test",
        product="Aspose.Cells",
        platform=".NET",
        website="aspose.com",
        website_section="Blog",
        item_name="Articles",
    ):
        pass


def test_disabled_metrics_context_does_not_emit_payload(capsys) -> None:
    _run_disabled_metrics_context(IndexerMetricsRun, IndexerMetricsSender)
    _run_disabled_metrics_context(GapMetricsRun, GapMetricsSender)

    out = capsys.readouterr().out
    assert "disabled (METRICS_ENABLED=False)" in out
    assert "payload before send" not in out
    assert "example.invalid" not in out
