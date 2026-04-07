"""initial schema

Revision ID: 20260407_0001
Revises:
Create Date: 2026-04-07 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260407_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "nodes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("node_num", sa.BigInteger(), nullable=False),
        sa.Column("short_name", sa.String(length=64), nullable=True),
        sa.Column("long_name", sa.String(length=160), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_nodes_node_num", "nodes", ["node_num"], unique=False)

    op.create_table(
        "mqtt_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("topic", sa.String(length=512), nullable=False),
        sa.Column("qos", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("retain", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("connection_id", sa.String(length=128), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("payload_text", sa.Text(), nullable=True),
        sa.Column("parse_status", sa.String(length=32), nullable=False, server_default="unparsed"),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_mqtt_messages_topic", "mqtt_messages", ["topic"], unique=False)
    op.create_index("ix_mqtt_messages_created_at", "mqtt_messages", ["created_at"], unique=False)
    op.create_index("ix_mqtt_messages_connection_id", "mqtt_messages", ["connection_id"], unique=False)
    op.create_index("ix_mqtt_messages_session_id", "mqtt_messages", ["session_id"], unique=False)

    op.create_table(
        "logical_packets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("inner_packet_id", sa.String(length=128), nullable=True),
        sa.Column("channel", sa.String(length=128), nullable=True),
        sa.Column("from_node", sa.BigInteger(), nullable=True),
        sa.Column("hop_start", sa.Integer(), nullable=True),
        sa.Column("hops_away", sa.Integer(), nullable=True),
        sa.Column("sender", sa.BigInteger(), nullable=True),
        sa.Column("packet_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("to_node", sa.BigInteger(), nullable=True),
        sa.Column("packet_type", sa.String(length=64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("next_hop", sa.BigInteger(), nullable=True),
        sa.Column("relay_node", sa.BigInteger(), nullable=True),
        sa.Column("rssi", sa.Float(), nullable=True),
        sa.Column("snr", sa.Float(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_logical_packets_fingerprint", "logical_packets", ["fingerprint"], unique=False)
    op.create_index("ix_logical_packets_session_id", "logical_packets", ["session_id"], unique=False)
    op.create_index("ix_logical_packets_inner_packet_id", "logical_packets", ["inner_packet_id"], unique=False)
    op.create_index("ix_logical_packets_channel", "logical_packets", ["channel"], unique=False)
    op.create_index("ix_logical_packets_from_node", "logical_packets", ["from_node"], unique=False)
    op.create_index("ix_logical_packets_sender", "logical_packets", ["sender"], unique=False)
    op.create_index("ix_logical_packets_packet_timestamp", "logical_packets", ["packet_timestamp"], unique=False)
    op.create_index("ix_logical_packets_to_node", "logical_packets", ["to_node"], unique=False)
    op.create_index("ix_logical_packets_packet_type", "logical_packets", ["packet_type"], unique=False)
    op.create_index("ix_logical_packets_last_seen_at", "logical_packets", ["last_seen_at"], unique=False)

    op.create_table(
        "packet_observations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("logical_packet_id", sa.BigInteger(), sa.ForeignKey("logical_packets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mqtt_message_id", sa.BigInteger(), sa.ForeignKey("mqtt_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("topic", sa.String(length=512), nullable=False),
        sa.Column("connection_id", sa.String(length=128), nullable=True),
        sa.Column("hop_start", sa.Integer(), nullable=True),
        sa.Column("hops_away", sa.Integer(), nullable=True),
        sa.Column("next_hop", sa.BigInteger(), nullable=True),
        sa.Column("relay_node", sa.BigInteger(), nullable=True),
        sa.Column("rssi", sa.Float(), nullable=True),
        sa.Column("snr", sa.Float(), nullable=True),
        sa.UniqueConstraint("mqtt_message_id", name="uq_packet_observations_mqtt_message_id"),
    )
    op.create_index("ix_packet_observations_logical_packet_id", "packet_observations", ["logical_packet_id"], unique=False)
    op.create_index("ix_packet_observations_mqtt_message_id", "packet_observations", ["mqtt_message_id"], unique=False)
    op.create_index("ix_packet_observations_session_id", "packet_observations", ["session_id"], unique=False)
    op.create_index("ix_packet_observations_observed_at", "packet_observations", ["observed_at"], unique=False)

    op.create_table(
        "route_hops",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("logical_packet_id", sa.BigInteger(), sa.ForeignKey("logical_packets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hop_index", sa.Integer(), nullable=False),
        sa.Column("from_node_id", sa.BigInteger(), sa.ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("to_node_id", sa.BigInteger(), sa.ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("from_node_num", sa.BigInteger(), nullable=True),
        sa.Column("to_node_num", sa.BigInteger(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_route_hops_logical_packet_id", "route_hops", ["logical_packet_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_route_hops_logical_packet_id", table_name="route_hops")
    op.drop_table("route_hops")

    op.drop_index("ix_packet_observations_observed_at", table_name="packet_observations")
    op.drop_index("ix_packet_observations_session_id", table_name="packet_observations")
    op.drop_index("ix_packet_observations_mqtt_message_id", table_name="packet_observations")
    op.drop_index("ix_packet_observations_logical_packet_id", table_name="packet_observations")
    op.drop_table("packet_observations")

    op.drop_index("ix_logical_packets_last_seen_at", table_name="logical_packets")
    op.drop_index("ix_logical_packets_packet_type", table_name="logical_packets")
    op.drop_index("ix_logical_packets_to_node", table_name="logical_packets")
    op.drop_index("ix_logical_packets_packet_timestamp", table_name="logical_packets")
    op.drop_index("ix_logical_packets_sender", table_name="logical_packets")
    op.drop_index("ix_logical_packets_from_node", table_name="logical_packets")
    op.drop_index("ix_logical_packets_channel", table_name="logical_packets")
    op.drop_index("ix_logical_packets_inner_packet_id", table_name="logical_packets")
    op.drop_index("ix_logical_packets_session_id", table_name="logical_packets")
    op.drop_index("ix_logical_packets_fingerprint", table_name="logical_packets")
    op.drop_table("logical_packets")

    op.drop_index("ix_mqtt_messages_session_id", table_name="mqtt_messages")
    op.drop_index("ix_mqtt_messages_connection_id", table_name="mqtt_messages")
    op.drop_index("ix_mqtt_messages_created_at", table_name="mqtt_messages")
    op.drop_index("ix_mqtt_messages_topic", table_name="mqtt_messages")
    op.drop_table("mqtt_messages")

    op.drop_index("ix_nodes_node_num", table_name="nodes")
    op.drop_table("nodes")

    op.drop_table("sessions")
