from pathlib import Path

from workload.config_loader import JOURNEY_NAMES, load_config
from workload.datasets import load_dataset
from workload.scenarios import registration, student_dashboard

from tests.test_domain_flows import _bootstrap_academic_graph


def test_all_load_configs_mix_to_100() -> None:
    config_dir = Path(__file__).resolve().parents[2] / "workload" / "config"
    for path in sorted(config_dir.glob("*.yaml")):
        config = load_config(path.stem)
        assert sum(config.mix.values()) == 100, path
        assert tuple(config.mix) == JOURNEY_NAMES
        assert "not production" in config.integrity or "not_production" in config.integrity


def test_student_dashboard_against_test_client(client, auth_headers) -> None:
    _bootstrap_academic_graph(client, auth_headers)
    data = load_dataset(client, auth_headers)
    assert data.student_ids
    assert data.course_ids
    student_dashboard(client, auth_headers, data)


def test_registration_skips_duplicate_semester_post(client, auth_headers) -> None:
    _bootstrap_academic_graph(client, auth_headers)
    data = load_dataset(client, auth_headers)
    registration(client, auth_headers, data)
    registration(client, auth_headers, data)
    student_id = data.student_ids[0]
    rows = client.get(
        f"/api/v1/students/{student_id}/semester-registrations", headers=auth_headers
    ).json()
    assert len(rows) == 1
