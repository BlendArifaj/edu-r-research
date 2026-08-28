from collections.abc import Generator

from fastapi.testclient import TestClient
from harness import auth_headers as make_headers
from harness import build_gateway
from pytest import fixture


@fixture()
def client() -> Generator[TestClient, None, None]:
    yield build_gateway()


@fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    return make_headers(client)
