from __future__ import annotations

import urllib.error
from pathlib import Path

from hugo_blog_audit_agent.auditor import run_audit
from hugo_blog_audit_agent.cli import build_run_metrics, deliver_metrics, write_run_artifacts
from hugo_blog_audit_agent.metrics_api import classify_metrics_api_response, normalized_metrics_payload, send_metrics_api
from hugo_blog_audit_agent.models import BlogConfig
from hugo_blog_audit_agent.reports import write_reports
from tests.helpers import make_repo

def test_deliver_metrics_skips_without_flag(monkeypatch) -> None:
    calls = []
    logs = []
    monkeypatch.setattr("hugo_blog_audit_agent.cli.send_metrics_api", lambda *_args, **_kwargs: calls.append("sent"))

    deliveries = deliver_metrics({"run_id": "skip-test"}, False, logs.append)

    assert calls == []
    assert deliveries == [{"target": "all", "sent": False, "status": "skipped", "reason": "disabled_by_flag"}]
    assert "skipped" in logs[0]

def test_deliver_metrics_sends_with_flag(monkeypatch) -> None:
    logs = []
    expected = [{"target": "team", "sent": True, "status": "success", "reason": ""}]
    monkeypatch.setattr("hugo_blog_audit_agent.cli.send_metrics_api", lambda metrics, log: expected)

    deliveries = deliver_metrics({"run_id": "send-test"}, True, logs.append)

    assert deliveries == expected
    assert "Sending metrics API payload" in logs[0]

def test_run_metrics_and_artifacts_are_written(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("METRICS_JOB_TYPE", raising=False)
    repo = make_repo(tmp_path)
    config = BlogConfig(
        "Test",
        str(repo),
        content_dir="content",
        expected_languages=["en", "fr"],
        website="https://example.com/blog",
    )
    result = run_audit(config, None, "report", None, True, False, tmp_path / "work")
    out = tmp_path / "output"
    write_reports(result, out, include_suggestions=False, draft_fixes=False, max_draft_fixes=None, priority_only=False)
    metrics = build_run_metrics(result, out, "report", None, None, None, True, 0, run_id="test-run")
    write_run_artifacts(out, ["[00:00:00] Test log"], metrics)
    payload = normalized_metrics_payload(metrics)
    assert payload["agent_name"] == "Blog Audit Agent"
    assert payload["agent_owner"] == "Muzammil Khan"
    assert payload["job_type"] == "test"
    assert payload["run_id"] == "test-run"
    assert payload["status"] == "success"
    assert payload["product"] == "Test"
    assert payload["platform"] == "All"
    assert payload["website"] == "https://example.com/blog"
    assert payload["website_section"] == "Blog"
    assert payload["item_name"] == "Blog Posts"
    assert payload["items_discovered"] == 2
    assert payload["items_failed"] == 0
    assert payload["items_succeeded"] == 2
    assert payload["run_duration_ms"] >= 0
    assert payload["token_usage"] == 0
    assert payload["api_calls_count"] == 0
    assert metrics["markdown_files_scanned"] == 2
    assert metrics["include_translations"] is True
    assert metrics["detailed_outputs"] is False
    assert metrics["llm"]["enabled"] is False
    assert metrics["post_date_filter"] == ""
    assert metrics["code_blocks"] == 1
    assert metrics["code_api_issues"] >= 0
    assert metrics["total_issues"] >= metrics["post_issues"]
    assert metrics["reports_written"] == ["audit-action-items.md"]
    assert (out / "audit-run.log").read_text(encoding="utf-8").startswith("[00:00:00] Test log")
    assert (out / "audit-metrics.json").exists()

def test_normalized_metrics_payload_has_required_nonempty_and_nonnegative_fields(monkeypatch) -> None:
    monkeypatch.delenv("METRICS_JOB_TYPE", raising=False)
    payload = normalized_metrics_payload({
        "agent_name": " ",
        "agent_owner": "",
        "job_type": "",
        "run_id": " ",
        "status": "",
        "product": "",
        "platform": "",
        "website": "",
        "website_section": "",
        "item_name": "",
        "items_discovered": -2,
        "items_failed": -1,
        "items_succeeded": -5,
        "run_duration_ms": -100,
        "token_usage": -10,
        "api_calls_count": -3,
    })

    for field in [
        "timestamp",
        "agent_name",
        "agent_owner",
        "job_type",
        "run_id",
        "status",
        "product",
        "platform",
        "website",
        "website_section",
        "item_name",
    ]:
        assert isinstance(payload[field], str)
        assert payload[field].strip()

    for field in [
        "items_discovered",
        "items_failed",
        "items_succeeded",
        "run_duration_ms",
        "token_usage",
        "api_calls_count",
    ]:
        assert payload[field] >= 0

    assert payload["job_type"] == "test"

def test_metrics_sender_uses_aspose_metrics_api_contract(monkeypatch) -> None:
    monkeypatch.setenv("METRICS_API_URL", "")
    monkeypatch.setenv("METRICS_ENDPOINT", "")
    monkeypatch.setenv("ASPOSE_METRICS_API_URL", "")
    monkeypatch.setenv("MUZAMMIL_KHAN_METRICS_API_KEY", "metrics-key")
    monkeypatch.setenv("METRICS_API_KEY", "")
    monkeypatch.setenv("ASPOSE_METRICS_API_KEY", "")
    monkeypatch.setenv("METRICS_JOB_TYPE", "test")
    calls = []

    class FakeResponse:
        status = 202

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{\n  "ok": true,\n  "agent_owner": "Muzammil Khan"\n}'

    def fake_urlopen(request, timeout):
        calls.append({
            "url": request.full_url,
            "method": request.get_method(),
            "headers": dict(request.headers),
            "payload": request.data.decode("utf-8"),
            "timeout": timeout,
        })
        return FakeResponse()

    monkeypatch.setattr("hugo_blog_audit_agent.metrics_api.urllib.request.urlopen", fake_urlopen)
    metrics = {
        "run_id": "run-1",
        "product": "Aspose.Drawing",
        "markdown_files_scanned": 3,
        "duration_seconds": 1.25,
        "llm": {"total_tokens": 42, "api_calls": 2},
    }

    logs = []
    deliveries = send_metrics_api(metrics, logs.append)

    assert [item["target"] for item in deliveries] == ["aspose_metrics_api"]
    assert deliveries[0]["sent"] is True
    assert deliveries[0]["status"] == "success"
    assert deliveries[0]["response_body"] == '{\n  "ok": true,\n  "agent_owner": "Muzammil Khan"\n}'
    assert len(logs) == 2
    assert logs[0].startswith("Metrics API payload: ")
    assert '"agent_owner":"Muzammil Khan"' in logs[0]
    assert '"product":"Aspose.Drawing"' in logs[0]
    assert "metrics-key" not in logs[0]
    assert logs[1] == 'Metrics API sent: delivery=success; status=202; response={"ok":true,"agent_owner":"Muzammil Khan"}'
    assert [call["url"] for call in calls] == ["https://metrics-api.aspose.app/agents"]
    assert calls[0]["method"] == "PUT"
    headers = {key.lower(): value for key, value in calls[0]["headers"].items()}
    assert headers["x-api-key"] == "metrics-key"
    assert "authorization" not in headers
    payload = __import__("json").loads(calls[0]["payload"])
    assert set(payload) == {
        "timestamp",
        "agent_name",
        "agent_owner",
        "job_type",
        "run_id",
        "status",
        "product",
        "platform",
        "website",
        "website_section",
        "item_name",
        "items_discovered",
        "items_failed",
        "items_succeeded",
        "run_duration_ms",
        "token_usage",
        "api_calls_count",
    }
    assert payload["product"] == "Aspose.Drawing"
    assert "token" not in payload
    assert "run_env" not in payload
    assert payload["job_type"] == "test"
    assert payload["items_discovered"] == 3
    assert payload["items_succeeded"] == 3
    assert payload["run_duration_ms"] == 1250.0
    assert payload["token_usage"] == 42
    assert payload["api_calls_count"] == 2

def test_metrics_sender_skips_when_api_key_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("METRICS_API_URL", "https://metrics.test/agents")
    monkeypatch.setenv("MUZAMMIL_KHAN_METRICS_API_KEY", "")
    monkeypatch.setenv("METRICS_API_KEY", "")
    monkeypatch.setenv("ASPOSE_METRICS_API_KEY", "")

    deliveries = send_metrics_api({"run_id": "missing-key-test", "markdown_files_scanned": 1})

    assert deliveries == [{"target": "aspose_metrics_api", "sent": False, "status": "skipped", "reason": "missing_api_key"}]

def test_metrics_api_retries_connection_failures(monkeypatch) -> None:
    monkeypatch.setenv("METRICS_API_URL", "https://metrics.test/agents")
    monkeypatch.setenv("MUZAMMIL_KHAN_METRICS_API_KEY", "metrics-key")
    monkeypatch.setenv("METRICS_API_KEY", "")
    monkeypatch.setenv("ASPOSE_METRICS_API_KEY", "")
    monkeypatch.setenv("METRICS_API_RETRIES", "1")
    calls = []

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"ok"

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise urllib.error.URLError("[Errno 11001] getaddrinfo failed")
        return FakeResponse()

    monkeypatch.setattr("hugo_blog_audit_agent.metrics_api.time.sleep", lambda _seconds: None)
    monkeypatch.setattr("hugo_blog_audit_agent.metrics_api.urllib.request.urlopen", fake_urlopen)

    deliveries = send_metrics_api({"run_id": "retry-test", "markdown_files_scanned": 1})

    assert deliveries[0]["target"] == "aspose_metrics_api"
    assert deliveries[0]["sent"] is True
    assert deliveries[0]["status"] == "success"
    assert deliveries[0]["attempts"] == 2
    assert calls == ["https://metrics.test/agents", "https://metrics.test/agents"]

def test_metrics_api_classifies_application_level_errors() -> None:
    prod = classify_metrics_api_response(
        "prod",
        {
            "status_code": 200,
            "response_body": '{"status":401,"error":"Unauthorized: invalid API key"}',
        },
    )
    team = classify_metrics_api_response(
        "team",
        {
            "status_code": 200,
            "response_body": "Error: Invalid API key",
        },
    )

    assert prod["status"] == "failed"
    assert prod["reason"] == "Unauthorized: invalid API key"
    assert team["status"] == "failed"
    assert team["reason"] == "Error: Invalid API key"
