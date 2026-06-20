# 灵问（Lingwen）— 智能问数引擎

> **基于 Agent + RAG 架构的自然语言转 SQL 引擎，让数据查询像提问一样简单。**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 项目简介

**灵问**是一款独立、可复用的通用智能问数引擎，能将用户的自然语言问题自动转化为准确的 SQL 查询并返回结果。产品最初为**天府一网监**（政府大数据监督系统）打造，但设计为通用引擎，可集成到任何需要自然语言数据查询能力的系统中。

相较于直接使用 DeepSeek API 进行 Text2SQL，灵问采用 **Agent + RAG（检索增强生成）五层架构**与 **8 步智能处理链路**，将 SQL 首次生成正确率提升至 **≥ 80%**，达到生产可用水平。

### 🎯 为什么选择灵问？

| 痛点 | 灵问的解决方案 |
|------|--------------|
| 通用大模型缺乏业务上下文 | RAG 注入 Schema 语义 + Few-shot 示例 |
| SQL 生成不够稳定 | CoT 思维链推理 + 自动重试 2 次 |
| 自然语言可能触发危险 SQL | 多重防线：LLM 层拦截 + 正则模式匹配 + 数据库只读账号 |
| RAG 冷启动效果差 | 支持种子数据导入 + 管理后台手动丰富元数据 |

---

## ✨ 核心功能

### P0 — 必须交付（已实现）
- 🗣️ **自然语言对话界面** — 输入问题，自动返回数据表格 + AI 分析 + 生成的 SQL
- 🔗 **MySQL 数据源管理** — 管理后台配置连接信息，支持连接测试
- 🔍 **自动 Schema 扫描** — 读取 `information_schema`，提取表名、字段、类型、注释、索引
- 📝 **元数据管理** — 编辑中文显示名、业务描述、枚举值映射、关联关系
- 🤖 **8 步 Agent 处理链路** — 意图识别 → 权限预校验 → RAG 并行检索 → CoT SQL 生成 → SQL 校验+安全注入 → 执行 → 结果包装 → 返回
- 🛡️ **SQL 安全防护** — 拦截 DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE；检测 SQL 注入特征；强制 `LIMIT 1000`
- 🔐 **JWT 认证** — 所有 API 需携带有效 Token
- 📊 **图表可视化** — 根据查询结果自动推荐 bar/line/pie 图表（Chart.js 原生渲染）

### P1 — 应该交付（已实现）
- ⭐ **Few-shot 示例管理** — 管理问题→SQL 示例对，持续优化特定场景准确率
- 🧩 **Skill 模板管理** — 预置"智能问数"Skill，包含可配置的 Prompt 模板与 RAG 参数
- 📋 **数据复制与导出** — 一键复制表格数据（TSV），一键导出 CSV / Excel（含 UTF-8 BOM）
- ⚡ **Redis 查询缓存** — 重复问题命中缓存，响应更快

### P2 — 规划中
- 📜 **查询历史与审计日志** — 全链路操作可追溯
- 👥 **RBAC 权限管理** — 用户角色管理，数据源级别访问控制
- 🔒 **行级权限注入** — 根据用户身份自动注入数据范围过滤条件
- 🗄️ **多数据源支持** — PostgreSQL、ClickHouse 等

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层                              │
│   对话界面 (React)  │  管理后台 (React)  │  REST API      │
├─────────────────────────────────────────────────────────┤
│                    业务功能层                              │
│   对话上下文管理  │  元数据管理  │  Skill 管理  │  Few-shot  │
├─────────────────────────────────────────────────────────┤
│                    核心能力层                              │
│   Agent 编排 (LangGraph)  │  RAG 检索  │  Text2SQL      │
├─────────────────────────────────────────────────────────┤
│                    安全控制层                              │
│   JWT 认证  │  SQL 注入拦截  │  危险操作拦截  │  行数限制   │
├─────────────────────────────────────────────────────────┤
│                    基础设施层                              │
│   DeepSeek API  │  ChromaDB  │  MySQL  │  Redis          │
└─────────────────────────────────────────────────────────┘
```

### 🔄 8 步 Agent 处理链路

```
用户提问
  → ① 意图识别（判断是否为"问数"场景，匹配 Skill）
  → ② 权限预校验（用户是否有该数据源访问权限）
  → ③ RAG 并行检索（Schema 检索 + Few-shot 示例检索）
  → ④ SQL 生成（CoT：先推理分析 → 再生成 SQL）
  → ⑤ SQL 校验 + 安全注入（语法检查 + 危险操作拦截 + LIMIT 注入）
  → ⑥ 执行（MySQL SELECT，数据库账号仅 SELECT 权限）
  → ⑦ 结果包装（表格数据 + AI 自然语言分析）
  → ⑧ 返回（含 SQL、数据、分析、图表建议）
```

### LangGraph 状态图

```
                    ┌──────────────┐
                    │  start_node  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  intent_rec  │ ① 意图识别 + Skill 匹配
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  perm_check  │ ② 权限预校验
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ rag_retrieve │ ③ 并行：Schema + Few-shot 检索
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   sql_gen    │ ④ CoT 推理 → 生成 SQL
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ sql_validate │ ⑤ 安全校验 + LIMIT 注入
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  sql_exec    │ ⑥ 执行 SQL
                    └──┬───────┬───┘
                       │       │
                 成功 ─┘       └── 失败 & retry < 2 → sql_gen
                       │
                    ┌──▼───────────┐
                    │ result_wrap  │ ⑦ 结果包装 + AI 分析
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   end_node   │ ⑧ 格式化返回
                    └──────────────┘
```

---

## 🛠️ 技术栈

| 层次 | 技术 | 用途 |
|------|------|------|
| **后端框架** | FastAPI 0.115+ | 异步 REST API、自动 OpenAPI 文档 |
| **Agent 编排** | LangGraph 0.2+ | StateGraph 构建 8 节点有状态 DAG，支持条件边与循环 |
| **大语言模型** | DeepSeek API (`deepseek-chat`) | 中文推理 + SQL 生成 |
| **向量嵌入** | Qwen3-Embedding-8B（via Gitee AI） | Schema 与 Few-shot 向量化编码 |
| **向量数据库** | ChromaDB 0.5（嵌入模式） | 轻量零运维 RAG 存储，随 FastAPI 进程启动 |
| **元数据存储** | MySQL 8.0 + SQLAlchemy 2.0 | 结构化元数据（ORM 模型） |
| **缓存（P1）** | Redis 5.0 | 查询结果缓存 + Schema/权限热数据缓存 |
| **前端框架** | React 18.3 + Vite 6 + MUI 6 + Tailwind CSS 3.4 | 现代 SPA，企业级 UI 组件 |
| **图表渲染** | Chart.js 4.5（原生） | 自动推导 bar/line/pie 图表 |
| **包管理** | Poetry 1.8+（Python）/ npm（Node.js） | 依赖锁定与虚拟环境管理 |
| **容器化部署** | Docker Compose | 一键启动 MySQL + Backend + Nginx |

---

## 📁 项目结构

```
lingwen/
├── backend/                    # Python FastAPI 后端（约 55 个文件）
│   ├── app/
│   │   ├── agent/              # LangGraph 节点（8 步处理链路）
│   │   │   └── nodes/          # intent_recognition, permission_check,
│   │   │                       #   rag_retrieval, sql_generation,
│   │   │                       #   sql_validation, sql_execution,
│   │   │                       #   result_wrapping, final_response
│   │   ├── api/                # REST API 路由层
│   │   ├── models/             # SQLAlchemy ORM 模型（7 个实体）
│   │   ├── schemas/            # Pydantic v2 请求/响应 Schema
│   │   ├── services/           # 业务逻辑层（8 个服务）
│   │   ├── rag/                # RAG 子层：embeddings, vector_store, retriever, indexer
│   │   ├── security/           # sql_guard（SQL 防护）+ encrypt（密码加密）
│   │   ├── middleware/         # JWT 认证、CORS、请求日志
│   │   └── utils/              # CSV 导出、统一响应格式
│   ├── alembic/                # 数据库迁移脚本
│   ├── tests/                  # pytest 测试套件
│   └── pyproject.toml          # Poetry 依赖声明
├── frontend/                   # React + Vite 前端（约 58 个文件）
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/           # ChatContainer, DataTable, SqlBlock,
│   │   │   │                   #   ResultChart, ExportButtons, ChatInput...
│   │   │   ├── admin/          # DatasourceForm, MetadataPanel, SkillEditor...
│   │   │   └── common/         # LoadingSpinner, EmptyState, ErrorBoundary...
│   │   ├── pages/              # LoginPage, ChatPage, admin/* 页面
│   │   ├── services/           # Axios API 调用层（8 个 Service）
│   │   ├── hooks/              # useQuery, useChart, useDatasources, useClipboard
│   │   ├── contexts/           # AuthContext, AppContext
│   │   └── types/              # TypeScript 类型定义
│   └── package.json
├── docs/                       # PRD、架构设计文档、Mermaid 图表
├── UI/                         # 登录页视觉稿、图表导出系统设计
├── scripts/                    # 运维脚本（DB 检查、SQL 导出、验证等）
├── docker-compose.yml          # Docker 单机部署编排
├── init.sql                    # 数据库初始化 DDL + 种子数据
├── deploy-guide.md             # Docker 部署详细指南
├── .env.example                # 环境变量模板
├── .gitignore
├── README.md                   # English README
└── README_zh.md                # 本文件（中文 README）
```

---

## 🚀 快速开始

### 环境要求

| 组件 | 要求 |
|------|------|
| Docker + Docker Compose | v2+（Windows/Mac: Docker Desktop 4.x+） |
| CPU | 建议 4 核及以上 |
| 内存 | 建议 8 GB 及以上 |
| 磁盘 | 建议 50 GB 可用空间 |

### 5 分钟 Docker 部署

```bash
# 1. 进入项目目录
cd lingwen

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填写真实的 API Key：
#   - LINGWEN_LLM_API_KEY      （DeepSeek API Key，必填）
#   - LINGWEN_EMBED_API_KEY    （Gitee AI Embedding API Key，必填）
#   - MYSQL_ROOT_PASSWORD      （MySQL root 密码，选填，有默认值）

# 3. 启动所有服务
docker compose up -d

# 4. 查看服务状态（三个服务都应为 Up / healthy）
docker compose ps

# 5. 浏览器访问
# http://localhost:8080
# 默认管理员账号：admin / admin123
```

### 本地开发环境

**后端：**

```bash
cd lingwen/backend
pip install poetry && poetry install
cp .env.example .env  # 编辑数据库连接等配置
alembic upgrade head    # 执行数据库迁移
uvicorn app.main:app --reload --port 8000
# API 文档：http://localhost:8000/docs
```

**前端：**

```bash
cd lingwen/frontend
npm install
cp .env.example .env  # VITE_API_BASE_URL=http://localhost:8000
npm run dev
# 开发服务器：http://localhost:5173
```

---

## 📡 API 概览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录，返回 JWT Token |
| `/api/query` | POST | **核心接口**：自然语言问题 → 数据 + 分析 + SQL |
| `/api/datasources` | GET/POST | 数据源列表 / 创建 |
| `/api/datasources/{id}` | GET/PUT/DELETE | 单个数据源 CRUD |
| `/api/datasources/{id}/test` | POST | 测试数据源连接 |
| `/api/schema` | GET | 获取 Schema（支持 `?datasource_id=`） |
| `/api/schema/scan` | POST | 触发 Schema 扫描 |
| `/api/metadata/tables` | GET/PUT | 表元数据查询/更新 |
| `/api/metadata/columns` | GET/PUT | 字段元数据查询/更新 |
| `/api/few-shot` | GET/POST | Few-shot 示例列表/创建 |
| `/api/few-shot/{id}` | GET/PUT/DELETE | 单个示例 CRUD |
| `/api/skills` | GET/POST | Skill 模板列表/创建 |
| `/api/skills/{id}` | GET/PUT/DELETE | 单个 Skill CRUD |

完整交互式 API 文档：`http://localhost:8000/docs`（Swagger）、`http://localhost:8000/redoc`（ReDoc）。

### 统一响应格式

```json
{
  "code": 200,
  "data": { ... },
  "message": "success"
}
```

**错误码规范**：

| 范围 | 含义 |
|------|------|
| 200 | 成功 |
| 40001-40099 | 业务错误（数据源无效、Schema 不存在等） |
| 40100-40199 | 认证/授权错误 |
| 40200-40299 | SQL 安全错误（危险操作拦截、注入检测） |
| 40300-40399 | SQL 执行错误（语法错误、超时） |
| 50000-50099 | 系统内部错误 |

---

## 🖥️ 服务端口

| 服务 | 容器端口 | 宿主机端口 | 访问地址 |
|------|---------|-----------|---------|
| **前端 Nginx** | 80 | 8080 | http://localhost:8080 |
| **后端 API** | 8000 | 8001 | http://localhost:8001/docs |
| **MySQL** | 3306 | 3307 | `mysql -h 127.0.0.1 -P 3307` |

> 端口映射可在 `docker-compose.yml` 中自定义，避免与本地服务冲突。

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [产品 PRD](docs/lingwen-prd.md) | 完整产品需求文档：用户故事、功能需求池、UI 设计、API 设计 |
| [架构设计](docs/lingwen-architecture.md) | 系统架构设计：类图、时序图、任务分解、共享知识规范 |
| [部署指南](lingwen/deploy-guide.md) | Docker 部署、配置说明、常见问题排查 |
| [图表与导出设计](UI/system_design.md) | Chart.js 图表可视化 & CSV/Excel 导出详细设计 |
| [Mermaid 图表](docs/) | 类图、时序图、任务依赖图（.mermaid 文件） |

---

## 🗺️ 版本规划

- [x] **v0.1** — MVP：8 步 Agent 链路、MySQL 数据源、对话界面、管理后台、JWT 认证
- [x] **v0.2** — 图表可视化（Chart.js）、CSV/Excel 导出、Few-shot 管理、Skill 模板
- [ ] **v0.3** — Redis 缓存、查询历史、审计日志
- [ ] **v1.0** — RBAC 权限、行级权限注入、多数据源（PostgreSQL、ClickHouse）
- [ ] **v1.1** — 多轮对话、语义缓存、SSO 单点登录集成

---

## 🤝 贡献指南

本项目由天府一网监工程团队开发维护。如需参与贡献，请联系团队 Lead。

---

## 📄 开源许可

MIT License — 详见 [LICENSE](LICENSE) 文件。

---

## 💡 产品命名由来

> 「灵」取灵动、灵敏之意，寓意系统能灵巧地理解用户意图；
> 「问」即提问、查询，强调自然语言交互的便捷性。
> **灵问** — 让数据查询，灵机一动，有问必答。

---

<p align="center">
  <b>灵问（Lingwen）</b> — 让数据查询像提问一样简单。<br/>
  为天府一网监平台 ❤️ 打造。
</p>
