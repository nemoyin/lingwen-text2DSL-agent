#!/bin/bash
# =============================================================================
# 天府一网监 后端 Docker 入口脚本
# 1. 运行数据库迁移（Alembic）
# 2. 启动 Uvicorn 服务
# =============================================================================

set -e

echo "=== 天府一网监 后端启动 ==="

# 确保 /app 在 Python 路径中（Alembic 需要导入 app 模块）
export PYTHONPATH="/app:${PYTHONPATH:-}"

# 从环境变量构造数据库连接 URL（覆盖 alembic.ini 中的硬编码）
DB_USER="${LINGWEN_DB_USER:-root}"
DB_PASS="${LINGWEN_DB_PASSWORD:-andy_l007}"
DB_HOST="${LINGWEN_DB_HOST:-mysql}"
DB_PORT="${LINGWEN_DB_PORT:-3306}"
DB_NAME="${LINGWEN_DB_NAME:-lingwen_metadata}"
ALEMBIC_URL="mysql+aiomysql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# 运行时替换 alembic.ini 中的数据库连接 URL
sed -i "s|^sqlalchemy.url = .*|sqlalchemy.url = ${ALEMBIC_URL}|" /app/alembic.ini

# 运行数据库迁移（若 init.sql 已建表则自动跳过）
echo "[1/2] 运行 Alembic 数据库迁移... (${DB_HOST}:${DB_PORT}/${DB_NAME})"
if alembic upgrade head 2>/tmp/alembic_err.log; then
    echo "  ✓ 数据库迁移完成"
else
    if grep -qi "already exists" /tmp/alembic_err.log; then
        echo "  ⚠ 表已存在（init.sql 已初始化），标记迁移版本..."
        alembic stamp head
        echo "  ✓ 迁移版本已标记"
    else
        echo "  ✗ 数据库迁移失败:"
        cat /tmp/alembic_err.log
        exit 1
    fi
fi

# 启动 Uvicorn
echo "[2/2] 启动 Uvicorn 服务..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
