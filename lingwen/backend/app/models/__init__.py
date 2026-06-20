"""ORM models — all models are imported here for Alembic autogenerate."""

from app.models.user import User
from app.models.datasource import DataSource
from app.models.table_metadata import TableMetadata
from app.models.column_metadata import ColumnMetadata
from app.models.few_shot import FewShotExample
from app.models.skill import SkillTemplate
from app.models.query_history import QueryHistory

__all__ = [
    "User",
    "DataSource",
    "TableMetadata",
    "ColumnMetadata",
    "FewShotExample",
    "SkillTemplate",
    "QueryHistory",
]
