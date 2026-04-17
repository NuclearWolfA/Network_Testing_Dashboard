import base64
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import MqttMessage


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
        parse_status="stored",
    )
    db.add(mqtt_message)
    db.flush()

    db.commit()
    db.refresh(mqtt_message)
    return mqtt_message
