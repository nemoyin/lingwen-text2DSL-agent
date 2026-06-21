"""add extra_params JSON column to datasources

Revision ID: 002
Revises: 001
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "datasources",
        sa.Column(
            "extra_params",
            sa.JSON(),
            nullable=True,
            comment="Type-specific connection parameters (schema, service_name, auth_type, etc.)",
        ),
    )
    # Set existing rows to empty dict
    op.execute("UPDATE datasources SET extra_params = '{}' WHERE extra_params IS NULL")


def downgrade() -> None:
    op.drop_column("datasources", "extra_params")
