from fastapi import APIRouter

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import BackendInstance
from app.services.backend_registry import to_network_dict, upsert_backend_instance


router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.get("/dummy")
def dummy_analyze_api() -> dict[str, str]:
    return {"message": "dummy analyze api"}


@router.post("/backend/register")
def register_backend_network() -> dict[str, str | int | bool | None]:
    session = SessionLocal()
    try:
        backend = upsert_backend_instance(session)
        return to_network_dict(backend)
    finally:
        session.close()


@router.get("/backend/me")
def get_backend_network() -> dict[str, str | int | bool | None]:
    session = SessionLocal()
    try:
        backend = (
            session.query(BackendInstance)
            .filter(BackendInstance.backend_id == settings.backend_id)
            .one_or_none()
        )
        if backend is None:
            backend = upsert_backend_instance(session)

        return to_network_dict(backend)
    finally:
        session.close()
