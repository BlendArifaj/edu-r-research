from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

from app.api import attendance, auth, faculty, finance, grade, library, research, student
from app.exceptions import AuthorizationError, ConflictError, DomainError, NotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(_, exc: NotFoundError) -> JSONResponse:
        return JSONResponse({"detail": exc.message}, status_code=404)

    @app.exception_handler(ConflictError)
    async def conflict_handler(_, exc: ConflictError) -> JSONResponse:
        return JSONResponse({"detail": exc.message}, status_code=409)

    @app.exception_handler(AuthorizationError)
    async def auth_handler(_, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse({"detail": exc.message}, status_code=401)

    @app.exception_handler(DomainError)
    async def domain_handler(_, exc: DomainError) -> JSONResponse:
        return JSONResponse({"detail": exc.message}, status_code=400)


def build_api_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(auth.router)
    router.include_router(faculty.router)
    router.include_router(student.router)
    router.include_router(grade.router)
    router.include_router(finance.router)
    router.include_router(attendance.router)
    router.include_router(library.router)
    router.include_router(research.router)
    return router
