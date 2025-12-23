"""add game_code to llm_runs

Revision ID: a1b2c3d4e5f6
Revises: fee3346a2bfe
Create Date: 2025-12-23 20:59:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "fee3346a2bfe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add game_code column to llm_runs table
    op.add_column("llm_runs", sa.Column("game_code", sa.String(length=64), nullable=True))


def downgrade() -> None:
    # Remove game_code column from llm_runs table
    op.drop_column("llm_runs", "game_code")
