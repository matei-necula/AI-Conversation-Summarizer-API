"""initial conversations table

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("rawTranscript", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("sentimentLabel", sa.String(length=16), nullable=False),
        sa.Column("sentimentScore", sa.Float(), nullable=False),
        sa.Column("keyTopics", postgresql.JSONB(), nullable=False),
        sa.Column(
            "createdAt",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_conversations_createdAt",
        "conversations",
        [sa.text('"createdAt" DESC')],
    )


def downgrade() -> None:
    op.drop_index("ix_conversations_createdAt", table_name="conversations")
    op.drop_table("conversations")
