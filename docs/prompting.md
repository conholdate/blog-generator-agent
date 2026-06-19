# Prompting

The current LLM prompt is implemented in `hugo_blog_audit_agent.llm.build_payload`.

## Prompt Contract

The prompt asks the model to behave as a technical SEO and developer-content reviewer. It requires JSON output and explicitly forbids inventing product capabilities, API names, links, or code behavior.

The required response fields are:

- `summary`
- `suggested_title`
- `suggested_description`
- `outline`
- `faq_questions`
- `content_actions`
- `risk_notes`
- `issues_addressed`

## Versioning

Prompt cache behavior is controlled by `PROMPT_VERSION` in `llm.py`. Change this value when the payload shape, model instructions, policy summary, or output contract changes in a way that should invalidate old cached responses.

## Regression Expectations

Prompt changes should include tests for:

- valid JSON response parsing
- cache-key changes when relevant prompt inputs change
- missing API key behavior
- mock provider behavior
- advisory suggestions remaining report-only

## Review Rules

Generated suggestions must not be treated as factual without review. The agent should prefer grounded policy issues, existing post content, and configured product data over model-generated assumptions.
