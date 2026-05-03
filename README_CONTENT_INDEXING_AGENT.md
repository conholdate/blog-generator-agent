# Content Indexing Agent (`cg-index`)

## 1. Purpose

`cg-index` is a CLI-driven indexing pipeline. It clones configured content repositories for a selected brand, product, and platform, then writes incremental JSONL indexes used by `cg-cover`.

It is intended for:

- local development
- repeatable CI runs
- downstream coverage and gap analysis

## 2. Outputs

Indexes are written under:

```text
outputs/<brand>/<product>/
  indexes/<repo_key>/
    all.jsonl
    <platform>.jsonl
  state/
    <repo_key>_state.json
    <repo_key>__<platform>.json
  cache/
    embeddings.sqlite
```

Repository clones are stored under:

```text
outputs/_repos/<brand>__<product>__<repo_key>/
```

## 3. Incremental Behavior

On each run, the indexer:

1. Loads brand and product YAML configuration.
2. Clones or updates configured repositories.
3. Discovers eligible Markdown files.
4. Computes SHA-256 fingerprints.
5. Reprocesses only new or changed files.
6. Reuses cached embeddings for identical text.
7. Optionally deletes index records for removed files with `--delete-missing`.
8. Writes JSONL index and state files.

## 4. Configuration

Preferred API key:

```env
PROFESSIONALIZE_API_KEY=
```

Backward-compatible key:

```env
PROFESSIONALIZE_API_KEY_1=
```

Fallback:

```env
OPENAI_API_KEY=
```

Optional provider/model settings:

```env
PROFESSIONALIZE_BASE_URL=https://llm.professionalize.com/v1
PROFESSIONALIZE_LLM_MODEL=gpt-oss
PROFESSIONALIZE_EMBEDDING_MODEL=qwen3-embedding-8b
OPENAI_BASE_URL=
```

Metrics are enabled by default and optional by default. Agent metadata, stages, and webhook URLs are loaded from `configs/metrics.json`, while metrics tokens remain in `.env`.

If `METRICS_REQUIRED=true`, metrics send failures fail the run.

## 5. Install

```bash
python -m pip install --upgrade pip
pip install -e .
```

For tests and evaluation:

```bash
pip install -e ".[dev]"
```

## 6. Commands

Deterministic run:

```bash
cg-index run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --platform net \
  --steps blog,docs,tutorials,api
```

Run only blogs:

```bash
cg-index run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --platform net \
  --steps blog
```

Delete missing content from the index:

```bash
cg-index run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --platform net \
  --steps blog,docs \
  --delete-missing
```

Interactive product selection:

```bash
cg-index run \
  --brand configs/aspose.yaml \
  --products-dir configs/aspose \
  --platform net
```

## 7. Validation

Run the test suite:

```bash
python -m pytest tests
```

Run coverage matching evaluation:

```bash
python scripts/evaluate_coverage.py --fixtures tests/fixtures/evaluation
```

The evaluator is offline and disables metrics and Sheets posting.
