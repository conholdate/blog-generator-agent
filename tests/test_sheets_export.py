from __future__ import annotations

import pytest

from agent_engine.content_gap_agent.tools.sheets_export import (
    is_successful_sheet_response,
    post_payload,
    resolve_sheet_config,
    validate_sheets_webhook_url,
)


VALID_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxExampleDeploymentId/exec"


def test_validate_sheets_webhook_url_accepts_apps_script_exec_url() -> None:
    ok, reason = validate_sheets_webhook_url(VALID_APPS_SCRIPT_URL)

    assert ok is True
    assert reason == ""


@pytest.mark.parametrize(
    "url",
    [
        "https://docs.google.com/spreadsheets/d/spreadsheet-id/edit",
        "https://drive.google.com/file/d/file-id/view",
        "https://script.google.com/macros/s/AKfycbxExampleDeploymentId/dev",
        "https://example.com/webhook",
    ],
)
def test_validate_sheets_webhook_url_rejects_non_web_app_urls(url: str) -> None:
    ok, reason = validate_sheets_webhook_url(url)

    assert ok is False
    assert "webhook_url" in reason


def test_post_payload_rejects_invalid_webhook_url_before_network(monkeypatch) -> None:
    def fail_post(*_args, **_kwargs):
        raise AssertionError("requests.post should not be called for an invalid webhook_url")

    monkeypatch.setattr("agent_engine.content_gap_agent.tools.sheets_export.requests.post", fail_post)

    status, text = post_payload(
        {"headers": [], "rows": [], "meta": {"row_count": 1}},
        "https://docs.google.com/spreadsheets/d/spreadsheet-id/edit",
        token=None,
    )

    assert status == 0
    assert "Use the Apps Script Web App URL" in text


def test_sheet_response_404_google_docs_page_has_actionable_reason() -> None:
    ok, reason = is_successful_sheet_response(
        404,
        '<!DOCTYPE html><html><head><title>Page Not Found</title></head><body>docs.google.com</body></html>',
    )

    assert ok is False
    assert "Apps Script deployment URL" in reason
    assert "/exec URL" in reason


def test_legacy_webhook_override_can_be_detected_as_invalid() -> None:
    class Settings:
        TOPICS_SHEETS = {"aspose": {"webhook_url": VALID_APPS_SCRIPT_URL}}
        TOPICS_SHEETS_TOKEN = ""
        TOPICS_ASPOSE_COM_WEBHOOK_URL = "https://docs.google.com/spreadsheets/d/spreadsheet-id/edit"
        TOPICS_ASPOSE_COM_COVERAGE_JSON = ""
        TOPICS_ASPOSE_COM_TOKEN = ""

    cfg = resolve_sheet_config(Settings(), "aspose")

    assert cfg["webhook_url"].startswith("https://docs.google.com/")
    ok, reason = validate_sheets_webhook_url(cfg["webhook_url"])
    assert ok is False
    assert "Google Docs/Drive" in reason
