# =============================================================================
# 天府一网监 后端 Dockerfile
# 单阶段构建（简化版）：pip install + 运行时
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Copy dependency manifest
COPY pyproject.toml ./

# Install dependencies via pip (纯 Python 包，无需编译工具)
# cryptography / pymysql 提供二进制 wheel，无需 gcc
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] pydantic pydantic-settings \
    sqlalchemy pymysql aiomysql alembic \
    python-jose[cryptography] passlib[bcrypt] python-multipart \
    langchain langchain-deepseek langgraph langchain-community chromadb \
    httpx python-dotenv csvkit mcp \
    && rm -rf /root/.cache/pip

# Copy application source code
COPY . .

# Create required directories
RUN mkdir -p logs

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Use entrypoint script (runs migrations then starts uvicorn)
ENTRYPOINT ["./docker-entrypoint.sh"]
