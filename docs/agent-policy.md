# Agent Policy

This policy describes what the Hugo Blog Audit Agent is allowed to do during a run.

## Default Mode

By default the agent may:

- read configured blog repository files
- read configured policy and product config files
- parse Markdown, Hugo config, templates, links, images, shortcodes, and code fences
- write audit reports, run logs, metrics JSON, and optional working files under configured output/work directories

By default the agent must not:

- overwrite source Markdown posts
- push changes to the source blog repository
- crawl a deployed website
- call an LLM provider
- send metrics to the metrics API
- publish content

## Explicit Opt-ins

The following behaviors require explicit configuration or CLI flags:

- LLM suggestions: `llm.enabled: true` or `--llm-suggestions true`
- metrics delivery: `--send-metrics true`
- draft-fix scaffolds: `--mode report-with-draft-fixes` or `--generate-draft-fixes true`
- retaining cloned work directories: `--keep-workdir`
- runtime SDK import checks: `runtime_import_check: true`

## Data Handling

Source content remains in the local repository unless an explicit opt-in sends derived data externally.

LLM suggestions send selected post excerpts, audit findings, policy context, and metadata to the configured provider. Metrics API delivery sends normalized run metrics and does not include source post bodies or API keys in the JSON payload.

## Output Safety

Generated draft fixes are review artifacts. They are not treated as publish-ready content and are not written over source files.

Secrets should be provided through environment variables or GitHub Secrets. Real credentials must not be committed to this repository.
