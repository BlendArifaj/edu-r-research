from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.security import hash_password
from attendance.main import create_app as attendance_app
from common.http import Peers
from common.peers import set_peers
from faculty.main import create_app as faculty_app
from finance.main import create_app as finance_app
from gateway.main import create_app as gateway_app
from grade.main import create_app as grade_app
from identity.main import create_app as identity_app
from identity.models import User
from library.main import create_app as library_app
from student.main import create_app as student_app

ADMIN_EMAIL = "admin@sems-r.local"
ADMIN_PASSWORD = "admin123"


def sqlite_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )


def build_gateway() -> TestClient:
    identity_engine = sqlite_engine()
    identity = identity_app(identity_engine)
    apps = {
        "identity": identity,
        "faculty": faculty_app(sqlite_engine()),
        "student": student_app(sqlite_engine()),
        "grade": grade_app(sqlite_engine()),
        "finance": finance_app(sqlite_engine()),
        "attendance": attendance_app(sqlite_engine()),
        "library": library_app(sqlite_engine()),
    }
    peers = Peers(apps=apps)
    set_peers(peers)
    gateway = gateway_app(peers=peers, identity_engine=identity_engine)
    _insert_admin(identity_engine)
    return TestClient(gateway)


def _insert_admin(engine) -> None:
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db: Session = factory()
    try:
        db.add(
            User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                full_name="SEMS-R Admin",
                role="admin",
            )
        )
        db.commit()
    finally:
        db.close()


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
