# Beta Validation Evidence

This document records the evidence currently available for the Hugo Blog Audit Agent beta. It is intended to make the tested operating envelope explicit rather than implying broad production validation.

Validation date: 2026-06-16

## Current Beta Claim

The agent is validated as a local and GitHub Actions oriented audit tool for Hugo blog repositories. It can scan configured Markdown content, apply heuristic and policy-backed checks, validate links/translations/product context/API references, and write audit reports without modifying source posts.

The beta is not yet validated as a hosted service, autonomous remediation system, rendered-site crawler, or publish pipeline.

## Known Tested Repository Shapes

The current automated test suite covers these repository shapes:

- Local Hugo-style repository with `hugo.yaml`, `content/`, `layouts/`, source `index.md`, and translated `index.fr.md` files.
- Product-scoped content paths such as `content/Aspose.blog/words/sample-post/index.md`.
- Product filters using forward-slash paths, for example `Aspose.blog/words`.
- Date-filtered posts where the date can come from front matter or from a dated path.
- Index-only scans that exclude translated Markdown files.
- Hugo repositories with front matter images, Markdown images, figure shortcodes, links, code fences, headings, and FAQ-like sections.
- Product-aware configs with `product_config_dir`, known product mentions, file-format aliases, money pages, documentation pages, and platform definitions.
- SDK/API validation using configured packages and local API reference repositories.
- Optional LLM suggestion flow using the mock provider and cache behavior.
- Metrics API delivery using mocked HTTP calls, `X-Api-Key` authentication, retry behavior, required payload validation, and failure classification.
- Report generation with default action-items output, detailed report output, and draft-fix scaffolds.

The repository also includes a real shared Aspose-style config shape under `configs/aspose.yaml` and product configs under `configs/aspose/`.

## Verified Commands

These commands passed locally on 2026-06-16:

```bash
python -m compileall agent_engine tests
```

Result: package and test modules compiled successfully.

```bash
python -m pytest
```

Result: 59 tests passed.

```bash
python -m ruff check agent_engine tests
```

Result: all lint checks passed.

```bash
python -m pytest --cov=hugo_blog_audit_agent --cov-report=term-missing --cov-report=xml
```

Result: 59 tests passed, 74.03% total coverage, above the configured 70% threshold.

```bash
python -m pip_audit -r requirements.txt
```

Result: no known vulnerabilities found in runtime requirements.

The test suite is split across scanner, policy evaluator, reports, metrics API delivery, CLI/config, SDK validation, LLM cache, and end-to-end fixture modules.

## Container Evidence

A pinned runtime image is defined in `Dockerfile` using `python:3.11.9-slim-bookworm`. The image installs the package, includes Git for configured repository clones, runs as a non-root user, and uses `/workspace` for mounted configs, repositories, and outputs.

The Docker build command is:

```bash
docker build -t hugo-blog-audit-agent .
```

The Dockerfile was added and statically reviewed. A local image build could not be completed in this environment because Docker Desktop's Linux engine pipe was unavailable. This remains a runtime environment limitation, not a known Dockerfile failure.

## Successful Run Examples

Default local report:

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --mode report
```

Product-scoped report:

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --product Aspose.blog/barcode --mode report
```

Product and post-date scoped report:

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --product Aspose.blog/barcode --post-date 2026-06-05 --include-translations false --mode report --verbose
```

Detailed report output:

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --mode report --detailed-outputs true
```

Draft-fix scaffolds:

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --mode report-with-draft-fixes --max-draft-fixes 5 --priority-only true
```

Container run with a mounted workspace:

```bash
docker run --rm -v "${PWD}:/workspace" hugo-blog-audit-agent --blog-config /workspace/configs/aspose.yaml --mode report
```

## Expected Output Files

Default report mode writes:

- `audit-action-items.md`
- `audit-run.log`
- `audit-metrics.json`

Detailed output mode also writes:

- `audit-summary.md`
- `complete-seo-audit.md`
- `code-audit.md`
- `post-audit.csv`
- `post-audit.json`
- `technical-seo-audit.md`
- `internal-linking-audit.md`
- `content-improvement-plan.md`
- `quick-wins.md`

Draft-fix mode also writes:

- `draft-fixes/index.csv`
- draft Markdown files under `draft-fixes/`

By default, outputs are placed under `outputs/audit/<blog>/` when the config output directory is `outputs`.

## Runtime Evidence to Capture Per Beta Run

Record beta runs in `docs/beta-evidence-log.md`.

For each beta run, retain:

- CLI command or GitHub Actions run URL.
- Blog config path and product/date/language filters.
- `audit-run.log`.
- `audit-metrics.json`.
- The generated `audit-action-items.md`.
- Whether detailed outputs, LLM suggestions, metrics API delivery, or draft fixes were enabled.
- Any skipped phases, clone failures, or metrics API/LLM errors from metrics.

Minimum success criteria:

- `audit-metrics.json` reports `status: success`.
- `markdown_files_scanned` is greater than zero for the intended scope.
- `audit-action-items.md` exists.
- `audit-run.log` includes repository prep, policy loading, scan, audit phases, scoring, and report writing.
- Source Markdown files are unchanged unless a human intentionally applies a draft fix outside the agent.

## Known Limitations

- The agent analyzes repository files, not rendered pages from a live website.
- It does not run Hugo builds or validate final rendered HTML.
- Link checks are local/static and do not guarantee deployed URL status.
- SDK/API validation is static and does not compile or execute code snippets.
- API reference repository coverage depends on configured docs and clone availability.
- Translation checks detect coverage and structure issues, not full linguistic quality.
- LLM suggestions are advisory and require human review.
- Metrics API delivery and LLM calls are optional external integrations and depend on endpoint credentials, timeout settings, and network availability.
- Docker runtime validation requires a working Docker Linux engine.

## Common Failure Modes

No Markdown files scanned:

- `content_dir` points to the wrong folder.
- `--product`, `--post-date`, `--languages`, or `--include-translations` filters exclude the intended files.
- The configured repository root is not the Hugo project root.

Repository clone failure:

- Remote URL or branch is invalid.
- Git is unavailable in the runtime environment.
- Private repository credentials are missing or lack read access.

Policy loading failure:

- A configured policy path is wrong after moving between local and CI paths.
- YAML syntax is invalid.
- A rule uses an unsupported condition operator.

SDK/API reference skip:

- API reference repository cannot be cloned or opened.
- Product config does not include the expected platform path.
- Reference docs do not contain the needed class/member symbols.

LLM suggestion failure:

- LLM suggestions are not explicitly enabled.
- API key, base URL, or model environment variables are missing.
- Provider response is not valid JSON.
- Timeout/retry settings are too low for the provider.

Metrics API failure:

- `--send-metrics true` was not passed.
- `MUZAMMIL_KHAN_METRICS_API_KEY` is missing.
- Endpoint returns an application-level authorization error.

Docker run failure:

- Docker Desktop or Linux containers are not running.
- Mounted workspace path is invalid for the host shell.
- Mounted output directory is not writable by the container user.

## Beta Exit Criteria

Before calling the agent release-candidate ready, collect evidence for:

- At least three distinct Hugo blog repositories or representative fixtures.
- One local path run and one remote clone run.
- One product-scoped run with SDK/API validation.
- One multilingual run with translations included.
- One index-only run with translations excluded.
- One GitHub Actions manual run that uploads artifacts.
- One container build and containerized report run.
- One run with optional LLM suggestions enabled against a non-production test provider or mock.
- One metrics API run against the configured endpoint using `METRICS_JOB_TYPE=test`.

Each run should preserve metrics, logs, and action-item reports for review.
