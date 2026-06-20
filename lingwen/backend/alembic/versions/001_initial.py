"""Initial database schema: 7 tables for the Lingwen metadata store.

Revision ID: 001
Revises: None
Create Date: 2026-05-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial set of tables."""
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    # 2. datasources
    op.create_table(
        "datasources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("db_type", sa.String(50), nullable=False, server_default="mysql"),
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default="3306"),
        sa.Column("database", sa.String(200), nullable=False),
        sa.Column("username", sa.String(200), nullable=False),
        sa.Column("password_encrypted", sa.String(512), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="inactive"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 3. tables_metadata
    op.create_table(
        "tables_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("datasource_id", sa.Integer(), nullable=False),
        sa.Column("table_name", sa.String(200), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("business_description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["datasource_id"], ["datasources.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tables_metadata_datasource_table",
        "tables_metadata",
        ["datasource_id", "table_name"],
    )

    # 4. columns_metadata
    op.create_table(
        "columns_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column("column_name", sa.String(200), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("data_type", sa.String(100), nullable=False),
        sa.Column("business_description", sa.Text(), nullable=True),
        sa.Column("enum_values", sa.JSON(), nullable=True),
        sa.Column("is_primary_key", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_foreign_key", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("foreign_ref", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["table_id"], ["tables_metadata.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_columns_metadata_table_column",
        "columns_metadata",
        ["table_id", "column_name"],
    )

    # 5. few_shot_examples
    op.create_table(
        "few_shot_examples",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("datasource_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("sql", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["datasource_id"], ["datasources.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. skill_templates
    op.create_table(
        "skill_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("rag_config", sa.JSON(), nullable=True),
        sa.Column("security_policy", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 7. query_history
    op.create_table(
        "query_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("datasource_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("generated_sql", sa.Text(), nullable=True),
        sa.Column("executed_sql", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["datasource_id"], ["datasources.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("query_history")
    op.drop_table("skill_templates")
    op.drop_table("few_shot_examples")
    op.drop_table("columns_metadata")
    op.drop_table("tables_metadata")
    op.drop_table("datasources")
    op.drop_table("users")
