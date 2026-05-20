"""add watchlist table

Revision ID: aa4e5764f5ed
Revises: 042ee49614ba
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "aa4e5764f5ed"
down_revision = "042ee49614ba"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "symbol",
            name="uq_watchlist_user_symbol"
        )
    )


def downgrade():
    op.drop_table("watchlist")
