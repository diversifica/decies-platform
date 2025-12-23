"""Add games table and item source field

Revision ID: f7c3d55b6bf7
Revises: fee3346a2bfe
Create Date: 2025-12-23 23:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f7c3d55b6bf7"
down_revision = "fee3346a2bfe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    game_item_type = postgresql.ENUM(
        "multiple_choice",
        "true_false",
        "match",
        "cloze",
        name="game_item_type",
        create_type=False,
    )
    game_item_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "games",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("item_type", sa.Enum("multiple_choice", "true_false", "match", "cloze", name="game_item_type"), nullable=False),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default="V1"),
        sa.Column("engine_version", sa.String(length=32), nullable=False, server_default="V1"),
        sa.Column("source_hint", sa.String(length=128), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="games_code_key"),
    )

    op.add_column("items", sa.Column("source_game", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("items", "source_game")
    op.drop_table("games")

    game_item_type = postgresql.ENUM(
        "multiple_choice",
        "true_false",
        "match",
        "cloze",
        name="game_item_type",
    )
    game_item_type.drop(op.get_bind(), checkfirst=True)
