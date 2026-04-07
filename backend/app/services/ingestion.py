import base64
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.entities import LogicalPacket, MqttMessage, Node, PacketObservation, RouteHop
from app.services.parser import parse_meshtastic_payload


def _upsert_node(db: Session, node_num: int | None) -> int | None:
    if node_num is None:
        return None
    stmt: Select[tuple[Node]] = select(Node).where(Node.node_num == node_num).order_by(Node.id.desc()).limit(1)
    node = db.execute(stmt).scalar_one_or_none()
    now = datetime.now(UTC)
    if node is None:
        node = Node(node_num=node_num, last_seen_at=now)
        db.add(node)
        db.flush()
    else:
        node.last_seen_at = now
    return node.id


def _set_route_hops(db: Session, logical_packet_id: int, route: Any) -> None:
    if not isinstance(route, list) or len(route) < 2:
        return
    for i in range(len(route) - 1):
        from_num = route[i]
        to_num = route[i + 1]
        if not isinstance(from_num, int) or not isinstance(to_num, int):
            continue
        route_hop = RouteHop(
            logical_packet_id=logical_packet_id,
            hop_index=i,
            from_node_id=_upsert_node(db, from_num),
            to_node_id=_upsert_node(db, to_num),
            from_node_num=from_num,
            to_node_num=to_num,
        )
        db.add(route_hop)


def persist_mqtt_message(
    db: Session,
    topic: str,
    qos: int,
    retain: bool,
    payload_raw: bytes,
    connection_id: str | None = None,
    meta: dict[str, Any] | None = None,
    session_id: int | None = None,
) -> MqttMessage:
    parse_result = parse_meshtastic_payload(topic=topic, payload_raw=payload_raw)

    try:
        raw_payload_text = payload_raw.decode("utf-8")
    except UnicodeDecodeError:
        raw_payload_text = "base64:" + base64.b64encode(payload_raw).decode("ascii")
    mqtt_message = MqttMessage(
        topic=topic,
        qos=qos,
        retain=retain,
        connection_id=connection_id,
        meta=meta or {},
        raw_payload=raw_payload_text,
        payload_text=parse_result.payload_text,
        parse_status=parse_result.status,
        session_id=session_id,
    )
    db.add(mqtt_message)
    db.flush()

    if parse_result.packet is None or parse_result.fingerprint is None:
        db.commit()
        db.refresh(mqtt_message)
        return mqtt_message

    packet_stmt = select(LogicalPacket).where(LogicalPacket.fingerprint == parse_result.fingerprint)
    if session_id is None:
        packet_stmt = packet_stmt.where(LogicalPacket.session_id.is_(None))
    else:
        packet_stmt = packet_stmt.where(LogicalPacket.session_id == session_id)

    logical_packet = db.execute(packet_stmt.limit(1)).scalar_one_or_none()
    if logical_packet is None:
        logical_packet = LogicalPacket(
            fingerprint=parse_result.fingerprint,
            session_id=session_id,
            inner_packet_id=parse_result.packet.get("inner_packet_id"),
            channel=parse_result.packet.get("channel"),
            from_node=parse_result.packet.get("from_node"),
            hop_start=parse_result.packet.get("hop_start"),
            hops_away=parse_result.packet.get("hops_away"),
            sender=parse_result.packet.get("sender"),
            packet_timestamp=parse_result.packet.get("packet_timestamp"),
            to_node=parse_result.packet.get("to_node"),
            packet_type=parse_result.packet.get("packet_type"),
            payload=parse_result.packet.get("payload"),
            next_hop=parse_result.packet.get("next_hop"),
            relay_node=parse_result.packet.get("relay_node"),
            rssi=parse_result.packet.get("rssi"),
            snr=parse_result.packet.get("snr"),
            observation_count=0,
        )
        db.add(logical_packet)
        db.flush()

    logical_packet.last_seen_at = datetime.now(UTC)
    logical_packet.observation_count += 1

    _upsert_node(db, logical_packet.from_node)
    _upsert_node(db, logical_packet.to_node)
    _upsert_node(db, logical_packet.sender)
    _upsert_node(db, logical_packet.next_hop)
    _upsert_node(db, logical_packet.relay_node)

    observation = PacketObservation(
        logical_packet_id=logical_packet.id,
        mqtt_message_id=mqtt_message.id,
        session_id=session_id,
        topic=topic,
        connection_id=connection_id,
        hop_start=logical_packet.hop_start,
        hops_away=logical_packet.hops_away,
        next_hop=logical_packet.next_hop,
        relay_node=logical_packet.relay_node,
        rssi=logical_packet.rssi,
        snr=logical_packet.snr,
    )
    db.add(observation)

    _set_route_hops(db, logical_packet.id, parse_result.packet.get("route"))

    db.commit()
    db.refresh(mqtt_message)
    return mqtt_message
