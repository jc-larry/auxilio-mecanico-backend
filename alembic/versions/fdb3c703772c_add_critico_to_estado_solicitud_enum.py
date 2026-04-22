"""add CRITICO to estado_solicitud enum

Revision ID: fdb3c703772c
Revises: 726fc2dc52f3
Create Date: 2026-04-21 14:02:25.676862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fdb3c703772c'
down_revision: Union[str, None] = '726fc2dc52f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot be executed within a transaction block in many PostgreSQL versions
    op.execute("COMMIT")
    op.execute("ALTER TYPE estado_solicitud ADD VALUE 'CRITICO'")


def downgrade() -> None:
    # Note: Removing a value from an enum is not directly supported in PostgreSQL without recreating the type.
    pass
