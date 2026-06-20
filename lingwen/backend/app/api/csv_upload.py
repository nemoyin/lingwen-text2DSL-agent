"""CSV upload endpoint — POST /api/datasources/upload-csv"""
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.services.csv_parser import read_csv
from app.services.csv_service import create_table_and_import, register_metadata
from app.services.datasource_service import register_csv_datasource
from app.utils.response import success

logger = logging.getLogger(__name__)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

router = APIRouter()


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    name: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    """Upload a CSV/XLSX file, create temp table, and register as data source."""
    # Validate extension
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 CSV 或 XLSX 文件")

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件超过 50MB 限制 (当前 {len(content) // 1024 // 1024}MB)")

    # Parse
    try:
        parsed = read_csv(content, filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(exc)}")

    if not parsed["sheets"]:
        raise HTTPException(status_code=400, detail="文件中未找到有效数据")

    # Use first sheet name as datasource name
    ds_name = name or filename.rsplit(".", 1)[0]
    if len(parsed["sheets"]) > 1:
        ds_name = f"{ds_name}_{parsed['sheets'][0]['name']}"

    # Register datasource first to get ID
    try:
        ds = await register_csv_datasource(db, ds_name, "")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"注册数据源失败: {str(exc)}")

    # Process each sheet (first sheet only for now — multi-sheet in future)
    sheet = parsed["sheets"][0]
    try:
        table_name = await create_table_and_import(sheet, ds.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"创建临时表失败: {str(exc)}")

    # Register metadata
    try:
        result = await register_metadata(db, ds.id, table_name, sheet, len(sheet["rows"]))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"注册元数据失败: {str(exc)}")

    logger.info("CSV uploaded: user=%s file=%s ds=%d rows=%d",
                user.get("username"), filename, ds.id, result["row_count"])

    # Auto-index schema into ChromaDB for RAG retrieval
    try:
        from app.rag.indexer import Indexer
        from app.api.deps import get_agent
        agent = await get_agent()
        indexer = Indexer(agent._embed_client, agent._vector_store)

        # Load the newly created table metadata
        from sqlalchemy import select
        from app.models import TableMetadata, ColumnMetadata
        from sqlalchemy.orm import selectinload

        tbl_stmt = (
            select(TableMetadata)
            .options(selectinload(TableMetadata.columns))
            .where(TableMetadata.datasource_id == ds.id)
        )
        tbl_result = await db.execute(tbl_stmt)
        tables = tbl_result.scalars().all()

        columns_by_table = {}
        for table in tables:
            columns_by_table[table.table_name] = table.columns

        schema_count = await indexer.index_schemas(ds.id, tables, columns_by_table)
        logger.info("[Pipeline|CSVUpload] Auto-indexed %d schemas for ds=%d", schema_count, ds.id)
    except Exception as exc:
        logger.warning("[Pipeline|CSVUpload] Schema auto-index failed (non-fatal): %s", exc)

    return success(data={
        "datasource_id": ds.id,
        "datasource_name": ds_name,
        **result,
        "sheets_count": len(parsed["sheets"]),
    })
