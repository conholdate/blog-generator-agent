# Content Indexing Agent (Incremental Indexer)

## 1) What it is

The **Content Indexing Agent** is a CLI-driven indexing pipeline that **clones content repositories** for a selected **brand → product → platform** and produces **incremental JSONL indexes** that can be reused by downstream coverage / gap-analysis agents. 

It is designed for:

* **Local development** (fast reruns while iterating)
* **CI/CD (GitHub Actions)** (incremental updates instead of re-indexing everything) 

---

## 2) What it produces

All outputs are written under:

```
outputs/<brand>/<product>/
  indexes/<repo_key>/
    all.jsonl            # for scope=all repos (e.g., blogs)
    <platform>.jsonl     # for scope=platform repos (e.g., docs/api/tutorials)
  state/
    <repo_key>_state.json
    <repo_key>__<platform>.json
  cache/
    embeddings.sqlite    # embedding cache (text hash -> embedding vector)
```

Repositories are cloned under:

```
outputs/_repos/<brand>**<product>**<repo_key>/
```



---

## 3) How it works (incremental indexing)

On every run, the agent:

1. **Discovers eligible files** (based on configured include globs / repo rules).
2. **Fingerprints each file** (SHA-256).
3. Reprocesses **only new or changed files** (incremental).
4. Reuses an **embedding cache** to avoid re-embedding identical text.
5. Optionally deletes index records for removed files using `--delete-missing`. 

This makes reruns efficient, especially in CI where content updates are typically small between runs. 

---

## 4) Requirements

* Python **3.11+**
* Git installed (repo cloning)
* API credentials (see Environment Variables below) 

---

## 5) Install

From repo root:

```bash
python -m pip install --upgrade pip
pip install -e .
```

This registers the CLI:

```bash
cg-index --help
```

---

## 6) Environment variables

Preferred:

* `PROFESSIONALIZE_API_KEY`
* `PROFESSIONALIZE_BASE_URL` (optional)
* `PROFESSIONALIZE_LLM_MODEL` (optional; default in project)
* `PROFESSIONALIZE_EMBEDDING_MODEL` (optional; default in project)

Local fallback:

* `OPENAI_API_KEY`
* `OPENAI_BASE_URL` (optional)

Output directory override:

* `CG_OUTPUTS_DIR` (optional; default: `outputs/`) 

The CLI also loads a local `.env` automatically. 

---

## 7) How to run

### A) Deterministic (recommended for CI)

```bash
cg-index run \
  --brand path/to/blogs.yaml \
  --product path/to/cells.yaml \
  --platform net \
  --steps blog,docs,tutorials,api
```

* `--steps` is a CSV list of repo keys (defaults to `blog,docs,tutorials,api`).

### B) Run a single step (example: only blogs)

```bash
cg-index run \
  --brand path/to/aspose.yaml \
  --product path/to/cells.yaml \
  --platform net \
  --steps blog
```

### C) Delete missing content from the index

```bash
cg-index run \
  --brand path/to/aspose.yaml \
  --product path/to/cells.yaml \
  --platform net \
  --steps blog,docs \
  --delete-missing
```

### D) Interactive selection (local dev convenience)

If you have a directory of product YAMLs:

```bash
cg-index run \
  --brand path/to/aspose.yaml \
  --products-dir path/to/products \
  --platform net
```
---

## 8) What to do next

This indexer is intended to feed **coverage and gap analysis agents**, which consume the generated JSONL indexes under `outputs/<brand>/<product>/indexes/...`. 
