"""create scans table

Revision ID: 1c07e253125d
Revises:
Create Date: 2026-05-01 22:13:42

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c07e253125d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scans",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("user_token", sa.String(length=512), nullable=False),
        sa.Column("fruit_type", sa.String(length=50), nullable=False),
        sa.Column("maturity_label", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("bbox", sa.JSON(), nullable=False),
        sa.Column("recommendation", sa.String(length=255), nullable=False),
        sa.Column("color_code", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("scan_id"),
    )
    op.create_index(
        op.f("ix_scans_user_token"), "scans", ["user_token"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_scans_user_token"), table_name="scans")
    op.drop_table("scans")
