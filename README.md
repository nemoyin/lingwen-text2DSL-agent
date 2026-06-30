# 灵问 (Lingwen) — Intelligent Query Engine

> **AI-powered natural language → SQL. Production-ready accuracy with Agent + RAG.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 Overview

**Lingwen** (灵问, "Smart Inquiry") is a standalone, reusable **intelligent query engine** that translates natural language questions into accurate SQL queries. It was originally built to power the **Tianfu Yiwangjian** (天府一网监) government big-data supervision platform, and is designed to be integrated into any system that needs natural language data access.

Unlike naive Text2SQL approaches, Lingwen uses an **Agent + RAG (Retrieval-Augmented Generation)** five-layer architecture with an **8-step processing pipeline**, achieving **≥ 80% first-shot SQL accuracy** in production environments.

### 🎯 Why Lingwen?

| Problem                                    | Lingwen's Solution                                                  |
| ------------------------------------------ | ------------------------------------------------------------------- |
| Generic LLMs lack business context         | RAG injects schema semantics + few-shot examples                    |
| SQL generation is brittle                  | Chain-of-Thought (CoT) reasoning + 2 automatic retries              |
| Natural language can trigger dangerous SQL | Multi-layer defense: LLM guard + regex patterns + DB read-only user |
| Cold-start RAG has poor recall             | Seed data import + manual metadata enrichment UI                    |

---

## ✨ Key Features

### P0 — Core (MVP)

- 🗣️ **Natural Language Chat Interface** — Ask questions, get data tables + AI analysis + generated SQL
- 🔗 **MySQL Datasource Management** — Configure and test connections from an admin console
- 🔍 **Auto Schema Scanning** — Reads `information_schema` to extract tables, columns, types, and comments
- 📝 **Metadata Enrichment** — Edit Chinese display names, business descriptions, and enum value mappings
- 🤖 **8-Step Agent Pipeline** — Intent recognition → Permission check → RAG retrieval → CoT SQL generation → Validation → Execution → Result wrapping → Response
- 🛡️ **SQL Safety** — Blocks DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE; detects SQL injection; enforces `LIMIT 1000`
- 🔐 **JWT Authentication** — Token-based auth for all API endpoints
- 📊 **Chart Visualization** — Auto-suggests bar/line/pie charts based on query results (Chart.js)

### P1 — Should Have

- ⭐ **Few-shot Example Management** — CRUD question→SQL pairs to continuously improve accuracy
- 🧩 **Skill Templates** — Pre-built "Smart Inquiry" skill with configurable prompts and RAG settings
- 📋 **Copy & Export** — One-click clipboard copy (TSV) and CSV/Excel export with UTF-8 BOM
- ⚡ **Redis Caching** — Query result cache for repeated questions

### P2 — Planned

- 📜 **Query History & Audit Logs** — Full operation traceability
- 👥 **RBAC** — Role-based data source access control
- 🔒 **Row-level Security** — Auto-inject data scope filters per user identity
- 🗄️ **Multi-Datasource** — PostgreSQL, ClickHouse, and more

### 🆕 MCP Server (v0.3)

- 🔌 **MCP Protocol Support** — Expose NL2SQL as MCP tools for any AI platform
- 🛠️ **Two Tools** — `lingwen_query` (natural language → data) + `lingwen_list_datasources` (discovery)
- 📡 **Dual Transport** — stdio for local IDEs (Claude Desktop/Code, Cursor) + SSE for remote platforms (Dify, n8n)
- 🔐 **JWT Auth** — Reuses existing authentication, zero additional setup
- 🪶 **Zero-Invasion** — Thin wrapper over existing service layer, ~500 lines of code

---

## 🔌 MCP Server

Lingwen exposes its NL2SQL capabilities as [MCP (Model Context Protocol)](https://spec.modelcontextprotocol.io/) tools, enabling any MCP-compatible AI platform to query your databases in natural language.

### Available Tools

| Tool | Description |
|------|-------------|
| `lingwen_query` | Natural language → data table + AI analysis + SQL |
| `lingwen_list_datasources` | List all available data sources |

### Quick Config

**Claude Desktop / Claude Code / WorkBuddy:**

```json
{
  "mcpServers": {
    "lingwen": {
      "command": "docker",
      "args": ["exec", "-i", "-e", "LINGWEN_JWT_TOKEN=<your-token>", "tianfu-backend", "python", "mcp_entrypoint.py"]
    }
  }
}
```

**Dify / n8n (SSE):**

```yaml
url: http://your-server:8001/api/mcp/sse
headers:
  Authorization: Bearer <your-token>
```

> 📖 Full MCP setup guide: [lingwen-mcp-server-design.md](docs/lingwen-mcp-server-design.md)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  User Interaction Layer                   │
│   Chat UI (React)  │  Admin Console (React)  │  REST API │
├─────────────────────────────────────────────────────────┤
│                   Business Logic Layer                    │
│   Dialog Context  │  Metadata Mgmt  │  Skills  │  Few-shot │
├─────────────────────────────────────────────────────────┤
│                     Core Capability Layer                 │
│   Agent Orchestration (LangGraph)  │  RAG  │  Text2SQL   │
├─────────────────────────────────────────────────────────┤
│                     Security Layer                       │
│   JWT Auth  │  SQL Injection Guard  │  Row Limits         │
├─────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                   │
│   DeepSeek API  │  ChromaDB  │  MySQL  │  Redis          │
└─────────────────────────────────────────────────────────┘
```

### 🔄 The 8-Step Agent Pipeline

```
User Question
  → ① Intent Recognition (classify query type, match skill)
  → ② Permission Pre-check (user authorized for this datasource?)
  → ③ RAG Parallel Retrieval (Schema search + Few-shot search)
  → ④ SQL Generation (Chain-of-Thought: reason first → then write SQL)
  → ⑤ SQL Validation + Safety Injection (syntax check + guard + LIMIT)
  → ⑥ Execution (MySQL SELECT with read-only account)
  → ⑦ Result Wrapping (table data + AI natural language analysis)
  → ⑧ Response (SQL + data + analysis + chart suggestion)
```

---

## 🛠️ Tech Stack

| Layer                         | Technology                                     | Purpose                                          |
| ----------------------------- | ---------------------------------------------- | ------------------------------------------------ |
| **Backend Framework**   | FastAPI 0.115+                                 | Async REST API, auto OpenAPI docs                |
| **Agent Orchestration** | LangGraph 0.2+                                 | StateGraph for 8-node DAG with conditional edges |
| **LLM**                 | DeepSeek API (`deepseek-chat`)               | Chinese-optimized reasoning + SQL generation     |
| **Embeddings**          | Qwen3-Embedding-8B (via Gitee AI)              | Schema & few-shot vector encoding                |
| **Vector DB**           | ChromaDB 0.5 (embedded mode)                   | Lightweight, zero-ops RAG storage                |
| **Metadata DB**         | MySQL 8.0 + SQLAlchemy 2.0                     | Structured metadata (ORM models)                 |
| **Cache (P1)**          | Redis 5.0                                      | Query result & schema hot-data cache             |
| **Frontend**            | React 18.3 + Vite 6 + MUI 6 + Tailwind CSS 3.4 | Modern SPA with enterprise UI components         |
| **Charts**              | Chart.js 4.5 (native)                          | Auto-derived bar/line/pie visualizations         |
| **Deployment**          | Docker Compose                                 | One-command: MySQL + Backend + Nginx             |

---

## 📁 Project Structure

```
lingwen/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── agent/              # LangGraph nodes (8-step pipeline)
│   │   ├── api/                # REST API routes + MCP SSE endpoint
│   │   ├── mcp_server/          # MCP Server (tools, auth)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic v2 request/response types
│   │   ├── services/           # Business logic layer
│   │   ├── rag/                # RAG: embeddings, vector store, retriever, indexer
│   │   ├── security/           # SQL guard + encryption
│   │   ├── middleware/         # JWT auth, CORS, logging
│   │   └── utils/              # CSV export, response helpers
│   ├── alembic/                # Database migrations
│   ├── tests/                  # pytest test suite
│   ├── mcp_entrypoint.py        # MCP stdio entry point
│   └── pyproject.toml          # Poetry dependencies
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── components/         # chat/, admin/, common/ components
│   │   ├── pages/              # LoginPage, ChatPage, admin pages
│   │   ├── services/           # Axios API client layer
│   │   ├── hooks/              # useQuery, useChart, useDatasources
│   │   ├── contexts/           # AuthContext, AppContext
│   │   └── types/              # TypeScript type definitions
│   └── package.json
├── docs/                       # PRD, architecture docs, diagrams
├── scripts/                    # Utility scripts (DB check, SQL export, etc.)
├── docker-compose.yml          # Single-command Docker deployment
├── init.sql                    # Database initialization + seed data
├── deploy-guide.md             # Detailed deployment instructions
├── .env.example                # Environment variable template
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites

| Component               | Requirement                              |
| ----------------------- | ---------------------------------------- |
| Docker + Docker Compose | v2+ (Docker Desktop 4.x+ on Windows/Mac) |
| CPU                     | 4 cores recommended                      |
| RAM                     | 8 GB recommended                         |
| Disk                    | 50 GB free                               |

### 5-Minute Docker Deployment

```bash
# 1. Clone and enter the project
cd lingwen

# 2. Configure environment variables
cp .env.example .env
# Edit .env — fill in your DeepSeek API key and Embedding API key

# 3. Start all services
docker compose up -d

# 4. Check status (all three services should show "healthy")
docker compose ps

# 5. Open in browser
# http://localhost:8080
# Default admin: admin / admin123
```

### Local Development

**Backend:**

```bash
cd lingwen/backend
pip install poetry && poetry install
cp .env.example .env  # edit as needed
alembic upgrade head
uvicorn app.main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

**Frontend:**

```bash
cd lingwen/frontend
npm install
cp .env.example .env  # VITE_API_BASE_URL=http://localhost:8000
npm run dev
# Dev server at http://localhost:5173
```

---

## 📡 API Overview

| Endpoint                       | Method         | Description                                          |
| ------------------------------ | -------------- | ---------------------------------------------------- |
| `/api/auth/login`            | POST           | User login → JWT token                              |
| `/api/query`                 | POST           | **Core**: NL question → data + analysis + SQL |
| `/api/datasources`           | GET/POST       | List / create datasources                            |
| `/api/datasources/{id}`      | GET/PUT/DELETE | Single datasource CRUD                               |
| `/api/datasources/{id}/test` | POST           | Test connection                                      |
| `/api/schema`                | GET            | Get schema (`?datasource_id=`)                     |
| `/api/schema/scan`           | POST           | Trigger schema scan                                  |
| `/api/metadata/tables`       | GET/PUT        | Table metadata                                       |
| `/api/metadata/columns`      | GET/PUT        | Column metadata                                      |
| `/api/few-shot`              | GET/POST       | Few-shot examples                                    |
| `/api/few-shot/{id}`         | GET/PUT/DELETE | Single example CRUD                                  |
| `/api/skills`                | GET/POST       | Skill templates                                      |
| `/api/skills/{id}`           | GET/PUT/DELETE | Single skill CRUD                                    |
| `/api/mcp/sse`              | GET            | MCP SSE endpoint (AI platform integration)           |

Full interactive API docs available at `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/redoc` (ReDoc).

---

## 🖥️ Services & Ports

| Service                    | Container Port | Host Port | URL                        |
| -------------------------- | -------------- | --------- | -------------------------- |
| **Frontend (Nginx)** | 80             | 8080      | http://localhost:8080      |
| **Backend API**      | 8000           | 8001      | http://localhost:8001/docs |
| **MySQL**            | 3306           | 3307      | mysql -h 127.0.0.1 -P 3307 |

---

## 📚 Documentation

| Document                                                | Description                                                      |
| ------------------------------------------------------- | ---------------------------------------------------------------- |
| [PRD (Product Requirements)](docs/lingwen-prd.md)          | Full product definition, user stories, requirements              |
| [Architecture Design](docs/lingwen-architecture.md)        | System design, class diagrams, sequence diagrams, task breakdown |
| [MCP Server Design](docs/lingwen-mcp-server-design.md)      | MCP tools, transports, auth, integration guide                    |
| [Deployment Guide](lingwen/deploy-guide.md)                | Docker deployment, configuration, troubleshooting                |
| [Competitive Analysis](docs/lingwen-vs-sqlbot-vs-dbgpt.md) | Lingwen vs SQLBot vs DB-GPT comparison                           |
| [System Design (Charts &amp; Export)](UI/system_design.md) | Chart visualization & data export design                         |

---

## 🗺️ Roadmap

- [X] **v0.1** — MVP: 8-step agent pipeline, MySQL datasource, chat UI, admin console
- [X] **v0.2** — Charts (Chart.js), CSV/Excel export, Few-shot management, Skill templates
- [x] **v0.3** — MCP Server, Redis caching, query history, audit logs
- [ ] **v1.0** — RBAC, row-level security, multi-datasource (PostgreSQL, ClickHouse)
- [ ] **v1.1** — Multi-turn conversation, semantic caching, SSO integration

---

## 🤝 Contributing

This project is currently developed by the Tianfu Yiwangjian engineering team. For contribution guidelines, please contact the team lead.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>灵问 (Lingwen)</b> — Making data as easy to access as asking a question.<br/>
  Built with ❤️ for the Tianfu Yiwangjian platform.
</p>
