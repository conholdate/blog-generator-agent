# Beta Evidence Log

Use this log to record release-candidate evidence from real or representative Hugo blog runs. Do not mark a run complete unless the artifacts are retained and reviewable.

## Run Matrix

| Date | Repo / Fixture | Source Type | Scope | Command / Workflow | Required Artifacts | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TODO | Mini Hugo fixture | Local fixture | end-to-end, translations included | `python -m pytest tests/test_e2e.py` | pytest output | Pending | Automated fixture coverage exists; attach CI run URL after merge. |
| TODO | Representative Hugo blog 1 | Local path | full report | TODO | `audit-action-items.md`, `audit-run.log`, `audit-metrics.json` | Pending | Fill after first beta run. |
| TODO | Representative Hugo blog 2 | Remote clone | product scoped with SDK/API validation | TODO | `audit-action-items.md`, `code-audit.md`, `audit-metrics.json` | Pending | Fill after first remote clone run. |
| TODO | Representative Hugo blog 3 | GitHub Actions manual dispatch | multilingual, detailed outputs | TODO | workflow URL, uploaded artifact, metrics summary | Pending | Fill after first workflow run. |
| TODO | Container runtime | Mounted workspace | default report | `docker run --rm -v "${PWD}:/workspace" hugo-blog-audit-agent --blog-config /workspace/configs/aspose.yaml --mode report` | Docker build log, output files | Pending | Requires working Docker Linux engine. |
| TODO | Metrics API test endpoint | Local or CI | metrics API enabled with `METRICS_JOB_TYPE=test` | TODO | `audit-metrics.json`, endpoint response log | Pending | Use test job type so submitted data can be filtered later. |
| TODO | LLM test provider or mock | Local or CI | LLM suggestions enabled | TODO | `audit-action-items.md`, LLM metrics | Pending | Do not use production content until data handling is approved. |

## Evidence Checklist Per Run

- Command, workflow URL, or CI job URL is recorded.
- Config path and filters are recorded.
- `audit-run.log` is retained.
- `audit-metrics.json` is retained.
- `audit-action-items.md` is retained.
- Detailed reports are retained when `--detailed-outputs true` is used.
- Any external integrations enabled are listed.
- Any skipped phases or failed deliveries are explained.
- Source Markdown changes are confirmed as absent unless a human applied draft fixes manually.

## Release-Candidate Evidence Summary

Before declaring release-candidate readiness, replace the TODO rows above with real evidence and confirm:

- At least three distinct Hugo blog repositories or representative fixtures have successful runs.
- At least one run uses a remote clone.
- At least one run uses SDK/API validation.
- At least one run includes translations.
- At least one run excludes translations with index-only scanning.
- At least one GitHub Actions manual audit run uploads artifacts.
- At least one Docker build and container run succeeds.
- At least one metrics API run succeeds with `METRICS_JOB_TYPE=test`.
- At least one optional LLM run succeeds against a mock or approved test provider.
