"""Locust entrypoint. Architecture-neutral: set BASE_URL / --host only.

MONOLITH:       BASE_URL=http://localhost:8000 locust -f workload/locustfile.py
MICROSERVICES:  BASE_URL=http://localhost:8080 locust -f workload/locustfile.py
"""

import sys
from pathlib import Path

from locust import events

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from workload.users import SemsUser  # noqa: F401

__all__ = ["SemsUser"]


@events.test_start.add_listener
def _on_start(environment, **_kwargs) -> None:
    host = environment.host or "unset"
    print(
        f"SEMS-R Locust starting against {host}. "
        "Synthetic reconstruction workload, not production SEMS traffic."
    )
