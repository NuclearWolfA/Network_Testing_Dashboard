from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, SmallInteger, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MqttMessage(Base):
    __tablename__ = "mqtt_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    qos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    retain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    connection_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="stored")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[hex] = mapped_column(String(128), nullable=False, index=True)
    destination: Mapped[hex] = mapped_column(String(128), nullable=False, index=True)
    reporter: Mapped[hex] = mapped_column(String(128), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False
                                                  , server_default=func.now(), index=True)
    sequence_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[bytes] = mapped_column(Text, nullable=True)
    next_hop: Mapped[Optional[hex]] = mapped_column(String(128), nullable=True, index=True)
    relay_node: Mapped[Optional[hex]] = mapped_column(String(128), nullable=True, index=True)
    portnum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    message_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)