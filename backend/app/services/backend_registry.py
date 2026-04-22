from __future__ import annotations

from datetime import datetime, timezone
import socket
from urllib.error import URLError
from urllib.request import urlopen

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import BackendInstance


def _get_local_ip() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def _get_public_ip() -> str | None:
    try:
        with urlopen(settings.backend_public_ip_service_url, timeout=3) as response:
            public_ip = response.read().decode("utf-8").strip()
            return public_ip or None
    except (URLError, OSError, TimeoutError):
        return None


def _build_base_url(local_ip: str | None, public_ip: str | None, announced_port: int) -> str:
    if settings.backend_public_base_url:
        return settings.backend_public_base_url.rstrip("/")

    host = public_ip or local_ip or "127.0.0.1"
    return f"{settings.backend_scheme}://{host}:{announced_port}"


def upsert_backend_instance(db: Session) -> BackendInstance:
    local_ip = _get_local_ip()
    public_ip = _get_public_ip()
    announced_port = settings.backend_public_port or settings.backend_bind_port
    nat_detected = bool(local_ip and public_ip and local_ip != public_ip)

    backend = db.query(BackendInstance).filter(BackendInstance.backend_id == settings.backend_id).one_or_none()

    base_url = _build_base_url(local_ip=local_ip, public_ip=public_ip, announced_port=announced_port)

    if backend is None:
        backend = BackendInstance(
            backend_id=settings.backend_id,
            scheme=settings.backend_scheme,
            local_ip=local_ip,
            local_port=settings.backend_bind_port,
            public_ip=public_ip,
            public_port=announced_port,
            base_url=base_url,
            nat_detected=nat_detected,
            extra={"public_ip_service_url": settings.backend_public_ip_service_url},
        )
        db.add(backend)
    else:
        backend.scheme = settings.backend_scheme
        backend.local_ip = local_ip
        backend.local_port = settings.backend_bind_port
        backend.public_ip = public_ip
        backend.public_port = announced_port
        backend.base_url = base_url
        backend.nat_detected = nat_detected
        backend.last_seen = datetime.now(timezone.utc)
        backend.extra = {"public_ip_service_url": settings.backend_public_ip_service_url}

    db.commit()
    db.refresh(backend)
    return backend


def to_network_dict(backend: BackendInstance) -> dict[str, str | int | bool | None]:
    return {
        "backend_id": backend.backend_id,
        "scheme": backend.scheme,
        "local_ip": backend.local_ip,
        "local_port": backend.local_port,
        "public_ip": backend.public_ip,
        "public_port": backend.public_port,
        "base_url": backend.base_url,
        "nat_detected": backend.nat_detected,
        "last_seen": backend.last_seen.isoformat() if backend.last_seen else None,
    }
