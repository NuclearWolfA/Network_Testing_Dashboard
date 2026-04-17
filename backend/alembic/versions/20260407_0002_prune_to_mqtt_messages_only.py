"""prune to mqtt messages only

Revision ID: 20260407_0002
Revises: 20260407_0001
Create Date: 2026-04-07 00:00:00
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260407_0002"
down_revision = "20260407_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("mqtt_messages_session_id_fkey", "mqtt_messages", type_="foreignkey")
    op.drop_index("ix_mqtt_messages_session_id", table_name="mqtt_messages")
    op.drop_column("mqtt_messages", "session_id")

    op.drop_table("route_hops")
    op.drop_table("packet_observations")
    op.drop_table("logical_packets")
    op.drop_table("nodes")
    op.drop_table("sessions")


def downgrade() -> None:
    raise RuntimeError("Downgrade not supported for the pruned schema")
