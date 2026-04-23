from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, SmallInteger, String, Text, func, text
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
    request_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    hops_away: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)


class BackendInstance(Base):
    __tablename__ = "backend_instances"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    backend_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    scheme: Mapped[str] = mapped_column(String(16), nullable=False, default="http")
    local_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    local_port: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=8000)
    public_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    public_port: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    nat_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(), index=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

class Node(Base):
    __tablename__ = "nodes"
    node_id: Mapped[hex] = mapped_column(String(128), primary_key=True, nullable=False, index=True)
    backend_id: Mapped[str] = mapped_column(String(128), ForeignKey("backend_instances.backend_id"), primary_key=True, nullable=False, index=True)
    last_byte: Mapped[hex] = mapped_column(String(2), nullable=False)