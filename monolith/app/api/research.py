from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.deps import get_current_user
from app.instrumentation.store import get_store
from app.models import User

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/traces")
def list_traces(
    limit: int = Query(default=100, ge=1, le=5000),
    _: User = Depends(get_current_user),
) -> JSONResponse:
    return JSONResponse(
        {
            "integrity": "sems-r-reconstruction-measured",
            "traces": get_store().snapshot(limit=limit),
        }
    )


@router.get("/traces/summary")
def trace_summary(_: User = Depends(get_current_user)) -> dict[str, object]:
    return get_store().summary()
