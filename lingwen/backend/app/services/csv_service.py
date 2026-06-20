"""CSV service — create temp tables, insert data, register metadata."""
import logging
import hashlib
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.csv_parser import COLUMN_TYPE_MAP
from app.config import settings

logger = logging.getLogger(__name__)
TEMP_DB = "lingwen_temp"
TEMP_USER = "root"
TEMP_PASS = "andy_l007"
TEMP_HOST = settings.db_host  # 从环境变量读取，Docker 中指向 mysql 服务
TEMP_PORT = 3306
BATCH_SIZE = 1000


def _generate_table_name(datasource_id: int) -> str:
    ts = hex(int(time.time() * 1000))[2:]
    h = hashlib.md5(str(datasource_id).encode()).hexdigest()[:6]
    return f"csv_{datasource_id}_{ts}_{h}"


async def create_table_and_import(
    sheet: dict[str, Any],
    datasource_id: int,
) -> str:
    """Create a temp MySQL table and insert all rows.

    Args:
        sheet: Parsed sheet with headers, rows, types.
        datasource_id: The registered datasource ID.

    Returns:
        The generated table name.
    """
    import aiomysql

    table_name = _generate_table_name(datasource_id)
    headers = sheet["headers"]
    types = sheet["types"]
    rows = sheet["rows"]

    conn = await aiomysql.connect(
        host=TEMP_HOST, port=TEMP_PORT,
        user=TEMP_USER, password=TEMP_PASS,
        db=TEMP_DB, autocommit=True,
    )
    cur = await conn.cursor()

    try:
        # DROP if exists
        await cur.execute(f"DROP TABLE IF EXISTS `{table_name}`")

        # CREATE TABLE
        col_defs = []
        for i, h in enumerate(headers):
            mysql_type = COLUMN_TYPE_MAP.get(types[i], "TEXT")
            col_defs.append(f"`{h['name']}` {mysql_type}")
        ddl = f"CREATE TABLE `{table_name}` ({', '.join(col_defs)}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        await cur.execute(ddl)

        # INSERT in batches
        placeholders = ", ".join(["%s"] * len(headers))
        insert_sql = f"INSERT INTO `{table_name}` VALUES ({placeholders})"
        batch = []
        for row in rows:
            values = []
            for j, h in enumerate(headers):
                val = row[j].strip().strip('"').strip("'") if j < len(row) else ""
                if types[j] == "integer" and val:
                    val = int(float(val.replace(",", "")))
                elif types[j] == "decimal(18,2)" and val:
                    val = float(val.replace(",", ""))
                elif types[j] == "date" and val:
                    val = val.replace("/", "-")
                values.append(val if val != "" else None)
            batch.append(values)
            if len(batch) >= BATCH_SIZE:
                await cur.executemany(insert_sql, batch)
                batch = []
        if batch:
            await cur.executemany(insert_sql, batch)

        row_count = await cur.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        row_count = (await cur.fetchone())[0]
        logger.info("Table %s created with %d rows", table_name, row_count)

    finally:
        await cur.close()
        conn.close()

    return table_name


async def register_metadata(
    db: AsyncSession,
    datasource_id: int,
    table_name: str,
    sheet: dict[str, Any],
    row_count: int,
) -> dict:
    """Register datasource, table_metadata, and columns_metadata for a CSV import.

    Returns:
        dict with datasource_id, table_name, columns, row_count
    """
    from app.services.datasource_service import register_csv_datasource
    from sqlalchemy import select
    from app.models.table_metadata import TableMetadata
    from app.models.column_metadata import ColumnMetadata

    sheet_name = sheet["name"]
    headers = sheet["headers"]
    types = sheet["types"]

    # 1. Register datasource (already done by caller, but ensure status)
    # 2. Create table metadata
    tmeta = TableMetadata(
        datasource_id=datasource_id,
        table_name=table_name,
        display_name=sheet_name,
        business_description=f"CSV 导入: {sheet_name} ({row_count} 行)",
    )
    db.add(tmeta)
    await db.flush()

    # 3. Create column metadata
    columns_out = []
    for i, h in enumerate(headers):
        cmeta = ColumnMetadata(
            table_id=tmeta.id,
            column_name=h["name"],
            display_name=h["display_name"],
            data_type=types[i],
            business_description=h.get("extra_desc", ""),
            is_primary_key=1 if i == 0 else 0,
        )
        db.add(cmeta)
        columns_out.append({
            "column_name": h["name"],
            "display_name": h["display_name"],
            "data_type": types[i],
        })

    await db.commit()
    logger.info("Metadata registered: table_id=%d, %d columns", tmeta.id, len(columns_out))

    return {
        "table_name": table_name,
        "columns": columns_out,
        "row_count": row_count,
    }
