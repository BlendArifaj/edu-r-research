from app.instrumentation.store import get_store
from tests.test_domain_flows import _bootstrap_academic_graph


def test_list_students_records_sql_and_components(client, auth_headers) -> None:
    get_store().clear()
    response = client.get("/api/v1/students", headers=auth_headers)
    assert response.status_code == 200
    traces = get_store().snapshot()
    matching = [row for row in traces if row["path"] == "/api/v1/students" and row["method"] == "GET"]
    assert matching, traces
    trace = matching[-1]
    assert trace["sql_query_count"] >= 1
    assert "students" in trace["database_entities"]
    assert "StudentService" in trace["components"] or "StudentRepository" in trace["components"]
    assert trace["integrity"] == "sems-r-reconstruction-measured"
    assert trace["duration_ms"] >= 0
    assert "X-Request-ID" in response.headers


def test_health_is_not_traced(client) -> None:
    get_store().clear()
    response = client.get("/health")
    assert response.status_code == 200
    assert get_store().snapshot() == []


def test_overview_touches_multiple_components(client, auth_headers) -> None:
    ids = _bootstrap_academic_graph(client, auth_headers)
    get_store().clear()
    response = client.get(f"/api/v1/students/{ids['student_id']}/overview", headers=auth_headers)
    assert response.status_code == 200, response.text
    traces = [
        row
        for row in get_store().snapshot()
        if row["path"].endswith("/overview")
    ]
    assert traces
    components = set(traces[-1]["components"])
    assert "StudentOverviewService" in components
    assert traces[-1]["sql_query_count"] >= 1
