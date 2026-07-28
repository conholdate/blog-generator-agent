from __future__ import annotations

from pydantic import BaseModel, Field


class CodeVerificationResult(BaseModel):
    """Result of verifying a code sample (instructions.md step 5).

    These samples come from Aspose's own product team, published verbatim in
    the release notes — they aren't LLM-generated, so "is this a real API"
    isn't the risk. The real risk is transcription drift: the extractor LLM
    re-typing the sample while selecting/JSON-encoding it and silently
    changing something. `source_verified` checks that deterministically by
    comparing against the code blocks fetcher.py scraped straight out of the
    source page's <pre> tags. `syntax_valid` is a lightweight bracket/quote
    balance check — not a full parse, since these are illustrative fragments
    (they reference helper methods and input files that only exist in the
    product team's own test environment), not standalone compilable programs.

    `tested` (real sandbox execution) stays False by design: these samples
    depend on proprietary licensed Aspose assemblies, external input files,
    and sometimes network services (e.g. a timestamp authority URL) that
    aren't available to this pipeline, so claiming "tested" would be
    dishonest. See code_verifier.py.
    """

    language: str
    tested: bool = False
    source_verified: bool = False
    syntax_valid: bool = False
    package_name: str | None = None
    package_version: str | None = None
    os: str | None = None
    input_file_used: str | None = None
    output_file_generated: str | None = None
    errors: list[str] = Field(default_factory=list)
    notes: str = ""
