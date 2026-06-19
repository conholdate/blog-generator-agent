# Hugo Blog Audit Agent Architecture

This document defines the orchestration boundaries, state model, control flow, side effects, and extension points for the Hugo Blog Audit Agent.

## Runtime Shape

The agent is a bounded local orchestration tool. It does not plan dynamically, delegate to other agents, crawl live websites, publish source content, or mutate blog posts. The main control path is deterministic and lives in `hugo_blog_audit_agent.auditor.run_audit`.

The CLI entrypoint in `hugo_blog_audit_agent.cli.main` is responsible for:

- parsing command-line options
- loading the blog configuration
- applying CLI overrides for optional LLM behavior
- selecting the output directory
- calling `run_audit`
- writing reports, logs, and metrics
- optionally sending metrics to the metrics API

## Control Flow

The audit run proceeds in this order:

1. Load policy files from the configured `policy_files`.
2. Prepare the repository source from a local path or remote Git URL.
3. Detect Hugo project files and language structure.
4. Scan Markdown content under the configured content directory.
5. Resolve the active product config when a product filter is provided.
6. Hydrate SDK/API reference validation sources when enabled.
7. Annotate local image and asset existence.
8. Group translations and detect missing localized versions.
9. Run technical Hugo SEO checks.
10. Run internal linking checks.
11. Run per-post content, audience, product-context, SDK/API, and on-page SEO checks.
12. Apply policy-grounded rules.
13. Run optional LLM suggestion enrichment only when explicitly enabled.
14. Score posts and return an `AuditResult`.
15. Write Markdown, CSV, JSON, run-log, and metrics artifacts.
16. Optionally send normalized metrics to the configured metrics API.

## State Model

The primary in-memory state is:

- `BlogConfig`: loaded configuration, repository source, audit options, policy paths, product configs, LLM options, SDK validation options.
- `Post`: parsed Markdown file state, front matter, body, headings, links, images, code samples, detected language, issues, scores, and optional LLM suggestions.
- `TranslationGroup`: grouped source and localized posts, available languages, missing languages, and group issues.
- `Issue`: normalized finding with severity, explanation, policy grounding, recommendation, effort, impact, and source location.
- `AuditResult`: final aggregate containing config, repository root, Hugo detection result, posts, groups, technical issues, internal-link issues, and LLM metrics.

Persistent state is limited to the configured output directory and work directory:

- audit reports under `outputs/audit/<blog>/` by default
- `audit-run.log`
- `audit-metrics.json`
- optional `draft-fixes/`
- optional cloned repositories under `outputs/_repos/`
- optional LLM cache files under the configured cache directory

## Side Effects

Default side effects:

- read repository files
- create output directories
- write audit reports, metrics, and logs
- clone remote repositories only when the config points to a remote source

Explicitly enabled side effects:

- LLM calls when `llm.enabled: true` or `--llm-suggestions true`
- metrics API delivery when `--send-metrics true`
- draft-fix scaffolds when `--mode report-with-draft-fixes` or `--generate-draft-fixes true`
- GitHub Actions report commits in the workflow after a successful manual run

The agent does not overwrite source Markdown posts. Draft fixes are written under the audit output directory for human review.

## External Boundaries

External network calls are bounded to:

- Git clone operations for configured repositories and API reference repositories.
- OpenAI-compatible chat completions endpoint for optional LLM suggestions.
- Metrics API endpoint for optional run telemetry.

No external call is required for the default local report mode when the configured repository and API references are already local or disabled.

## Extension Points

Supported extension points:

- Add or replace policy YAML files in `policies/`.
- Add product configs under `configs/<blog>/`.
- Add file-format aliases through `configs/file_formats.json`.
- Add new condition operators in `policy/evaluator.py` when a policy cannot be expressed with existing facts.
- Add new scanner fields in `scanner.py` and corresponding model fields in `models.py`.
- Add new report sections in `reports.py`.
- Add additional metrics fields in `cli.build_run_metrics` and `metrics_api.normalized_metrics_payload`.

New extension code should preserve the default safety contract: read-only source content, explicit opt-in for external calls, and report artifacts written under the configured output directory.
