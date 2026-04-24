# Content Gap Coverage Agent (`cg-cover`)

## 1. Purpose

`cg-cover` computes coverage maps between indexed content sources for a selected brand and product. It is designed to answer questions such as:

- Which Docs topics have matching Blog posts?
- Which Docs topics have matching Tutorials?
- Which Blog topics exist for one platform but not another?

The agent consumes JSONL indexes produced by `cg-index` and writes machine-readable and human-readable reports.

## 2. Supported Cases

- `blogs_to_blogs`
- `docs_to_blogs`
- `docs_to_tutorials`

`blogs_to_blogs` does not require `--platform`. Docs-based cases require `--platform` because that platform provides the baseline docs index.

## 3. Matching Behavior

Current matching is deterministic and offline.

### Blogs -> Blogs

`blogs_to_blogs` uses normalized key equality:

- Baseline topics are grouped by `IndexRecord.key`.
- Candidate blog records are matched by the same normalized key.
- Release/update posts and posts before `2020-01-01` or without parseable dates are excluded.

### Docs -> Blogs and Docs -> Tutorials

Docs-based cases use lexical candidate ranking:

- Candidates are ranked by normalized lexical similarity.
- Exact normalized topic match scores `1.0`.
- Substring containment scores `0.9`.
- Other candidates score `0.0`.

The following CLI options are active for docs-based matching:

- `--threshold-strict`
- `--threshold-loose`
- `--top-k`
- `--no-embeddings`

A candidate is considered covered when the best candidate within `top-k` reaches `threshold-loose`. Matches at or above `threshold-strict` are marked as strict; matches between loose and strict are marked as loose.

`--no-embeddings` keeps matching lexical-only. The current coverage engine does not require embedding/vector lookup.

## 4. Inputs

### Brand YAML

Required keys:

- `key`
- `website`

Optional:

- `outputs_root`

### Product YAML

Required keys:

- `key`
- `display_name`

## 5. Commands

Blogs -> Blogs:

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case blogs_to_blogs
```

Docs -> Blogs:

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case docs_to_blogs \
  --platform net
```

Docs -> Tutorials:

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case docs_to_tutorials \
  --platform net
```

Tune matching:

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case docs_to_blogs \
  --platform net \
  --threshold-strict 0.95 \
  --threshold-loose 0.80 \
  --top-k 5
```

Limit target platforms:

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case blogs_to_blogs \
  --platforms net,java
```

## 6. Outputs

Coverage artifacts are written under:

```text
outputs/<brand>/<product>/coverage/<case>/<baseline>/
```

Typical files:

- `coverage.json`
- `coverage.md`
- `gaps.md`
- `<brand>-<product>_<baseline>_missing_topics.md`

`coverage.json` includes:

- `case`
- `brand_key`
- `product_key`
- `baseline_platform`
- `platforms`
- `meta`
- `rows`

The `meta` object contains structured runtime data such as:

- `matching_mode`
- `threshold_strict`
- `threshold_loose`
- `top_k`
- `total_cells`
- `matched_cells`
- `missing_cells`
- `match_rate`
- release/update exclusion counts
- baseline/candidate counts

## 7. Metrics And Sheets Safety

Metrics are enabled by default and optional by default. Agent metadata, stages, and webhook URLs are loaded from `configs/metrics.json`. Metrics tokens remain in `.env`.

If `METRICS_REQUIRED=true`, missing webhooks or non-2xx responses fail the run.

Google Sheets posting is skipped when:

```env
CG_SKIP_SHEETS_AUTO_POST=true
```

The evaluation harness sets this automatically.

## 8. Local Missing Topics Workflow

Run the local workflow for `Aspose.Cells`:

```bash
python scripts/run_missing_topics_workflow_local.py \
  --brand-yaml configs/aspose.yaml \
  --product-yaml configs/aspose/cells.yaml \
  --index-platform net \
  --case blogs_to_blogs \
  --steps blog \
  --append
```

Use `--post` only when you want to send the generated payload to the configured Google Sheet.

## 9. Evaluation

Run the offline evaluator:

```bash
python scripts/evaluate_coverage.py --fixtures tests/fixtures/evaluation
```

JSON output:

```bash
python scripts/evaluate_coverage.py --fixtures tests/fixtures/evaluation --json
```

The evaluator runs against golden fixtures and reports precision, recall, F1, true positives, false positives, true negatives, false negatives, exact/key matches, and lexical matches.

## 10. Exit Codes

- `0`: success
- `2`: configuration or prerequisite error
- `3`: not implemented
- `4`: unexpected failure
