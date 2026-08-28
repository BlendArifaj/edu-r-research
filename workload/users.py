from __future__ import annotations

import os
from typing import Any

from locust import HttpUser, between, task

from workload.config_loader import DEFAULT_MIX, load_config
from workload.datasets import WorkloadData, load_dataset
from workload.scenarios import JOURNEYS

ADMIN_EMAIL = os.environ.get("SEMS_ADMIN_EMAIL", "admin@sems-r.local")
ADMIN_PASSWORD = os.environ.get("SEMS_ADMIN_PASSWORD", "admin123")

_CONFIG_NAME = os.environ.get("SEMS_WORKLOAD_CONFIG", "smoke")
try:
    _CONFIG = load_config(_CONFIG_NAME)
    MIX = _CONFIG.mix
    WAIT = between(_CONFIG.wait_min_s, _CONFIG.wait_max_s)
except Exception:
    MIX = DEFAULT_MIX
    WAIT = between(0.05, 0.3)


def login(client: Any, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        name="/api/v1/auth/login",
    )
    if response.status_code != 200:
        raise RuntimeError(f"login failed for {email}: {response.status_code} {response.text}")
    return str(response.json()["access_token"])


class SemsUser(HttpUser):
    """Architecture-neutral SEMS-R user. Target only via BASE_URL / --host."""

    wait_time = WAIT

    def on_start(self) -> None:
        token = login(self.client, ADMIN_EMAIL, ADMIN_PASSWORD)
        self.headers = {"Authorization": f"Bearer {token}"}
        self.data: WorkloadData = load_dataset(self.client, self.headers)
        if not self.data.student_ids:
            raise RuntimeError("target has no students; seed SEMS-R before running Locust")

    @task(MIX["student_dashboard"])
    def student_dashboard(self) -> None:
        JOURNEYS["student_dashboard"](self.client, self.headers, self.data)

    @task(MIX["grades"])
    def grades(self) -> None:
        JOURNEYS["grades"](self.client, self.headers, self.data)

    @task(MIX["registration"])
    def registration(self) -> None:
        JOURNEYS["registration"](self.client, self.headers, self.data)

    @task(MIX["finance"])
    def finance(self) -> None:
        JOURNEYS["finance"](self.client, self.headers, self.data)

    @task(MIX["attendance"])
    def attendance(self) -> None:
        JOURNEYS["attendance"](self.client, self.headers, self.data)

    @task(MIX["library"])
    def library(self) -> None:
        JOURNEYS["library"](self.client, self.headers, self.data)

    @task(MIX["faculty_admin"])
    def faculty_admin(self) -> None:
        JOURNEYS["faculty_admin"](self.client, self.headers, self.data)
