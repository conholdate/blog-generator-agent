from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

# ----------------------------
# Result model
# ----------------------------

@dataclass(frozen=True)
class KeyDecision:
    key: Optional[str]
    confidence: float
    method: str          # "heuristic" | "llm" | "none"
    rationale: str


# ----------------------------
# Heuristic (fast) key maker
# ----------------------------

_FORMAT_SYNONYMS: Dict[str, str] = {
    "DAE": "COLLADA",
    "COLLADA": "COLLADA",
    "OBJ": "OBJ",
    "STL": "STL",
    "FBX": "FBX",
    "GLTF": "GLTF",
    "GLB": "GLB",
    "3DS": "3DS",
    "PLY": "PLY",
    "USD": "USD",
    "USDA": "USD",
    "USDC": "USD",
    "STEP": "STEP",
    "STP": "STEP",
    "IGES": "IGES",
    "IGS": "IGES",
    "AMF": "AMF",
    "U3D": "U3D",
    "DXF": "DXF",
    "DWG": "DWG",
    "VRML": "VRML",
    "WRL": "VRML",
    "JT": "JT",
    "IFC": "IFC",
}

_NOT_FORMAT_TOKENS = {
    "A", "AN", "AND", "OR", "THE",
    "API", "SDK",
    "CREATE", "READ", "SAVE", "GET", "TRY", "FREE",
    "GUIDE", "TUTORIAL", "ONLINE",
    "JAVA", "PYTHON", "C", "CPP", "CXX", "CSHARP", "DOTNET", "NET",
    "SCENE", "MODEL", "MESH", "VIEWPORT", "EFFECTS",
    "IMPORT", "EXPORT", "CONVERT", "RENDER", "SPLIT", "MERGE",
    "WITH", "USING", "FROM", "TO", "IN", "ON", "BY", "OF", "AS", "AT",
}

_INTENT_MAP: List[Tuple[str, str]] = [
    (r"\bconvert\b|\bconversion\b|\btransform\b", "CONVERT"),
    (r"\bimport\b|\bload\b|\bopen\b|\bread\b", "IMPORT"),
    (r"\bexport\b|\bsave\b|\bwrite\b|\bgenerate\b", "EXPORT"),
    (r"\brender\b|\bdraw\b", "RENDER"),
    (r"\bcreate\b|\bbuild\b|\bconstruct\b", "CREATE"),
    (r"\bsplit\b|\bseparate\b", "SPLIT"),
    (r"\bmerge\b|\bcombine\b|\bjoin\b", "MERGE"),
]

_PAIR_PATTERNS = [
    # whitespace-delimited only (prevents AND-to-RUS from "and Torus")
    re.compile(r"\b(?P<src>[A-Za-z0-9]{1,12})\b\s+(?:to|2)\s+\b(?P<dst>[A-Za-z0-9]{1,12})\b", re.I),
    re.compile(r"\b(?P<src>[A-Za-z0-9]{1,12})\b\s*(?:→|->|➜|⇒|⟶)\s*\b(?P<dst>[A-Za-z0-9]{1,12})\b", re.I),
    re.compile(r"\bfrom\s+(?P<src>[A-Za-z0-9]{1,12})\b\s+to\s+\b(?P<dst>[A-Za-z0-9]{1,12})\b", re.I),
    re.compile(r"\bconvert\s+(?P<src>[A-Za-z0-9]{1,12})\b\s+(?:file\s+)?to\s+\b(?P<dst>[A-Za-z0-9]{1,12})\b", re.I),
]

_IMPORT_FROM = re.compile(r"\bimport\b.*\bfrom\s+(?P<src>[A-Za-z0-9]{1,12})\b", re.I)
_SAVE_TO = re.compile(r"\b(?:save|export|write)\b.*\bto\s+(?P<dst>[A-Za-z0-9]{1,12})\b", re.I)
_EXT = re.compile(r"\.([A-Za-z0-9]{1,6})\b")


def _canon_format(raw: str) -> Optional[str]:
    tok = (raw or "").strip().strip(".").upper()
    tok = re.sub(r"[^A-Z0-9]+", "", tok)
    if not tok:
        return None
    if tok in _NOT_FORMAT_TOKENS:
        return None
    if not (2 <= len(tok) <= 6):
        return None
    if not re.search(r"[A-Z]", tok):
        return None
    return _FORMAT_SYNONYMS.get(tok, tok)


def _detect_intent(text: str) -> str:
    lt = (text or "").lower()
    for pat, norm in _INTENT_MAP:
        if re.search(pat, lt, flags=re.I):
            return norm
    return "GENERAL"


def _extract_formats(text: str) -> List[str]:
    found: List[str] = []

    for m in _EXT.finditer(text):
        fmt = _canon_format(m.group(1))
        if fmt:
            found.append(fmt)

    tokens = re.findall(r"\b[A-Za-z0-9]{2,6}\b", text)
    for tok in tokens:
        fmt = _canon_format(tok)
        if fmt and fmt in set(_FORMAT_SYNONYMS.values()):
            found.append(fmt)

    freq: Dict[str, int] = {}
    for f in found:
        freq[f] = freq.get(f, 0) + 1
    return sorted(freq.keys(), key=lambda x: (-freq[x], x))


def _extract_pair(text: str) -> Optional[Tuple[str, str]]:
    canon_vals = set(_FORMAT_SYNONYMS.values())
    for pat in _PAIR_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        src = _canon_format(m.group("src"))
        dst = _canon_format(m.group("dst"))
        if not src or not dst or src == dst:
            continue
        # Require at least one side be a known format (reduces API-to-CREATE)
        if (src not in canon_vals) and (dst not in canon_vals):
            continue
        return src, dst
    return None


def heuristic_key(record: Dict[str, Any]) -> KeyDecision:
    parts: List[str] = []
    for k in ("title", "topic", "excerpt"):
        v = record.get(k)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    kws = record.get("keywords") or []
    if isinstance(kws, list):
        parts.extend([str(x) for x in kws if str(x).strip()])
    text = "\n".join(parts)

    intent = _detect_intent(text)
    fmts = _extract_formats(text)
    pair = _extract_pair(text)

    if pair:
        src, dst = pair
        return KeyDecision(
            key=f"{src}-to-{dst}",
            confidence=0.95,
            method="heuristic",
            rationale=f"Detected explicit conversion pair {src} to {dst}.",
        )

    if intent == "IMPORT":
        m = _IMPORT_FROM.search(text)
        if m:
            src = _canon_format(m.group("src"))
            if src:
                return KeyDecision(
                    key=f"IMPORT-SCENE-FROM-{src}",
                    confidence=0.85,
                    method="heuristic",
                    rationale=f"Detected import intent with source format {src}.",
                )
        if fmts:
            return KeyDecision(
                key=f"IMPORT-SCENE-FROM-{fmts[0]}",
                confidence=0.70,
                method="heuristic",
                rationale=f"Detected import intent with dominant format {fmts[0]}.",
            )

    if intent in {"EXPORT", "RENDER"}:
        m = _SAVE_TO.search(text)
        if m:
            dst = _canon_format(m.group("dst"))
            if dst:
                return KeyDecision(
                    key=f"{intent}-SCENE-TO-{dst}",
                    confidence=0.80,
                    method="heuristic",
                    rationale=f"Detected {intent.lower()} intent with target format {dst}.",
                )
        if fmts:
            return KeyDecision(
                key=f"{intent}-SCENE-TO-{fmts[0]}",
                confidence=0.60,
                method="heuristic",
                rationale=f"Detected {intent.lower()} intent with dominant format {fmts[0]}.",
            )

    return KeyDecision(key=None, confidence=0.0, method="none", rationale="No reliable heuristic key.")


# ----------------------------
# LLM fallback (validated)
# ----------------------------

_KEY_ALLOWED = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+){1,8}$")  # 2..9 segments


def _validate_key(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    k = key.strip().upper()
    if not _KEY_ALLOWED.fullmatch(k):
        return None
    # avoid junk keys like API-to-CREATE patterns (common failure)
    bad = {"API", "SDK", "CREATE", "READ", "SAVE", "GET", "TRY", "FREE", "GUIDE", "TUTORIAL"}
    segs = k.split("-")
    if any(s in bad for s in segs):
        return None
    return k


def llm_key(client: OpenAI, record: Dict[str, Any], *, model: str) -> KeyDecision:
    """
    LLM generates a key when heuristics cannot.
    Output MUST be a JSON object: {"key": "...", "confidence": 0..1, "rationale": "..."}.
    We validate the key and drop it if it doesn't conform.
    """
    payload = {
        "id": record.get("id"),
        "product": record.get("product"),
        "platform": record.get("platform"),
        "title": record.get("title"),
        "topic": record.get("topic"),
        "category": record.get("category"),
        "sub_category": record.get("sub_category"),
        "keywords": record.get("keywords", [])[:30],
        "excerpt": (record.get("excerpt") or "")[:2000],
        "url": record.get("url"),
    }

    system = (
        "You are an indexing key generator.\n"
        "Create a SHORT, STABLE, CLUSTERING key.\n"
        "Rules:\n"
        "- Output JSON only.\n"
        "- key must be uppercase with '-' separators.\n"
        "- Prefer conversion: OBJ-to-STL.\n"
        "- Prefer intent keys: IMPORT-SCENE-FROM-COLLADA, EXPORT-SCENE-TO-FBX.\n"
        "- Do NOT use generic words like API, SDK, GUIDE, TUTORIAL, FREE.\n"
        "- Keep 2 to 6 segments.\n"
    )

    user = f"Record:\n{json.dumps(payload, ensure_ascii=False)}\nReturn JSON: {{\"key\":\"...\",\"confidence\":0.0,\"rationale\":\"...\"}}"

    # Using Responses API style (works with modern OpenAI python). If your client uses chat.completions,
    # swap accordingly.
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_output_tokens=200,
    )

    text = (resp.output_text or "").strip()
    try:
        data = json.loads(text)
    except Exception:
        return KeyDecision(key=None, confidence=0.0, method="llm", rationale="LLM returned non-JSON.")

    key = _validate_key(str(data.get("key") or ""))
    if not key:
        return KeyDecision(key=None, confidence=0.0, method="llm", rationale="LLM key failed validation.")

    conf = float(data.get("confidence") or 0.55)
    conf = max(0.0, min(1.0, conf))
    rationale = str(data.get("rationale") or "LLM-generated key.")
    return KeyDecision(key=key, confidence=conf, method="llm", rationale=rationale)


def make_key(
    client: OpenAI,
    record: Dict[str, Any],
    *,
    llm_model: str,
    enable_llm: bool = True,
    llm_min_confidence: float = 0.55,
) -> KeyDecision:
    """
    Main entrypoint:
    - heuristic first
    - LLM fallback if enabled and heuristic failed
    - always validated
    """
    h = heuristic_key(record)
    if h.key:
        return h

    if not enable_llm:
        return h

    l = llm_key(client, record, model=llm_model)
    if l.key and l.confidence >= llm_min_confidence:
        return l

    return KeyDecision(key=None, confidence=0.0, method="none", rationale="No valid key.")