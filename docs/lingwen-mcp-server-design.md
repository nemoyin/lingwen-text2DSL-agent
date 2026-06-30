# 灵问（Lingwen）MCP Server — 需求与设计方案

> **版本**: v1.0 | **日期**: 2026-06-29 | **作者**: Lingwen 架构组
>
> **背景**: [Lingwen vs SQLBot vs DB-GPT 对比分析](./lingwen-vs-sqlbot-vs-dbgpt.md) 指出 MCP 协议支持是 Lingwen 的核心能力缺口。

---

## 1. 需求概述

### 1.1 问题陈述

当前 Lingwen 是独立的 Web 应用，用户必须打开浏览器访问 `http://lingwen:8080` 才能使用。这导致：

| 痛点 | 描述 |
|------|------|
| **应用孤岛** | 无法嵌入 IDE（Claude Code / Cursor / Continue）、低代码平台（n8n / Dify / Coze）、或第三方系统 |
| **上下文切换** | 用户在 IDE 写代码时想查数据 → 切浏览器 → 打开 Lingwen → 提问 → 复制结果 → 切回 IDE |
| **能力不可编排** | 无法和其他 MCP 工具（文件系统、图表、邮件）串联组成自动化工作流 |
| **分发受限** | 100% 依赖独立部署 + 独立访问，无法通过生态分发获客 |

### 1.2 目标

**让任何支持 MCP 协议的 AI 平台（Claude Desktop、Claude Code、Cursor、n8n、Dify 等）都能直接调用 Lingwen 的自然语言查数能力。**

### 1.3 价值度量

| 指标 | 当前 | 目标 |
|------|------|------|
| 接入方式 | 1 种（Web 页面） | 3+ 种（Web + MCP + REST API） |
| 可嵌入平台 | 0 | 5+（Claude 系列、Cursor、n8n、Dify、MaxKB） |
| 跨工具编排能力 | 无 | 可与其他 MCP 工具串联 |
| 实现成本 | — | ≤ 1 人周（核心 300-500 行 Python） |

---

## 2. 用例分析

### 2.1 角色与场景

| 角色 | 场景 | 当前 | MCP 之后 |
|------|------|------|---------|
| **开发者** | 在 VS Code 写后端代码时，想查一下"本月各产品线的营收排行" | 切浏览器 → Lingwen → 复制粘贴 | 在 IDE Chat 中 `@lingwen 本月各产品线的营收排行` |
| **数据分析师** | 在 Claude Code 分析数据时，需要反复查数据库 | 手动查 Lingwen → 导出 CSV → Claude 分析 | Claude 直接调用 `lingwen_query` → 分析 → 画图 |
| **运维/自动化** | 在 n8n/Dify 工作流中需要查询数据作为决策节点 | 不支持 | 拖入 Lingwen MCP 节点 → 自然语言查询 → 结果流入下游 |
| **政务办案人员** | 在纪委监委办案系统中直接问"该单位近3年三公经费趋势" | 打开两个系统 | 在办案系统 Chat 中直接获得答案 |
| **产品经理** | 想快速验证一个数据问题，不想写 SQL | 找开发帮忙 | 在 Claude Desktop 中直接自然语言提问 |

### 2.2 典型交互流程

```
用户在 Claude Code 中输入:
"帮我查一下一网监数据库中，本月各类型预警的数量和分布情况"

→ Claude (MCP Client)
  → 调用 lingwen_list_datasources → 获取数据源列表 → 理解上下文
  → 调用 lingwen_get_schema("一网监生产库") → 了解表结构
  → 调用 lingwen_query("本月各类型预警的数量和分布", datasource_id=1)
    → Lingwen MCP Server
      → 8 步 Agent 管线 (意图识别→RAG→SQL生成→校验→执行)
      → 返回: { data: [...], analysis: "...", sql: "SELECT ..." }
  → Claude 解读结果，生成自然语言回答
```

---

## 3. 功能需求

### 3.1 MCP Tools（对外暴露的能力）

| 优先级 | Tool 名称 | 功能 | 输入参数 | 输出 |
|--------|-----------|------|----------|------|
| **P0** | `lingwen_query` | 自然语言查数（核心） | `question` (str), `datasource_id` (int, optional), `history` (list, optional) | `{data, analysis, sql, chart_suggestion, row_count}` |
| **P0** | `lingwen_list_datasources` | 列出可用数据源 | 无 | `[{id, name, db_type, status, table_count}]` |
| **P1** | `lingwen_get_schema` | 获取数据源 Schema | `datasource_id` (int), `table_name` (str, optional) | `{tables: [{name, display_name, description, columns: [...]}]}` |
| **P1** | `lingwen_execute_sql` | 执行安全 SQL（SELECT only） | `sql` (str), `datasource_id` (int) | `{columns, rows, row_count, is_truncated}` |
| **P2** | `lingwen_get_query_history` | 查询历史 | `limit` (int, default 10) | `[{id, question, sql, status, created_at}]` |

### 3.2 MCP Resources（被动暴露的数据）

| 优先级 | Resource URI | 内容 | 说明 |
|--------|-------------|------|------|
| **P0** | `lingwen://datasources` | JSON 数据源列表 | AI 启动时可读取以了解可用数据 |
| **P1** | `lingwen://datasources/{id}` | 单个数据源详情 | 含连接信息摘要（隐藏密码） |
| **P2** | `lingwen://schema/{datasource_id}` | Schema 快照 | 缓存的表结构视图 |

### 3.3 非功能需求

| 需求 | 规格 | 说明 |
|------|------|------|
| **认证** | API Key（JWT Token） | 复用 Lingwen 现有 JWT 认证，通过 MCP 初始化 params 传入 |
| **安全** | 继承 SqlGuard | 所有 SQL 自动经过 DROP/DELETE 拦截 + LIMIT 注入 |
| **权限** | 继承 RBAC | 数据源级别访问控制，只能查询有权限的数据源 |
| **流式** | SSE 协议 | `lingwen_query` 支持流式返回查询进度 + LLM 推理过程 |
| **超时** | 30s 默认 | 超过 30s 返回部分结果 + timeout 标记 |
| **并发** | 无状态设计 | 每个 MCP 请求独立处理，不依赖 session 粘滞 |
| **传输** | stdio + SSE 双模式 | stdio 用于本地 IDE，SSE 用于远程/Web 平台 |

---

## 4. 技术设计

### 4.1 总体架构

```
┌──────────────────────────────────────────────────────┐
│                    MCP Clients                        │
│  Claude Desktop  │  Claude Code  │  Cursor  │  Dify  │
└────────────┬─────────────────────────────────────────┘
             │  MCP Protocol (stdio / SSE)
             ▼
┌──────────────────────────────────────────────────────┐
│              Lingwen MCP Server (新增)                │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Tool Handler │  │ Resource     │  │ Auth      │  │
│  │ (6 tools)    │  │ Provider     │  │ Middleware│  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  │
│         │                 │                │        │
│         └────────┬────────┘                │        │
│                  ▼                         │        │
│  ┌──────────────────────────────┐          │        │
│  │     Service Adapter Layer    │◄─────────┘        │
│  │  (复用现有 service 层)        │                   │
│  └──────────────┬───────────────┘                   │
│                 │                                   │
└─────────────────┼───────────────────────────────────┘
                  │
┌─────────────────┼───────────────────────────────────┐
│  现有 Lingwen Backend                               │
│  ┌──────────────┼───────────────────────────────┐  │
│  │  Agent 管线  │  RAG 检索  │  数据源适配器     │  │
│  │  SqlGuard    │  RBAC     │  QueryService     │  │
│  └──────────────┴───────────┴───────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**设计原则**：MCP Server 是薄封装层，不包含业务逻辑。所有能力由现有 Service 层提供，MCP Server 只做协议适配。

### 4.2 代码结构

```
lingwen/backend/
├── app/
│   ├── mcp_server/                    # 新增：MCP Server 模块
│   │   ├── __init__.py
│   │   ├── server.py                  # MCP Server 主入口 + 注册
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── query.py               # lingwen_query tool
│   │   │   ├── datasources.py         # lingwen_list_datasources tool
│   │   │   ├── schema.py              # lingwen_get_schema tool
│   │   │   ├── execute.py             # lingwen_execute_sql tool
│   │   │   └── history.py             # lingwen_get_query_history tool
│   │   ├── resources/
│   │   │   ├── __init__.py
│   │   │   └── datasource_resource.py # lingwen:// 资源 URI
│   │   └── auth.py                    # JWT 验证中间件
│   ├── services/                      # 现有 service 层（复用）
│   │   ├── query_service.py
│   │   ├── datasource_service.py
│   │   └── ...
│   └── ...
├── mcp_entrypoint.py                  # 新增：stdio 模式入口
└── pyproject.toml                     # 新增 mcp 依赖
```

### 4.3 MCP Server 实现（核心代码骨架）

#### 4.3.1 依赖（pyproject.toml 新增）

```toml
[project]
dependencies = [
    # 新增
    "mcp>=1.0.0",
]
```

#### 4.3.2 Server 注册（server.py）

```python
"""Lingwen MCP Server — 将智能问数能力暴露为 MCP Tools"""
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationCapabilities
from mcp.server.stdio import stdio_server
from .tools.query import register_query_tool
from .tools.datasources import register_datasources_tool
from .tools.schema import register_schema_tool
from .tools.execute import register_execute_tool
from .auth import AuthMiddleware

def create_lingwen_mcp_server() -> Server:
    """创建并配置 Lingwen MCP Server"""
    server = Server("lingwen-mcp")

    # 注册所有 Tools
    register_query_tool(server)
    register_datasources_tool(server)
    register_schema_tool(server)
    register_execute_tool(server)

    return server
```

#### 4.3.3 核心 Tool：lingwen_query（query.py）

```python
"""lingwen_query — 自然语言查数（核心 MCP Tool）"""
from mcp.server import Server
from mcp.types import Tool, TextContent
from app.services.query_service import QueryService
from app.services.datasource_service import DatasourceService

def register_query_tool(server: Server):
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="lingwen_query",
                description="""使用自然语言查询数据库。输入中文问题，返回数据表格和AI分析。

示例:
- "本月各部门销售额排行"
- "近30天预警数量趋势"
- "三公经费实际支出与预算对比"

支持8种数据源：MySQL、PostgreSQL、ClickHouse、Oracle、Doris、Hive、ES、达梦DM8。
""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "自然语言数据查询问题"
                        },
                        "datasource_id": {
                            "type": "integer",
                            "description": "数据源ID（可选，不传则自动选择默认数据源）"
                        },
                        "history": {
                            "type": "array",
                            "description": "多轮对话历史 [{question, answer}, ...]（可选）"
                        }
                    },
                    "required": ["question"]
                }
            )
        ]
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name != "lingwen_query":
            return []

        query_service = QueryService()
        result = await query_service.execute_agent_query(
            question=arguments["question"],
            datasource_id=arguments.get("datasource_id"),
            history=arguments.get("history"),
            user_id=arguments.get("_auth_user_id"),  # 由 auth 中间件注入
        )

        # 格式化返回（纯文本 + JSON 双模式）
        output = f"""## 查询结果

**问题**: {arguments["question"]}
**生成SQL**: ```sql\n{result.get("sql", "")}\n```

### 数据 ({result.get("row_count", 0)} 行)

{_format_table(result.get("data", []))}

### AI 分析

{result.get("analysis", "")}
"""
        return [TextContent(type="text", text=output)]
```

#### 4.3.4 Auth 中间件（auth.py）

```python
"""MCP Auth Middleware — JWT Token 验证"""
import jwt
from functools import wraps

class LingwenAuth:
    def __init__(self, jwt_secret: str):
        self.jwt_secret = jwt_secret

    def authenticate(self, token: str) -> dict:
        """验证 JWT Token，返回用户信息"""
        payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        return {"user_id": payload["sub"], "role": payload.get("role", "user")}
```

### 4.4 传输模式

#### 模式 A：stdio（本地 IDE 场景）

```python
# mcp_entrypoint.py — stdio 入口
import asyncio
from mcp.server.stdio import stdio_server
from app.mcp_server.server import create_lingwen_mcp_server

async def main():
    server = create_lingwen_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options=...)

if __name__ == "__main__":
    asyncio.run(main())
```

**Claude Desktop 配置**：
```json
{
  "mcpServers": {
    "lingwen": {
      "command": "python",
      "args": ["-m", "lingwen.backend.mcp_entrypoint"],
      "env": {
        "LINGWEN_API_URL": "http://localhost:8001",
        "LINGWEN_JWT_TOKEN": "eyJ..."
      }
    }
  }
}
```

#### 模式 B：SSE（远程/Web 平台场景）

```python
# 在现有 FastAPI app 中挂载 MCP SSE 端点
from fastapi import FastAPI
from app.mcp_server.server import create_lingwen_mcp_server
from mcp.server.sse import SseServerTransport

app = FastAPI()

@app.get("/mcp/sse")
async def mcp_sse_endpoint():
    server = create_lingwen_mcp_server()
    transport = SseServerTransport("/mcp/messages/")
    # ... SSE 握手 + 消息路由
```

**Dify 配置**：
```yaml
mcp_server:
  url: https://lingwen.example.com/mcp/sse
  auth:
    type: bearer
    token: ${LINGWEN_JWT_TOKEN}
```

### 4.5 与现有系统的交互

```
MCP Tool 调用
  → Tool Handler (mcp_server/tools/*.py)
    → Service Layer (app/services/*.py) — 完全复用现有代码
      → Agent Pipeline (app/core/agent/)
        → RAG Retrieval (ChromaDB)
        → LLM Generation (DeepSeek API)
        → SqlGuard Validation
        → SQL Execution (adapters)
      → Result Formatting
    → MCP Response (TextContent)
```

**零侵入**：MCP Server 不修改任何现有 service/agent/adapter 代码。它只是在现有 REST API 之上加了一个 MCP 协议适配层。

### 4.6 安全设计

| 层 | 措施 |
|----|------|
| **认证** | JWT Token 通过 MCP `env` 或初始化参数传入，每次 Tool 调用前验证 |
| **鉴权** | 继承 Lingwen RBAC，`lingwen_query` 只返回用户有权限的数据源 |
| **SQL 安全** | 复用 SqlGuard（危险操作拦截 + LIMIT 1000 注入），MCP 层不做额外 SQL 处理 |
| **审计** | 所有 MCP Tool 调用记录到 `query_history`，标记 `source='mcp'` |
| **传输加密** | SSE 模式下走 HTTPS；stdio 模式走本地进程间通信 |

### 4.7 流式输出设计

`lingwen_query` 支持流式返回管线进度：

```
# 流式响应事件序列
event: step
data: {"step": "intent_rec", "status": "completed", "elapsed_ms": 5}

event: step  
data: {"step": "rag_retrieve", "status": "completed", "elapsed_ms": 45}

event: step
data: {"step": "sql_gen", "status": "running", "reasoning": "正在分析用户意图..."}

event: step
data: {"step": "sql_gen", "status": "completed", "sql": "SELECT ...", "elapsed_ms": 2239}

event: step
data: {"step": "sql_exec", "status": "completed", "row_count": 42, "elapsed_ms": 310}

event: done
data: {"data": [...], "analysis": "...", "chart_suggestion": {...}}
```

MCP Client（如 Claude）收到流式事件后可以实时展示进度，提升用户体验。

---

## 5. 实施计划

### 5.1 分阶段交付

| 阶段 | 内容 | 工时 | 产出 |
|------|------|------|------|
| **Phase 1 (MVP)** | stdio 模式 + 3 P0 Tools（query / list_datasources / get_schema）+ JWT 认证 | 3-5 天 | 可在 Claude Desktop/Code 中使用 |
| **Phase 2** | SSE 模式 + execute_sql Tool + Resources + 流式输出 | 2-3 天 | 可接入 Dify/n8n 等平台 |
| **Phase 3** | query_history Tool + 审计标记 + 文档 + 示例 | 1-2 天 | 生产可用 |

### 5.2 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| **新增** | `app/mcp_server/__init__.py` | 模块入口 |
| **新增** | `app/mcp_server/server.py` | Server 注册 |
| **新增** | `app/mcp_server/tools/query.py` | P0 核心 Tool |
| **新增** | `app/mcp_server/tools/datasources.py` | P0 数据源列表 Tool |
| **新增** | `app/mcp_server/tools/schema.py` | P1 Schema Tool |
| **新增** | `app/mcp_server/tools/execute.py` | P1 SQL 执行 Tool |
| **新增** | `app/mcp_server/tools/history.py` | P2 查询历史 Tool |
| **新增** | `app/mcp_server/resources/datasource_resource.py` | P1 Resource |
| **新增** | `app/mcp_server/auth.py` | JWT 验证 |
| **新增** | `mcp_entrypoint.py` | stdio 入口 |
| **修改** | `pyproject.toml` | 添加 `mcp` 依赖 |
| **修改** | `app/main.py` | 挂载 MCP SSE 端点（Phase 2） |

### 5.3 依赖清单

```
mcp>=1.0.0           # Anthropic 官方 MCP Python SDK
```

所有其他依赖（FastAPI、LangGraph、SQLAlchemy、ChromaDB 等）已存在，无需新增。

### 5.4 验证方式

| 验证项 | 方法 |
|--------|------|
| **单元测试** | 每个 Tool 独立测试，mock service 层 |
| **集成测试** | 启动 MCP Server → MCP Inspector 测试每个 Tool |
| **端到端** | Claude Desktop 配置 Lingwen MCP → 发起自然语言查询 → 验证返回结果 |
| **安全测试** | 无 Token 调用 → 应返回 401；危险 SQL → 应被 SqlGuard 拦截 |
| **回归测试** | 确保现有 REST API 不受影响（`pytest` 全部通过） |

---

## 6. 附录

### A. MCP Client 配置示例

#### Claude Desktop

```json
{
  "mcpServers": {
    "lingwen": {
      "command": "python",
      "args": ["/opt/lingwen/backend/mcp_entrypoint.py"],
      "env": {
        "LINGWEN_JWT_TOKEN": "eyJhbGciOiJIUzI1NiIs..."
      }
    }
  }
}
```

#### Claude Code

```json
{
  "mcpServers": {
    "lingwen": {
      "command": "python",
      "args": ["${workspaceFolder}/mcp_entrypoint.py"],
      "env": {
        "LINGWEN_JWT_TOKEN": "${LINGWEN_JWT_TOKEN}"
      }
    }
  }
}
```

#### Dify (通过 SSE)

```yaml
# dify.yml
mcp_servers:
  - name: lingwen
    transport: sse
    url: https://lingwen.example.com/mcp/sse
    headers:
      Authorization: "Bearer ${LINGWEN_JWT_TOKEN}"
```

### B. Tool 响应示例

#### lingwen_query 响应

```json
{
  "data": [
    {"部门": "市场部", "销售额(万)": 1250, "环比(%)": 12.3},
    {"部门": "销售部", "销售额(万)": 2100, "环比(%)": 5.7}
  ],
  "analysis": "本月销售部销售额最高，达2100万元。市场部环比增长最快(12.3%)。",
  "sql": "SELECT department AS 部门, SUM(amount)/10000 AS '销售额(万)', ...",
  "row_count": 8,
  "chart_suggestion": {
    "type": "bar",
    "title": "各部门销售额对比",
    "x_field": "部门",
    "y_field": "销售额(万)"
  },
  "is_truncated": false,
  "elapsed_ms": 3124
}
```

### C. 参考资料

- [MCP 协议规范](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Lingwen PRD](./lingwen-prd.md)
- [Lingwen 系统架构](./lingwen-architecture.md)
- [Lingwen vs SQLBot vs DB-GPT 对比分析](./lingwen-vs-sqlbot-vs-dbgpt.md)
