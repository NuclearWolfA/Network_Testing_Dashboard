from fastapi import APIRouter

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import BackendInstance, Message, Node
from app.services.backend_registry import to_network_dict, upsert_backend_instance


router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.get("/dummy")
def dummy_analyze_api() -> dict[str, str]:
    return {"message": "dummy analyze api"}


@router.get("/nodes")
def list_nodes() -> list[dict[str, str]]:
    session = SessionLocal()
    try:
        nodes = session.query(Node).order_by(Node.backend_id.asc(), Node.node_id.asc()).all()
        return [
            {
                "node_id": node.node_id,
                "backend_id": node.backend_id,
                "last_byte": node.last_byte,
            }
            for node in nodes
        ]
    finally:
        session.close()


@router.get("/nodes/{node_id}/sender-sequences")
def get_sender_sequence_numbers(node_id: str) -> dict[str, str | list[int] | int]:
    session = SessionLocal()
    try:
        rows = (
            session.query(Message.sequence_number)
            .filter(Message.source == node_id)
            .distinct()
            .order_by(Message.sequence_number.asc())
            .all()
        )

        sequence_numbers = [row[0] for row in rows]
        return {
            "node_id": node_id,
            "count": len(sequence_numbers),
            "sequence_numbers": sequence_numbers,
        }
    finally:
        session.close()


@router.get("/nodes/{node_id}/messages")
def get_sender_messages(node_id: str) -> dict[str, str | int | list[dict[str, str | int | None]]]:
    session = SessionLocal()
    try:
        rows = (
            session.query(Message)
            .filter(Message.source == node_id)
            .order_by(Message.sequence_number.asc(), Message.id.asc())
            .all()
        )

        unique_messages: dict[int, Message] = {}
        for row in rows:
            if row.sequence_number not in unique_messages:
                unique_messages[row.sequence_number] = row

        messages = [
            {
                "sequence_number": row.sequence_number,
                "source": row.source,
                "destination": row.destination,
                "portnum": row.portnum,
                "message_type": row.message_type,
            }
            for _, row in sorted(unique_messages.items(), key=lambda item: item[0])
        ]

        return {
            "node_id": node_id,
            "count": len(messages),
            "messages": messages,
        }
    finally:
        session.close()


@router.get("/nodes/{node_id}/messages/{sequence_number}/reports")
def get_sequence_reports(node_id: str, sequence_number: int) -> dict[str, str | int | list[dict[str, str | int | None]]]:
    session = SessionLocal()
    try:
        rows = (
            session.query(Message)
            .filter(Message.source == node_id, Message.sequence_number == sequence_number)
            .order_by(Message.timestamp.asc(), Message.id.asc())
            .all()
        )

        reports = [
            {
                "id": row.id,
                "source": row.source,
                "destination": row.destination,
                "reporter": row.reporter,
                "sequence_number": row.sequence_number,
                "timestamp": row.timestamp.isoformat(),
                "next_hop": row.next_hop,
                "relay_node": row.relay_node,
                "portnum": row.portnum,
                "message_type": row.message_type,
                "request_id": row.request_id,
            }
            for row in rows
        ]

        return {
            "node_id": node_id,
            "sequence_number": sequence_number,
            "count": len(reports),
            "reports": reports,
        }
    finally:
        session.close()


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
