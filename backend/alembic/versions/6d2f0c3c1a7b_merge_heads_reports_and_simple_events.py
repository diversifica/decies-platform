"""Merge heads: reports and simple learning events

Revision ID: 6d2f0c3c1a7b
Revises: 4374b8842427, 9c1c0d8a2f0d
Create Date: 2025-12-17 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "6d2f0c3c1a7b"
down_revision: tuple[str, str] | None = ("4374b8842427", "9c1c0d8a2f0d")
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
