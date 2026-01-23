# Content Gap Coverage Agent (cg-cover)

## 1) What it is

The **Content Gap Coverage Agent** computes **coverage maps** between content sources (e.g., Docs → Blogs, Docs → Tutorials, Blogs → Blogs) for a given **brand + product (+ optional baseline platform)**. It is intended to quantify “what content exists where,” and to surface **coverage gaps** that can be prioritized for new content creation or migration work. 

This agent runs as a CLI (`cg-cover`) and writes machine-readable outputs (JSON) plus human-readable reports (Markdown) to an outputs folder rooted at the brand’s configured `outputs_root` (or `outputs` by default). 

---

## 2) What it does (high-level workflow)

1. **Loads configuration**

   * Brand YAML (`--brand`) and Product YAML (`--product`). 
2. **Normalizes website metadata**

   * Uses the brand `website` to derive a normalized domain value used in reporting and metrics. 
3. **Runs a coverage case**

   * `blogs_to_blogs`
   * `docs_to_blogs`
   * `docs_to_tutorials` 
4. **Optionally uses semantic matching**

   * Uses similarity thresholds (`--threshold-strict`, `--threshold-loose`) and `--top-k` to decide what constitutes “covered.”
   * Can force a lexical-only fallback via `--no-embeddings`. 
5. **Writes coverage outputs**

   * Writes JSON/Markdown reports under the brand’s resolved outputs root. 

---

## 3) Inputs

### Brand YAML (`--brand`)

Required keys used by the CLI:

* `key` (brand key)
* `website` (used for normalized domain)
* `outputs_root` (optional; defaults to `outputs`) 

### Product YAML (`--product`)

Required keys used by the CLI:

* `key` (product key)
* `display_name` (product display name) 

---

## 4) How to run

### A) Basic run

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case blogs_to_blogs
```

`blogs_to_blogs` does **not** require `--platform`. 

### B) Docs-based cases (platform required)

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case docs_to_blogs \
  --platform net
```

For any case other than `blogs_to_blogs`, `--platform` is required. 

### C) Tune similarity + top matches

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case docs_to_tutorials \
  --platform net \
  --threshold-strict 0.86 \
  --threshold-loose 0.80 \
  --top-k 5
```

Thresholds and top-k are exposed as CLI flags. 

### D) Limit platforms (blogs_to_blogs only)

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case blogs_to_blogs \
  --platforms net,java
```

`--platforms` accepts a comma-separated platform list to constrain analysis (primarily useful for `blogs_to_blogs`). 

### E) Force lexical-only (no embeddings)

```bash
cg-cover run \
  --brand configs/aspose.yaml \
  --product configs/aspose/cells.yaml \
  --case blogs_to_blogs \
  --no-embeddings
```

This disables semantic matching and forces lexical fallback behavior. 

---

## 5) Outputs

The CLI resolves the outputs root as:

* `brand.outputs_root` if present
* otherwise defaults to `outputs`
* if relative, it is resolved relative to the brand yaml directory 

The agent then writes coverage artifacts under that resolved root (exact subfolders depend on the case and your internal agent implementation). 

---

## 6) Exit codes and error handling

* **2**: configuration/prerequisite errors (including missing `--platform` for non-blogs cases)
* **3**: not implemented
* **4**: unexpected failure 

---

If you want, I can also generate a **shorter “Quickstart-only” README** variant (10–15 lines) suitable for the repo root, while keeping this longer one under `docs/`.
