# LLM Boundaries

LLM suggestions are optional and disabled by default.

## Activation

LLM calls happen only when one of these is true:

- the config sets `llm.enabled: true`
- the CLI receives `--llm-suggestions true`
- the CLI mode implies suggestions and the config allows them

The provider is OpenAI-compatible. The endpoint and credentials come from config or environment variables such as `PROFESSIONALIZE_BASE_URL`, `PROFESSIONALIZE_API_KEY`, and `PROFESSIONALIZE_LLM_MODEL`.

## Data Sent

For each selected post, the request payload includes:

- blog name and audience profile
- whether developer-audience checks are enabled
- post file path
- title, description, language, word count, and headings
- selected audit issues with issue type, severity, explanation, recommendation, policy ID, and rule ID
- a bounded body excerpt controlled by `max_body_chars`
- a summary of configured policy rules
- the required JSON response schema

The payload does not intentionally include environment variables, API keys, Git credentials, or full repository state.

## Selection and Limits

Only posts with audit issues are eligible. Posts are sorted by priority score, then limited by `llm.max_posts` or `--llm-max-posts`.

The body excerpt is bounded by `max_body_chars`, defaulting to 6000 characters.

## Caching

LLM responses are cached by post content, policy summary, prompt version, model, provider, and relevant settings. Cache files are written under the configured LLM cache directory or the audit work directory.

Changing `PROMPT_VERSION` in `llm.py` intentionally invalidates the cache for prompt behavior changes.

## Human Review

LLM output is advisory. It can suggest titles, descriptions, outlines, FAQs, and action items, but it does not modify source posts. All suggestions require editorial and technical review before publication.
