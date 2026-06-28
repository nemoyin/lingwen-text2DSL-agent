# 灵问（lingwen）智能问数引擎 — 系统架构设计文档

> **版本**: v1.1 | **日期**: 2026-06-28 | **作者**: Bob（架构师）
>
> **基于 PRD**: lingwen-prd.md v1.0

---

## 1. 架构概述

灵问采用五层架构设计，从用户交互到基础设施层逐层解耦：

```
用户交互层 (React + Vite + MUI)
  Chat UI  |  Admin Console  |  REST API
                    |
业务逻辑层
  对话上下文管理  |  元数据管理  |  Skill 管理  |  Few-shot 管理
                    |
核心能力层
  Agent 编排 (LangGraph)  |  RAG 检索  |  Text2SQL (DeepSeek)
                    |
安全层
  JWT 认证  |  SQL 注入检测  |  危险操作拦截  |  行数限制
                    |
基础设施层
  DeepSeek API  |  ChromaDB  |  MySQL (metadata)  |  Redis (optional)
```

---

## 2. Agent 管线（StateGraph）

8 个节点构成的 LangGraph StateGraph：

```
intent_rec → perm_check → rag_retrieve → sql_gen → sql_validate → sql_exec → result_wrap → final
                                                   ↑                          │
                                                   │   (重试 ≤2次)  ←─── retry │
                                                   │                          │
                                                   └── (危险SQL跳过重试) ──────┘
```

### 2.1 各节点职责

| 节点 | 职责 | 输入 | 输出 |
|------|------|------|------|
| intent_rec | LLM 意图识别 + 匹配 Skill | question | intent |
| perm_check | 数据源权限 + 状态校验 | datasource_id, user_id | status |
| rag_retrieve | 并行检索：Schema (top-k=5) + Few-shot (top-k=3) | question, datasource_id | retrieved_schemas, retrieved_examples |
| sql_gen | CoT 推理 → SQL/ES|QL 生成 + 方言提示注入 | question + RAG context + dialect_hint | cot_reasoning, generated_sql |
| sql_validate | 安全检查 + LIMIT 1000 注入 | generated_sql | executed_sql (or error_info) |
| sql_exec | 执行查询（async 引擎 / native 客户端） | executed_sql, datasource_id | execution_result |
| result_wrap | LLM 数据解读 + 图表推荐 + 追问建议 | execution_result, question | ai_analysis, chart_suggestion |
| final | 组装响应 | all state | final_result |

### 2.2 条件路由

- `perm_check` → auth_failed: 直接 result_wrap（不浪费 LLM token）
- `sql_validate` → 危险 SQL: 直接 result_wrap（不触发重试）
- `sql_exec` → failed + retry < 2: 回 sql_gen 重试（带 error_info）
- `sql_exec` → failed + retry ≥ 2: result_wrap（返回 CoT 推理过程）

---

## 3. 数据模型

### 3.1 ORM 实体

| 模型 | 表名 | 关键字段 |
|------|------|---------|
| User | users | id, username, password_hash, role, is_active |
| DataSource | datasources | id, name, db_type, host, port, database, username, password_encrypted, extra_params, status |
| TableMetadata | tables_metadata | id, datasource_id, table_name, display_name, business_description |
| ColumnMetadata | columns_metadata | id, table_id, column_name, display_name, data_type, business_description, is_primary_key |
| FewShotExample | few_shot_examples | id, datasource_id, question, sql, description, tags |
| SkillTemplate | skill_templates | id, name, description, prompt_template, rag_config, is_active |
| QueryHistory | query_history | id, user_id, datasource_id, question, generated_sql, executed_sql, result_json, latency_ms, feedback |

### 3.2 AgentState

| 字段 | 类型 | 说明 |
|------|------|------|
| question | str | 用户自然语言问题 |
| datasource_id | int | 目标数据源 ID |
| user_id | int | 请求用户 ID |
| intent | dict | 意图识别结果 |
| retrieved_schemas | list[dict] | RAG 检索到的表结构 |
| retrieved_examples | list[dict] | RAG 检索到的 Few-shot 示例 |
| cot_reasoning | str | CoT 推理过程 |
| generated_sql | str | LLM 生成的 SQL/ES|QL |
| executed_sql | str | 经校验 + LIMIT 注入后的安全 SQL |
| execution_result | list[dict] | 查询执行结果行 |
| ai_analysis | str | AI 自然语言分析 |
| chart_suggestion | dict | 图表类型 + 标题建议 |
| error_info | str | 错误信息 |
| retry_count | int | 当前重试次数 |
| status | str | 管线状态 init/auth_failed/failed/success |
| history | list[dict] | 多轮对话上下文 |

---

## 4. API 设计

### 4.1 统一响应格式

```json
{"code": 200, "data": {...}, "message": "success"}
```

### 4.2 端点清单

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/health | GET | 健康检查 |
| /api/auth/login | POST | 登录获取 JWT |
| /api/query | POST | 同步查询 |
| /api/query/stream | POST | SSE 流式查询 |
| /api/query/history | GET | 查询历史（分页） |
| /api/query/{id} | DELETE | 删除历史记录 |
| /api/query/{id}/feedback | POST | 查询反馈（赞/踩） |
| /api/datasources | GET/POST | 数据源列表/创建 |
| /api/datasources/types | GET | 支持的数据库类型 |
| /api/datasources/{id} | GET/PUT/DELETE | 单源 CRUD |
| /api/datasources/{id}/test | POST | 连接测试 |
| /api/datasources/upload-csv | POST | CSV 上传 |
| /api/schema/scan | POST | Schema 扫描 |
| /api/metadata/tables | GET/PUT | 表元数据 |
| /api/metadata/columns | GET/PUT | 字段元数据 |
| /api/few-shot | GET/POST | Few-shot CRUD |
| /api/skills | GET/POST | Skill CRUD |
| /api/models | GET/POST | LLM 模型管理 |
| /api/models/{id}/set-default | POST | 切换默认模型 |
| /api/benchmark/sets | GET/POST | 测试集管理 |
| /api/benchmark/runs | GET/POST | 测评任务 |
| /api/benchmark/runs/{id}/execute | POST | 执行测评 |
| /api/benchmark/runs/{id} | GET | 测评详情 |
| /api/stats | GET | 仪表盘统计 |
| /api/stats/trends | GET | 查询趋势 |
| /api/alerts | GET/POST | 预警管理 |
| /api/alerts/{id}/escalate | POST | 升级为案件 |
| /api/alerts/cases | GET | 案件列表 |
| /api/roles + /api/permissions | GET/POST | RBAC |
| /api/user/settings | GET/PUT | 个人设置 |
| /api/logs | GET | 在线日志 |
| /api/rag/reindex | POST | RAG 重建索引 |
| /api/rag/status | GET | RAG 状态 |

---

## 5. 安全设计

### 5.1 SqlGuard

| 检查项 | 实现 |
|--------|------|
| 危险操作拦截 | DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE, GRANT, REVOKE, REPLACE, RENAME |
| SQL 注入检测 | `--` 注入、`;` 多语句、`UNION SELECT`、`SLEEP()`、`BENCHMARK()`、`OR 1=1` |
| 行数限制 | 强制 `LIMIT 1000`，超过时标记 `is_truncated: true` |

### 5.2 认证

- JWT (HS256)，默认 480 分钟过期
- 密码 bcrypt 哈希存储
- 数据源密码 AES-256-CBC 加密存储

---

## 6. 多数据源适配器架构

```
app/adapters/
  __init__.py          # 注册中心: @register_adapter + get_adapter() + available_types()
  base.py              # 抽象基类: ConnectionParams, SchemaColumn, SchemaTable
  mysql_adapter.py     # MySQL (aiomysql, async)
  postgresql_adapter.py# PostgreSQL (asyncpg, async)
  doris_adapter.py     # Apache Doris (aiomysql, MySQL协议兼容, async)
  clickhouse_adapter.py# ClickHouse (clickhouse-connect, sync→to_thread)
  oracle_adapter.py    # Oracle (oracledb, async)
  hive_adapter.py      # Apache Hive (pyhive, sync→to_thread)
  elasticsearch_adapter.py # ES 8.x (elasticsearch-py, ES|QL)
  dm_adapter.py        # 达梦 DM8 (dmPython, sync→to_thread)
```

### 6.1 执行路径分支

```
datasource_service.execute_query()
  ├─ uses_sqlalchemy() == False (ES, Hive, DM)
  │    └─ adapter.execute_query(params, sql)  # 原生客户端
  ├─ uses_sqlalchemy() == True + async driver (MySQL, PG, Doris)
  │    └─ create_async_engine → engine.connect()
  └─ uses_sqlalchemy() == True + sync driver (ClickHouse)
       └─ create_engine (sync) → asyncio.to_thread()
```

### 6.2 方言提示注入

`SQLGenerationNode` 查询 `datasources.db_type` → 获取适配器 → `get_dialect_hint()` → 注入 SystemMessage。

---

## 7. RAG 层

| 组件 | 说明 |
|------|------|
| EmbeddingClient | DeepSeek/Qwen3-Embedding API 封装 |
| VectorStore | ChromaDB 集合管理（schema + fewshot 两个 collection） |
| SchemaRetriever | Schema 语义搜索 top-k=5 |
| FewShotRetriever | Few-shot 语义搜索 top-k=3 |
| Indexer | 向量索引构建 + 全量重建 |

RAG 无结果时自动触发元数据回退：直接从 MySQL 查询 `tables_metadata` + `columns_metadata` 构建 schema 上下文。

---

## 8. 前端架构

### 8.1 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| /login | LoginPage | 登录 |
| /dashboard | DashboardPage | 仪表盘 |
| /chat | ChatPage | 核心对话 |
| /profile | ProfilePage | 个人设置 |
| /alerts/* | AlertPage / AlertListPage | 预警管理 |
| /cases/new | CasePage | 新建案件 |
| /admin/datasources | DatasourcePage | 数据源管理 |
| /admin/metadata | MetadataPage | 元数据管理 |
| /admin/skills | SkillPage | Skill 管理 |
| /admin/few-shot | FewShotPage | Few-shot 管理 |
| /admin/benchmark | BenchmarkPage | Agent 测评 |
| /admin/models | ModelManagement | 模型管理 |
| /admin/logs | LogViewer | 日志查看 |
| /admin/roles | RoleManagement | 角色管理 |
| /admin/users | UserManagement | 用户管理 |

### 8.2 核心 Hooks

| Hook | 说明 |
|------|------|
| useQuery | 查询发送 + 结果接收（同步/流式） |
| useChart | Chart.js 生命周期管理（create/update/destroy/type-switch） |
| useClipboard | 一键 TSV 复制 |
| useDatasources | 数据源列表管理 |

### 8.3 核心组件

| 组件 | 说明 |
|------|------|
| DataTable | 数据表格 + 截断提示 |
| ResultChart | 图表（bar/line/pie）+ 类型切换 + 全屏 |
| ExportButtons | CSV/Excel 导出 |
| VoiceInput + SpeakButton | 语音输入（STT）+ 语音播报（TTS） |

---

## 9. 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 后端框架 | FastAPI | 0.115+ |
| Agent 编排 | LangGraph | 0.2+ |
| LLM | DeepSeek API | deepseek-chat |
| Embeddings | Qwen3-Embedding-8B (Gitee AI) | - |
| 向量 DB | ChromaDB (embedded) | 0.5 |
| 元数据 DB | MySQL | 8.0 |
| 前端 | React + Vite + MUI + Tailwind CSS | 18.3 / 6.x / 6.x / 3.4 |
| 图表 | Chart.js 4.5 (native) | 4.5 |
| 导出 | xlsx + file-saver | 0.18 / 2.0 |
| 构建 | Poetry | 1.8+ |
| 部署 | Docker Compose | v2+ |

---

> **文档结束** — v1.1 更新于 2026-06-28，补充多数据源适配器、Agent 测评、流式推送、多模型管理等内容。
