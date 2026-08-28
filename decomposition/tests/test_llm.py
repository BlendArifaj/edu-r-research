from pathlib import Path

from decomposition.extraction.evidence_builder import FORBIDDEN_GOLD
from decomposition.llm.convert import proposal_to_decomposition
from decomposition.llm.parse import format_validation_error, parse_proposal
from decomposition.llm.prompts import build_prompt
from decomposition.llm.providers import MockProvider
from decomposition.llm.runner import run_llm_experiments

ROOT = Path(__file__).resolve().parents[2]


def _tiny_evidence() -> dict:
    return {
        "system": {"name": "SEMS-R", "is_original_sems_source": False},
        "components": [
            {"name": "FacultyService", "kind": "service", "module": "app.services.faculty_service"},
            {"name": "LibraryService", "kind": "service", "module": "app.services.library_service"},
        ],
        "dependencies": {
            "G_call": [{"from": "FacultyService", "to": "LibraryService", "kind": "call"}]
        },
        "database_usage": [
            {
                "component": "FacultyService",
                "entity": "Faculty",
                "static_direct": True,
                "static_via_repository": False,
            }
        ],
        "entity_ownership": [
            {
                "entity": "Faculty",
                "table": "faculties",
                "sharing_degree": 1,
                "candidate_owner": "FacultyService",
                "accessing_components": ["FacultyService"],
            }
        ],
        "runtime_interactions": {"available": False, "note": "empty rather than fabricated"},
        "domain_descriptions": {
            "system": {"description": "A reconstructed university system."},
            "functional_areas": [{"id": "faculty", "capabilities": ["course catalog"]}],
            "known_cross_domain_dependencies": ["Library membership is issued to staff."],
        },
        "migration_constraints": {
            "rules": [{"id": "R1", "statement": "Decompose into independently deployable services."}],
            "machine_checkable": ["no_empty_services"],
        },
    }


def test_c0_omits_call_graph_c1_includes_it() -> None:
    evidence = _tiny_evidence()
    c0 = build_prompt("C0", evidence)
    c1 = build_prompt("C1", evidence)
    assert "FacultyService" in c0
    assert "Call dependencies" not in c0
    assert "FacultyService -> LibraryService" not in c0
    assert "Call dependencies" in c1
    assert "FacultyService -> LibraryService" in c1
    assert FORBIDDEN_GOLD not in c0
    assert FORBIDDEN_GOLD not in c1


def test_c2_adds_rules_c3_adds_critique() -> None:
    evidence = _tiny_evidence()
    c1 = build_prompt("C1", evidence)
    c2 = build_prompt("C2", evidence)
    c3 = build_prompt("C3", evidence)
    assert "R1:" not in c1
    assert "R1:" in c2
    assert "Self-critique" not in c2
    assert "Self-critique" in c3
    assert FORBIDDEN_GOLD not in c3


def test_parse_fenced_json() -> None:
    raw = """```json
    {"services": [{"name": "s", "components": ["AService"]}], "uncertain_decisions": []}
    ```"""
    proposal = parse_proposal(raw)
    assert proposal.services[0].name == "s"
    assert proposal.services[0].components == ["AService"]


def test_invalid_json_is_not_fabricated(tmp_path: Path) -> None:
    class Bad:
        name = "mock"

        def generate(self, prompt: str, *, model: str, temperature: float) -> str:
            return "this is not json"

    results = run_llm_experiments(
        evidence=_tiny_evidence(),
        provider=Bad(),  # type: ignore[arg-type]
        model="unit-test",
        conditions=["C0"],
        runs=1,
        temperature=0.0,
        max_retries=0,
        out_dir=tmp_path,
        scientific=True,
    )
    assert results[0]["parse_ok"] is False
    assert results[0]["is_scientific_run"] is False
    parsed = (tmp_path / "unit-test" / "C0" / "run_01" / "parsed.json").read_text()
    assert parsed.strip() == "null"


def test_retry_then_success(tmp_path: Path) -> None:
    class Flaky:
        name = "mock"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, prompt: str, *, model: str, temperature: float) -> str:
            self.calls += 1
            if self.calls < 2:
                return "nope"
            return '{"services":[{"name":"s","components":["FacultyService","LibraryService"]}]}'

    flaky = Flaky()
    results = run_llm_experiments(
        evidence=_tiny_evidence(),
        provider=flaky,  # type: ignore[arg-type]
        model="unit-test",
        conditions=["C0"],
        runs=1,
        temperature=0.0,
        max_retries=2,
        out_dir=tmp_path,
        scientific=True,
    )
    assert flaky.calls == 2
    assert results[0]["parse_ok"] is True
    payload = __import__("json").loads(
        (tmp_path / "unit-test" / "C0" / "run_01" / "parsed.json").read_text()
    )
    assert payload["component_assignment"]["FacultyService"] == "s"
    assert payload["system"]["gold_labels_used"] is False


def test_mock_run_is_not_scientific(tmp_path: Path) -> None:
    results = run_llm_experiments(
        evidence=_tiny_evidence(),
        provider=MockProvider(),
        model="mock-not-a-model",
        conditions=["C0"],
        runs=1,
        temperature=0.0,
        max_retries=0,
        out_dir=tmp_path,
        scientific=False,
    )
    assert results[0]["is_scientific_run"] is False
    assert results[0]["parse_ok"] is True


def test_convert_records_duplicates() -> None:
    proposal = parse_proposal(
        '{"services":[{"name":"a","components":["X"]},{"name":"b","components":["X"]}]}'
    )
    dumped = proposal_to_decomposition(proposal, method="llm_test", metadata={"condition": "C0"})
    assert dumped["component_assignment"]["X"] == "b"
    assert dumped["rule_violations"]


def test_http_errors_do_not_keep_api_keys() -> None:
    leaked = "Client error '404 Not Found' for url 'https://example.com/v1?key=SECRET123'"
    redacted = format_validation_error(RuntimeError(leaked))
    assert "SECRET123" not in redacted
    assert "key=REDACTED" in redacted


def test_full_evidence_c3_prompt_excludes_gold() -> None:
    import json

    evidence_path = ROOT / "outputs/evidence/architectural_evidence.json"
    if not evidence_path.exists():
        return
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    prompt = build_prompt("C3", evidence)
    assert FORBIDDEN_GOLD not in prompt
    assert "StudentService" in prompt
    assert "R9:" in prompt
    assert "Call dependencies" in prompt
