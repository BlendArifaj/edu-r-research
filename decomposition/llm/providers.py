from __future__ import annotations

import os
from typing import Protocol

import httpx


class LLMProvider(Protocol):
    name: str

    def generate(self, prompt: str, *, model: str, temperature: float) -> str: ...


class MissingCredentialsError(RuntimeError):
    """Raised when a provider is requested without credentials. Do not fabricate output."""


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None, timeout: float = 120.0) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout

    def generate(self, prompt: str, *, model: str, temperature: float) -> str:
        if not self.api_key:
            raise MissingCredentialsError("OPENAI_API_KEY is not set")
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"])


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None, timeout: float = 120.0) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.timeout = timeout

    def generate(self, prompt: str, *, model: str, temperature: float) -> str:
        if not self.api_key:
            raise MissingCredentialsError("ANTHROPIC_API_KEY is not set")
        payload = {
            "model": model,
            "max_tokens": 8000,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        blocks = response.json().get("content") or []
        return "".join(str(block.get("text") or "") for block in blocks)


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, timeout: float = 120.0) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.timeout = timeout

    def generate(self, prompt: str, *, model: str, temperature: float) -> str:
        if not self.api_key:
            raise MissingCredentialsError("GEMINI_API_KEY is not set")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }
        response = httpx.post(
            url,
            headers={"x-goog-api-key": self.api_key},
            json=payload,
            timeout=self.timeout,
        )
        if response.is_error:
            from decomposition.llm.parse import format_validation_error

            detail = format_validation_error(
                RuntimeError(f"Gemini HTTP {response.status_code}: {response.text[:500]}")
            )
            raise RuntimeError(detail)
        candidates = response.json().get("candidates") or []
        parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []
        return "".join(str(part.get("text") or "") for part in parts)


class XaiProvider:
    """xAI Grok chat completions. Not the Cursor IDE agent (that can see gold files)."""

    name = "xai"

    def __init__(self, api_key: str | None = None, timeout: float = 300.0) -> None:
        self.api_key = api_key or os.environ.get("XAI_API_KEY", "")
        self.timeout = timeout

    def generate(self, prompt: str, *, model: str, temperature: float) -> str:
        if not self.api_key:
            raise MissingCredentialsError("XAI_API_KEY is not set")
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = httpx.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=self.timeout,
        )
        if response.is_error:
            from decomposition.llm.parse import format_validation_error

            detail = format_validation_error(
                RuntimeError(f"xAI HTTP {response.status_code}: {response.text[:500]}")
            )
            raise RuntimeError(detail)
        return str(response.json()["choices"][0]["message"]["content"])


class OllamaProvider:
    name = "ollama"

    def __init__(self, host: str | None = None, timeout: float = 300.0) -> None:
        self.host = (host or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip(
            "/"
        )
        self.timeout = timeout

    def generate(self, prompt: str, *, model: str, temperature: float) -> str:
        payload = {
            "model": model,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature},
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = httpx.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout)
        except httpx.ConnectError as exc:
            raise MissingCredentialsError(f"Ollama is not reachable at {self.host}") from exc
        if response.is_error:
            from decomposition.llm.parse import format_validation_error

            detail = format_validation_error(
                RuntimeError(f"Ollama HTTP {response.status_code}: {response.text[:500]}")
            )
            raise RuntimeError(detail)
        return str(response.json().get("message", {}).get("content") or "")


class MockProvider:
    """Test double. Outputs are not scientific LLM results."""

    name = "mock"

    def __init__(self, canned: str | None = None) -> None:
        self.canned = canned

    def generate(self, prompt: str, *, model: str, temperature: float) -> str:
        if self.canned is not None:
            return self.canned
        names = _component_names_from_prompt(prompt)
        if not names:
            names = ["ExampleService"]
        services = [
            {
                "name": "mock-service",
                "components": names,
                "owned_entities": [],
                "responsibilities": ["mock holdover; not a scientific result"],
                "dependencies": [],
                "rationale": "Deterministic mock provider.",
            }
        ]
        import json

        return json.dumps(
            {
                "services": services,
                "migration_priority": [
                    {"service": "mock-service", "rank": 1, "confidence": 0.0, "reason": "mock"}
                ],
                "uncertain_decisions": ["entire mock assignment"],
                "unsupported_assumptions": [],
                "rule_violations": [],
                "architectural_risks": [],
                "critique": "mock",
                "revised": False,
            }
        )


def credentials_available(name: str, *, allow_local_ollama: bool = False) -> tuple[bool, str]:
    """Return whether a provider can be called. Never logs secret values."""
    key = name.lower().strip()
    if key == "openai":
        ok = bool(os.environ.get("OPENAI_API_KEY"))
        return ok, "" if ok else "OPENAI_API_KEY is not set"
    if key == "anthropic":
        ok = bool(os.environ.get("ANTHROPIC_API_KEY"))
        return ok, "" if ok else "ANTHROPIC_API_KEY is not set"
    if key == "gemini":
        ok = bool(os.environ.get("GEMINI_API_KEY"))
        return ok, "" if ok else "GEMINI_API_KEY is not set"
    if key in {"xai", "grok"}:
        ok = bool(os.environ.get("XAI_API_KEY"))
        return ok, "" if ok else "XAI_API_KEY is not set"
    if key == "ollama":
        host_set = bool(os.environ.get("OLLAMA_HOST") or os.environ.get("SEMS_ENABLE_OLLAMA"))
        if allow_local_ollama or host_set:
            return True, ""
        return False, "OLLAMA_HOST or SEMS_ENABLE_OLLAMA is not set; not probing localhost"
    if key == "mock":
        return False, "mock is not a scientific LLM provider"
    return False, f"unknown provider: {name}"


def get_provider(name: str) -> LLMProvider:
    key = name.lower().strip()
    if key == "openai":
        return OpenAIProvider()
    if key == "anthropic":
        return AnthropicProvider()
    if key == "gemini":
        return GeminiProvider()
    if key in {"xai", "grok"}:
        return XaiProvider()
    if key == "ollama":
        return OllamaProvider()
    if key == "mock":
        return MockProvider()
    raise ValueError(f"unknown provider: {name}")


def _component_names_from_prompt(prompt: str) -> list[str]:
    names = []
    for line in prompt.splitlines():
        if line.startswith("- ") and "[" in line and "module=" in line:
            names.append(line[2:].split(" [", 1)[0].strip())
    return names
