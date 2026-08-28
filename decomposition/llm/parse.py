from __future__ import annotations

import json
import re

from pydantic import ValidationError

from decomposition.llm.schema import DecompositionProposal

FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json_object(text: str) -> str:
    fenced = FENCE.search(text)
    blob = fenced.group(1) if fenced else text
    start = blob.find("{")
    end = blob.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object found in model output")
    return blob[start : end + 1]


def parse_proposal(text: str) -> DecompositionProposal:
    payload = json.loads(extract_json_object(text))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return DecompositionProposal.model_validate(payload)


def format_validation_error(error: Exception) -> str:
    if isinstance(error, ValidationError):
        return _redact_secrets(error.errors().__repr__())
    return _redact_secrets(str(error))


def _redact_secrets(text: str) -> str:
    text = re.sub(r"([?&]key=)[^&\s\"']+", r"\1REDACTED", text, flags=re.IGNORECASE)
    text = re.sub(
        r"(Authorization:\s*Bearer\s+)\S+",
        r"\1REDACTED",
        text,
        flags=re.IGNORECASE,
    )
    return text
