"""add user model and transaction user fields

Revision ID: 042ee49614ba
Revises: 5d346241bf15
Create Date: 2026-05-19 12:26:04.969483
"""

from alembic import op
import sqlalchemy as sa


revision = "042ee49614ba"
down_revision = "5d346241bf15"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username")
    )

    # These columns are required by the current Transaction model.
    # They are added here so a fresh database can be migrated from scratch.
    with op.batch_alter_table("transaction") as batch_op:
        batch_op.add_column(sa.Column("external_source", sa.String(length=50)))
        batch_op.add_column(sa.Column("external_id", sa.String(length=100)))
        batch_op.add_column(sa.Column("user_id", sa.Integer()))


def downgrade():
    with op.batch_alter_table("transaction") as batch_op:
        batch_op.drop_column("user_id")
        batch_op.drop_column("external_id")
        batch_op.drop_column("external_source")

    op.drop_table("user")
