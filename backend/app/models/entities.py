from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CaptureSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    node_num: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    long_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))


class MqttMessage(Base):
    __tablename__ = "mqtt_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    qos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    retain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    connection_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    payload_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unparsed")
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)


class LogicalPacket(Base):
    __tablename__ = "logical_packets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)

    inner_packet_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    channel: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    from_node: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    hop_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hops_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sender: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    packet_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    to_node: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    packet_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    next_hop: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    relay_node: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    rssi: Mapped[float | None] = mapped_column(Float, nullable=True)
    snr: Mapped[float | None] = mapped_column(Float, nullable=True)

    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    observations: Mapped[list["PacketObservation"]] = relationship(back_populates="logical_packet")
    route_hops: Mapped[list["RouteHop"]] = relationship(back_populates="logical_packet")


class PacketObservation(Base):
    __tablename__ = "packet_observations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    logical_packet_id: Mapped[int] = mapped_column(ForeignKey("logical_packets.id", ondelete="CASCADE"), nullable=False, index=True)
    mqtt_message_id: Mapped[int] = mapped_column(ForeignKey("mqtt_messages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)

    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    topic: Mapped[str] = mapped_column(String(512), nullable=False)
    connection_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hop_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hops_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    next_hop: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    relay_node: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    rssi: Mapped[float | None] = mapped_column(Float, nullable=True)
    snr: Mapped[float | None] = mapped_column(Float, nullable=True)

    logical_packet: Mapped["LogicalPacket"] = relationship(back_populates="observations")


class RouteHop(Base):
    __tablename__ = "route_hops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    logical_packet_id: Mapped[int] = mapped_column(ForeignKey("logical_packets.id", ondelete="CASCADE"), nullable=False, index=True)
    hop_index: Mapped[int] = mapped_column(Integer, nullable=False)

    from_node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True)
    to_node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True)
    from_node_num: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    to_node_num: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    logical_packet: Mapped["LogicalPacket"] = relationship(back_populates="route_hops")
