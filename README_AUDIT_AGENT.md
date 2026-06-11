# Hugo Blog Audit Agent

Python CLI for local-only SEO, content quality, technical Hugo, internal linking, and multilingual audits of Hugo blog repositories.

By default, the agent reads repository files only. It does not crawl a deployed website, does not push to GitHub, does not make LLM calls, does not send metrics webhooks, and does not overwrite source posts. Optional draft fixes are written only under the audit output folder. When LLM suggestions are explicitly enabled, selected post excerpts, audit findings, and policy context are sent to the configured LLM provider.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

If editable install is not needed:

```bash
pip install -r requirements.txt
```

## Sample Config

See `configs/aspose.yaml`.

```yaml
key: aspose
display_name: Aspose
outputs_root: ../outputs
repositories:
  - repo_key: blog
    repo_type: blog
    repo_path: C:\GitHub\aspose-blog
    repo_url: https://github.com/Aspose/aspose-blog.git
    root_subdir: content/Aspose.Blog
audit:
  blog_name: Aspose
  content_dir: content
  output_dir: outputs
  developer_audience: true
  product_config_dir: aspose
  file_formats_path: file_formats.json
  audience_profile: "Developers and technical decision-makers evaluating or using Aspose APIs for document and file-format processing."
  known_product_mentions:
    - Aspose.Words
    - Aspose.PDF
    - Aspose.Imaging
    - Aspose.BarCode
  sdk_validation:
    enabled: true
    runtime_import_check: false
  llm:
    enabled: false
    provider: openai-compatible
    model: gpt-4o-mini
    max_posts: 10
    cache_dir: outputs/_llm_cache
  policy_files:
    - ../policies/content-quality.yaml
    - ../policies/audience-fit.yaml
    - ../policies/on-page-seo.yaml
    - ../policies/internal-linking.yaml
    - ../policies/multilingual-seo.yaml
    - ../policies/technical-hugo-seo.yaml
    - ../policies/blog-editorial-policy.yaml
```

The loader supports both this shared config schema and the older flat audit schema. Use `repo_path` for a local repository folder and `repo_url` for a GitHub or other Git URL. For remote URLs, the agent clones into `outputs/_repos` by default. Existing configs that put a local path in `repo_url` still work for backward compatibility.

For developer/API blogs, set `developer_audience: true`. This adds audience-fit checks for code examples, setup instructions, file-format context, troubleshooting notes, and API/reference links.

Use `known_product_mentions` to validate product/library names mentioned in prose, titles, descriptions, tags, categories, and keywords. Product config `display_name` values are also treated as verified names, and `known_product_mentions` can list additional verified names that do not have a local product config. Fenced code blocks are excluded from this editorial check because code imports and symbols are handled by SDK/API validation. Namespaces below a verified product are accepted, so `Aspose.BarCode.Generation` is valid when `Aspose.BarCode` is verified. For example, if prose says `Aspose.DICOM` but that name is not verified, the audit reports `unverified_product_mention` and recommends replacing it with a verified product/API name or accurate generic wording.

Use `product_config_dir` to load product-specific configs from `configs/aspose/`. When `--product` is passed, the agent infers the product key, loads the matching product config, and uses it for product-aware checks.

Product configs provide:

- `display_name`: verified product name, such as `Aspose.BarCode`.
- `formats`: expected product/file formats for product-specific context checks.
- `actions`: expected product tasks, such as generate, read, convert, export, edit.
- `money_pages`: product landing pages that posts should link to where relevant.
- `docs_pages`: documentation pages that posts should link to where relevant.
- `api_repo`, `api_branch`, and platform `api_path`: API reference sources for code/class validation.
- `platform_definitions`: platform keyword hints for .NET, Java, Python, C++, Node.js, PHP, Android, and other supported stacks.

Use `file_formats_path` to load `file_formats.json`; its aliases improve file-format context checks across all products.

Use `sdk_validation.enabled` to validate SDK imports, API symbols, explicit class/member mentions, and assignment-style property usage inside blog prose and fenced code blocks. For product-scoped audits, the agent builds API reference sources automatically from the selected product config. It clones or opens the relevant `api_repo`, indexes class/member/property names under the enabled platform `api_path` values, then reports `unresolved_api_module`, `unresolved_api_symbol`, `unresolved_api_class`, `unresolved_api_member`, and `deprecated_api_symbol`. Missing class/member findings include nearest existing indexed-symbol suggestions where available. Set `runtime_import_check: true` only when the target Python SDKs are installed in the current environment.

Policy files define audit rules, intended audiences, evidence, severity, and recommended fixes. The audit engine loads `policy_files` from the config and uses them to ground findings with policy ID, rule ID, evidence, and intended audience in issue tables and JSON output.

LLM suggestions are disabled by default. Set `llm.enabled: true` in config or pass `--llm-suggestions true` to generate optional review suggestions for the highest-priority posts. The built-in client loads `.env` from the current working directory, uses an OpenAI-compatible chat completions endpoint, reads `PROFESSIONALIZE_BASE_URL`, `PROFESSIONALIZE_API_KEY`, `PROFESSIONALIZE_LLM_MODEL`, and `PROFESSIONALIZE_EMBEDDING_MODEL` by default, and falls back to existing OpenAI-compatible environment names where supported. It caches responses by post content, policy context, model, and prompt version, and stores suggestions only in audit outputs.

Example `.env` values:

```text
PROFESSIONALIZE_BASE_URL=https://your-provider.example/v1
PROFESSIONALIZE_API_KEY=...
PROFESSIONALIZE_LLM_MODEL=your-chat-model
PROFESSIONALIZE_EMBEDDING_MODEL=your-embedding-model
PROFESSIONALIZE_TIMEOUT_SECONDS=120
PROFESSIONALIZE_LLM_RETRIES=1
```

## CLI Usage

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --mode report
```

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --product Aspose.blog/3d --mode report-with-fix-suggestions
```

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --product Aspose.blog/barcode --post-date 2026-06-05 --include-translations false --mode report
```

This pattern is useful for auditing only newly published source posts for one product:

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --product Aspose.blog/barcode --post-date 2026-06-05 --include-translations false --mode report --verbose
```

```bash
python -m hugo_blog_audit_agent --blog-config configs/aspose.yaml --mode report-with-draft-fixes --max-draft-fixes 5 --priority-only true
```

Useful flags:

- `--blog-config`: required YAML/JSON blog config path.
- `--product`: optional product/path filter.
- `--post-date` / `--date`: optional `YYYY-MM-DD` post date filter. Combine with `--product` to audit only posts from a selected product and date.
- `--mode`: `report`, `report-with-fix-suggestions`, or `report-with-draft-fixes`.
- `--generate-draft-fixes`: boolean override to generate drafts.
- `--max-draft-fixes`: limit generated drafts.
- `--priority-only`: generate drafts only for high-priority posts.
- `--languages`: comma-separated language filter.
- `--include-translations`: include translated Markdown files; use `--include-translations false` to scan source `index.md` files only.
- `--detailed-outputs`: generate the full detailed report set in addition to `audit-action-items.md`; defaults to `false`.
- `--llm-suggestions`: enable optional LLM-generated review suggestions; sends selected post excerpts and audit findings to the configured provider.
- `--llm-model`: override the configured LLM model.
- `--llm-base-url`: override the configured OpenAI-compatible `/v1` base URL or full chat completions URL.
- `--llm-max-posts`: limit how many highest-priority posts receive LLM suggestions.
- `--llm-timeout-seconds`: LLM HTTP read timeout; defaults to `120` seconds and can also be set with `PROFESSIONALIZE_TIMEOUT_SECONDS`.
- `--llm-retries`: retry count for timeout or connection-style LLM failures; defaults to `1` and can also be set with `PROFESSIONALIZE_LLM_RETRIES`.
- `--send-metrics`: send normalized run metrics to configured metrics webhooks; defaults to `false`.
- `--verbose`: print run details.
- `--quiet`: suppress progress logs and final metrics in the console.
- `--keep-workdir`: keep cloned repository workspace.

When SDK validation is enabled and a matching product config has an `api_repo`, the agent may clone API reference repositories under the work directory, by default `outputs/_repos/_api_references/`.

## Reports

Outputs go to a blog-specific folder under `outputs/audit/` by default. For the Aspose sample, outputs are written to `outputs/audit/aspose/`.

Default output:

- `audit-action-items.md`: consolidated actionable backlog across audit findings, with priority, severity, area, recommended fix, effort, impact, and source report for each item.
- `audit-run.log`: timestamped phase-by-phase audit log.
- `audit-metrics.json`: run metrics such as duration, files scanned, issue totals, severity counts, code block counts, code/API issue counts, high-priority post counts, LLM usage/cache/error counts, whether detailed outputs were enabled, and whether metrics webhook delivery was attempted.

Metrics webhook delivery is disabled unless `--send-metrics true` is passed. When enabled, configure `METRICS_WEBHOOK_URL_PROD`, `TOKEN_FOR_PROD`, `METRICS_WEBHOOK_URL_TEAM`, and `TOKEN_FOR_TEAM` in `.env` or the process environment.

When `--llm-suggestions true` or `llm.enabled: true` is used, `audit-action-items.md` includes an `LLM Suggestions` section with suggested titles, descriptions, outlines, FAQ questions, concrete content actions, and review notes. These suggestions are advisory only and do not modify source posts.

When `--detailed-outputs true` is passed, the CLI also writes:

- `audit-summary.md`: executive summary and segment-level dashboard across complete SEO, content, audience fit, code/API audit, on-page SEO, technical SEO, internal linking, multilingual SEO, quick wins, and inventory.
- `complete-seo-audit.md`: consolidated SEO audit with scorecard, per-post SEO segment score table, issue summaries, content, technical, linking, multilingual, product-context, audience-fit, inventory, and roadmap sections.
- `code-audit.md`: code-block and SDK/API validation report, including API reference sources, per-post code coverage, unresolved imports/classes/properties, deprecated symbols, and nearest-symbol suggestions for missing classes or members.
- `post-audit.csv`: one row per post with scores, issue counts, and recommended action.
- `post-audit.json`: full structured audit data.
- `technical-seo-audit.md`: Hugo config/template/static-file SEO findings.
- `internal-linking-audit.md`: broken links, orphan posts, weak anchors, linking opportunities.
- `content-improvement-plan.md`: prioritized title, description, heading, FAQ, schema, linking, and expansion recommendations.
- `quick-wins.md`: low-effort fixes with expected impact.

The CLI also prints progress logs while it runs and shows a final metrics summary at the end. Use `--quiet` when you only want the output files.

## Policy Files

Policy files live under `policies/` and are listed per blog config. They define segment rules, intended audiences, severity, evidence, recommendations, effort, and expected SEO impact.

Current policy files:

- `content-quality.yaml`
- `audience-fit.yaml`
- `on-page-seo.yaml`
- `internal-linking.yaml`
- `multilingual-seo.yaml`
- `technical-hugo-seo.yaml`
- `blog-editorial-policy.yaml`

To customize another blog, add or replace entries in `policy_files` in that blog's config. Code changes are only needed if a new policy requires a new condition operator.

## Improvement Planning

The repository includes `implementation-plan.md`, which describes the workflow for applying audit findings to real blog posts. It covers batching, source-post updates, metadata improvements, internal linking, image handling, translation workflow, QA, and a planned manual GA4/Search Console CSV integration.

The manual CSV plan expects exports such as:

```text
inputs/gsc-pages-last-90-days.csv
inputs/gsc-queries-pages-last-90-days.csv
inputs/ga4-landing-pages-last-90-days.csv
```

Those files are not required for the current audit run; they are planned inputs for performance-aware prioritization.

## Draft Fixes

Draft generation is disabled by default.

It is enabled only when:

- `--mode report-with-draft-fixes`
- or `--generate-draft-fixes true`

Drafts are written to the audit folder's `draft-fixes/` directory, for example `outputs/audit/aspose/draft-fixes/`. The original Markdown files are not overwritten. `draft-fixes/index.csv` maps source files to generated draft files and notes.

## Tests

```bash
python -m pytest
```

## Known Limitations

- The audit uses local heuristics and does not verify rendered HTML from a live site.
- Code/API validation is static. It validates imports and symbols against indexed API reference docs, but it does not execute snippets or compile projects.
- If an API reference repository is unavailable or cannot be cloned in the current environment, the audit logs the skip and continues.
- YAML/TOML parsing is best with `PyYAML` and Python 3.11+ `tomllib`; fallback parsing is intentionally minimal.
- Translation quality checks detect obvious metadata and structure issues, not full linguistic quality.
- Draft fixes are conservative scaffolds for manual review, not publish-ready rewrites.

## Future Improvements

- Add richer rendered-template analysis using a local Hugo build.
- Add deeper method-level API validation from API reference metadata where available.
- Add near-duplicate detection with `rapidfuzz`.
- Add topic clustering and link opportunity ranking with embeddings or NLP.
- Implement the planned manual GA4/Search Console CSV import from `implementation-plan.md`.
