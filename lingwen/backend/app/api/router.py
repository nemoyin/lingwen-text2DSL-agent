"""Unified API router — all sub-routers are registered here."""

from fastapi import APIRouter

from app.api import auth, query, datasources, schema, metadata, few_shot, skills, history, stats, csv_upload, history_ext, alerts, settings, rbac, benchmark, models, logs, rag, mcp

api_router = APIRouter()

# Auth
api_router.include_router(auth.router, prefix="/api/auth", tags=["认证"])

# Query (core Text2SQL endpoint)
api_router.include_router(query.router, prefix="/api", tags=["查询"])

# Data sources
api_router.include_router(datasources.router, prefix="/api/datasources", tags=["数据源"])

# Schema scan & browse
api_router.include_router(schema.router, prefix="/api/schema", tags=["Schema"])

# Metadata management
api_router.include_router(metadata.router, prefix="/api/metadata", tags=["元数据"])

# Few-shot examples
api_router.include_router(few_shot.router, prefix="/api/few-shot", tags=["Few-shot"])

# Skill templates
api_router.include_router(skills.router, prefix="/api/skills", tags=["Skill"])

# Query history
api_router.include_router(history.router, prefix="/api/query", tags=["历史"])

# Dashboard stats
api_router.include_router(stats.router, prefix="/api", tags=["统计"])

# CSV upload
api_router.include_router(csv_upload.router, prefix="/api/datasources", tags=["CSV上传"])

# History actions (delete, feedback)
api_router.include_router(history_ext.router, prefix="/api/query", tags=["历史操作"])

# Alerts & cases
api_router.include_router(alerts.router, prefix="/api/alerts", tags=["预警"])

# User settings
api_router.include_router(settings.router, prefix="/api/user", tags=["用户设置"])

# RBAC
api_router.include_router(rbac.router, prefix="/api", tags=["权限管理"])

# Benchmark
api_router.include_router(benchmark.router, prefix="/api/benchmark", tags=["测评"])

# Model management
api_router.include_router(models.router, prefix="/api", tags=["模型管理"])

# Log viewer
api_router.include_router(logs.router, prefix="/api", tags=["日志查看"])

# RAG management
api_router.include_router(rag.router, prefix="/api/rag", tags=["RAG管理"])

# MCP Server (SSE transport)
api_router.include_router(mcp.router, prefix="/api/mcp", tags=["MCP"])
