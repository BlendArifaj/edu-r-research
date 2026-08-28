from fastapi.testclient import TestClient

from clustered.assembly import create_campus_app
from common.http import Peers
from common.peers import get_peers, set_peers
from harness import ADMIN_EMAIL, ADMIN_PASSWORD, _insert_admin, sqlite_engine


def _core_engines() -> dict:
    return {
        "identity": sqlite_engine(),
        "faculty": sqlite_engine(),
        "student": sqlite_engine(),
        "grade": sqlite_engine(),
        "finance": sqlite_engine(),
        "attendance": sqlite_engine(),
    }


def test_campus_keeps_library_as_http_and_core_in_process() -> None:
    set_peers(Peers())
    engines = _core_engines()
    app = create_campus_app(engines=engines, library_url="http://library.test:8000")
    peers = get_peers()
    assert "student" in peers._apps
    assert "grade" in peers._apps
    assert "faculty" in peers._apps
    assert "finance" in peers._apps
    assert "attendance" in peers._apps
    assert "library" not in peers._apps
    assert peers._urls["library"] == "http://library.test:8000"
    client = TestClient(app)
    assert client.get("/internal/students/1").status_code != 404
    assert client.get("/internal/courses/1").status_code != 404
    assert client.get("/internal/staff-user-ids").status_code != 404


def test_campus_with_in_process_library_can_login() -> None:
    engines = {**_core_engines(), "library": sqlite_engine()}
    app = create_campus_app(engines=engines, include_library_app=True)
    _insert_admin(engines["identity"])
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert login.status_code == 200, login.text
