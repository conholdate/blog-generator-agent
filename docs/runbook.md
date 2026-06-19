# Runbook

## Local Report Run

Install the package and run:

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --mode report
```

For a product and post date:

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --product Aspose.blog/barcode --post-date 2026-06-05 --include-translations false --mode report --verbose
```

## Container Run

Build the runtime image:

```bash
docker build -t hugo-blog-audit-agent .
```

Run with the current repository mounted as `/workspace`:

```bash
docker run --rm -v "${PWD}:/workspace" hugo-blog-audit-agent --blog-config /workspace/configs/aspose.yaml --mode report
```

The image uses Python `3.11.9-slim-bookworm`, installs the CLI package, includes Git for configured repository clones, and runs as a non-root user.

## Expected Outputs

The default output directory is `outputs/audit/<blog>/`.

Expected files:

- `audit-action-items.md`
- `audit-run.log`
- `audit-metrics.json`

When `--detailed-outputs true` is used, additional Markdown, CSV, and JSON reports are generated.

## Operational Checks

After a run, verify:

- `audit-metrics.json` has `status: success`
- `markdown_files_scanned` is greater than zero for non-empty scopes
- `total_issues` and severity counts match expectations for the selected scope
- `audit-run.log` includes each major phase
- generated draft fixes, if enabled, are under `draft-fixes/`

## Common Failures

Repository clone fails:

- confirm the repository URL and branch
- confirm local Git credentials or the GitHub Actions secret used for private repositories

No Markdown files scanned:

- confirm `content_dir`
- confirm `--product`, `--post-date`, `--languages`, and `--include-translations` filters

LLM suggestions missing:

- confirm `--llm-suggestions true` or `llm.enabled: true`
- confirm provider URL, API key, model, timeout, and retry settings
- check `llm` metrics in `audit-metrics.json`

Metrics API failure:

- confirm `--send-metrics true`
- confirm `MUZAMMIL_KHAN_METRICS_API_KEY` is available in the environment
- check the `metrics_api` entry in `audit-metrics.json`

## Incident Handling

If a run sends data to the wrong external endpoint, revoke the affected credential, disable the workflow or flag, inspect `audit-run.log` and workflow logs, and rotate any exposed tokens.

If generated reports are wrong, keep the source blog unchanged, preserve the output directory for investigation, and reproduce with the same config and CLI flags.
