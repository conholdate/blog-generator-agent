# Release Process

## Release Readiness Checklist

Before tagging a release:

- update `CHANGELOG.md`
- run `python -m compileall agent_engine`
- run `python -m pytest`
- run `python -m ruff check agent_engine tests`
- run `python -m pytest --cov=hugo_blog_audit_agent --cov-report=term-missing --cov-report=xml`
- run `python -m pip_audit -r requirements.txt`
- build the runtime image with `docker build -t hugo-blog-audit-agent .`
- run the sample CLI command against a small known Hugo fixture or approved blog repository
- update `docs/beta-evidence-log.md` with retained artifact locations
- confirm `audit-action-items.md`, `audit-run.log`, and `audit-metrics.json` are generated
- confirm optional external calls are disabled by default
- review changes to policy files and product configs

## Versioning

The package version is defined in `pyproject.toml`.

Use semantic versioning:

- patch: bug fixes and documentation updates
- minor: new checks, reports, config fields, or compatible CLI flags
- major: incompatible config, output schema, or CLI changes

## Release Notes

Release notes should include:

- new audit capabilities
- changed defaults
- security or data-handling changes
- migration notes for config or CLI changes
- known limitations

## Rollback

To roll back a bad release:

- revert the release commit or tag
- disable any affected workflow dispatch runs
- restore the previous package version
- document the issue and corrective action in `CHANGELOG.md`
