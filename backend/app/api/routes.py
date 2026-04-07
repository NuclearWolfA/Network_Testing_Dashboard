import base64
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.entities import LogicalPacket, MqttMessage, Node, PacketObservation, RouteHop
from app.services.ingestion import persist_mqtt_message


router = APIRouter()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class IngestRequest(BaseModel):
    topic: str
    qos: int = Field(default=0, ge=0, le=2)
    retain: bool = False
    payload: str
    payload_is_base64: bool = False
    connection_id: str | None = None
    session_id: int | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


@router.post("/ingest")
def ingest_message(request: IngestRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    payload_raw = base64.b64decode(request.payload) if request.payload_is_base64 else request.payload.encode("utf-8")
    mqtt_message = persist_mqtt_message(
        db=db,
        topic=request.topic,
        qos=request.qos,
        retain=request.retain,
        payload_raw=payload_raw,
        connection_id=request.connection_id,
        session_id=request.session_id,
        meta=request.meta,
    )
    return {
        "mqtt_message_id": mqtt_message.id,
        "parse_status": mqtt_message.parse_status,
        "created_at": mqtt_message.created_at,
    }


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)) -> dict[str, Any]:
    total_messages = db.scalar(select(func.count(MqttMessage.id))) or 0
    parsed_messages = db.scalar(select(func.count(MqttMessage.id)).where(MqttMessage.parse_status == "parsed")) or 0
    encoded_unparsed = (
        db.scalar(select(func.count(MqttMessage.id)).where(MqttMessage.parse_status == "encoded_topic_unparsed")) or 0
    )
    total_packets = db.scalar(select(func.count(LogicalPacket.id))) or 0
    total_observations = db.scalar(select(func.count(PacketObservation.id))) or 0
    duplicates = db.scalar(select(func.count(LogicalPacket.id)).where(LogicalPacket.observation_count > 1)) or 0

    return {
        "total_messages": total_messages,
        "parsed_messages": parsed_messages,
        "encoded_unparsed_messages": encoded_unparsed,
        "parse_rate": (parsed_messages / total_messages) if total_messages else 0.0,
        "logical_packets": total_packets,
        "packet_observations": total_observations,
        "duplicate_logical_packets": duplicates,
    }


@router.get("/nodes/stats")
def get_node_stats(db: Session = Depends(get_db), limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    traffic = db.execute(
        select(
            func.coalesce(LogicalPacket.from_node, LogicalPacket.sender).label("node_num"),
            func.count(LogicalPacket.id).label("packet_count"),
            func.max(LogicalPacket.last_seen_at).label("last_seen_at"),
        )
        .group_by("node_num")
        .order_by(func.count(LogicalPacket.id).desc())
        .limit(limit)
    ).all()

    known_nodes = {
        row.node_num: row
        for row in db.execute(select(Node).where(Node.node_num.in_([r.node_num for r in traffic if r.node_num is not None]))).scalars()
    }

    response: list[dict[str, Any]] = []
    for row in traffic:
        node = known_nodes.get(row.node_num)
        response.append(
            {
                "node_num": row.node_num,
                "packet_count": row.packet_count,
                "last_seen_at": row.last_seen_at,
                "short_name": node.short_name if node else None,
                "long_name": node.long_name if node else None,
            }
        )
    return response


@router.get("/messages/recent")
def get_recent_messages(db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    rows = db.execute(select(MqttMessage).order_by(MqttMessage.created_at.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "topic": row.topic,
            "qos": row.qos,
            "retain": row.retain,
            "created_at": row.created_at,
            "connection_id": row.connection_id,
            "parse_status": row.parse_status,
            "raw_payload": row.raw_payload,
        }
        for row in rows
    ]


@router.get("/packets/search")
def search_packets(
    db: Session = Depends(get_db),
    from_node: int | None = None,
    to_node: int | None = None,
    packet_type: str | None = None,
    session_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    stmt = select(LogicalPacket)
    if from_node is not None:
        stmt = stmt.where(LogicalPacket.from_node == from_node)
    if to_node is not None:
        stmt = stmt.where(LogicalPacket.to_node == to_node)
    if packet_type is not None:
        stmt = stmt.where(LogicalPacket.packet_type == packet_type)
    if session_id is not None:
        stmt = stmt.where(LogicalPacket.session_id == session_id)

    rows = db.execute(stmt.order_by(LogicalPacket.last_seen_at.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "session_id": row.session_id,
            "fingerprint": row.fingerprint,
            "inner_packet_id": row.inner_packet_id,
            "channel": row.channel,
            "from": row.from_node,
            "hop_start": row.hop_start,
            "hops_away": row.hops_away,
            "sender": row.sender,
            "timestamp": row.packet_timestamp,
            "to": row.to_node,
            "type": row.packet_type,
            "payload": row.payload,
            "next_hop": row.next_hop,
            "relay_node": row.relay_node,
            "rssi": row.rssi,
            "snr": row.snr,
            "first_seen_at": row.first_seen_at,
            "last_seen_at": row.last_seen_at,
            "observation_count": row.observation_count,
        }
        for row in rows
    ]


@router.get("/packets/{packet_id}/path")
def get_packet_path(packet_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    packet = db.execute(select(LogicalPacket).where(LogicalPacket.id == packet_id)).scalar_one_or_none()
    if packet is None:
        return {"packet": None, "route_hops": [], "observations": []}

    route_hops = db.execute(
        select(RouteHop).where(RouteHop.logical_packet_id == packet_id).order_by(RouteHop.hop_index.asc())
    ).scalars().all()
    observations = db.execute(
        select(PacketObservation)
        .where(PacketObservation.logical_packet_id == packet_id)
        .order_by(PacketObservation.observed_at.asc())
    ).scalars().all()

    return {
        "packet": {
            "id": packet.id,
            "from": packet.from_node,
            "to": packet.to_node,
            "type": packet.packet_type,
            "timestamp": packet.packet_timestamp,
            "observation_count": packet.observation_count,
        },
        "route_hops": [
            {
                "hop_index": hop.hop_index,
                "from_node": hop.from_node_num,
                "to_node": hop.to_node_num,
                "observed_at": hop.observed_at,
                "meta": hop.meta,
            }
            for hop in route_hops
        ],
        "observations": [
            {
                "id": obs.id,
                "mqtt_message_id": obs.mqtt_message_id,
                "observed_at": obs.observed_at,
                "topic": obs.topic,
                "connection_id": obs.connection_id,
                "hop_start": obs.hop_start,
                "hops_away": obs.hops_away,
                "next_hop": obs.next_hop,
                "relay_node": obs.relay_node,
                "rssi": obs.rssi,
                "snr": obs.snr,
            }
            for obs in observations
        ],
    }


@router.get("/packets/duplicates")
def get_duplicates(db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, Any]]:
    rows = db.execute(
        select(LogicalPacket)
        .where(LogicalPacket.observation_count > 1)
        .order_by(LogicalPacket.observation_count.desc(), LogicalPacket.last_seen_at.desc())
        .limit(limit)
    ).scalars().all()
    return [
        {
            "id": row.id,
            "fingerprint": row.fingerprint,
            "inner_packet_id": row.inner_packet_id,
            "from": row.from_node,
            "to": row.to_node,
            "type": row.packet_type,
            "timestamp": row.packet_timestamp,
            "observation_count": row.observation_count,
            "last_seen_at": row.last_seen_at,
        }
        for row in rows
    ]
