# 灵问（lingwen）智能问数引擎 — MVP PRD

> **版本**: v1.0 | **日期**: 2026-05-28 | **作者**: Alice（产品经理）

---

## 1. 项目信息

| 项目 | 说明 |
|------|------|
| **语言** | 中文 |
| **技术栈** | 后端：FastAPI + LangChain/LangGraph + DeepSeek API；前端：Vite + React + MUI + Tailwind CSS |
| **项目名称** | `lingwen` |
| **产品定位** | 独立、可复用的通用智能问数引擎，基于 Agent + RAG 五层架构，先独立产品化，后续集成到一网监系统 |
| **MVP 数据源** | MySQL（单源，后续扩展 PostgreSQL、ClickHouse 等） |
| **向量数据库** | ChromaDB（轻量起步，后续可迁移至 Milvus） |

### 原始需求复述

政府大数据监督系统"一网监"当前使用 DeepSeek API 直接 Text2SQL，SQL 准确率低。需升级为 Agent + RAG 架构，打造独立通用智能问数引擎"灵问"，MVP 阶段支持 MySQL 单数据源，提供 API 服务 + 管理后台 + 对话界面。

---

## 2. 产品定义

### 2.1 产品目标（Product Goals）

| # | 目标 | 衡量标准 |
|---|------|----------|
| **G1** | Text2SQL 准确率达到生产可用水平 | SQL 首次生成正确率 ≥ 80%（通过 RAG + CoT + 自动重试机制） |
| **G2** | 端到端查询体验流畅 | 自然语言→结果展示 P95 响应时间 ≤ 5s |
| **G3** | 支撑中等规模并发使用 | 并发请求 ≥ 50，系统稳定不降级 |

### 2.2 核心用户故事（User Stories）

#### P0（MVP 必须实现）

| ID | 用户故事 | 验收标准 |
|----|----------|----------|
| **US-1** | 作为**业务人员**，我可以在对话界面用自然语言提问（如"本月各部门销售额"），系统自动生成 SQL 并返回数据表格和 AI 分析，**以便**无需依赖技术人员即可自助获取数据洞察 | 输入自然语言→数秒内返回表格+文字分析 |
| **US-2** | 作为**数据分析师**，当 SQL 生成结果不准确时，系统能自动重试或给出明确的失败原因，**以便**我能判断结果是可信的 | 执行失败自动重试 2 次，兜底返回 CoT 推理过程 |
| **US-3** | 作为**系统管理员**，我可以在管理后台配置 MySQL 数据源并触发自动 Schema 扫描，**以便**新数据源能快速接入系统 | 填写连接信息→保存→扫描→看到表结构和字段列表 |
| **US-4** | 作为**系统管理员**，我可以在元数据管理界面浏览和编辑表/字段的业务语义（中文名、业务描述、枚举值），**以便**提升 RAG 检索的准确度和 SQL 生成质量 | 支持字段级编辑和批量导入 |
| **US-5** | 作为**数据安全管理员**，系统的 SQL 执行必须自动拦截 DROP/DELETE/UPDATE 等危险操作，并限制单次返回 ≤ 1000 行，**以便**防止数据泄露和误操作 | 危险 SQL 被拦截并提示；超 1000 行自动截断并告知 |

#### P1（MVP 应该实现）

| ID | 用户故事 | 验收标准 |
|----|----------|----------|
| **US-6** | 作为**数据分析师**，我可以管理 Few-shot 示例（查询文本→正确 SQL），**以便**持续优化特定业务场景的 SQL 生成准确率 | CRUD 操作 Few-shot 示例，并关联到指定数据源 |
| **US-7** | 作为**数据分析师**，我可以使用预置的通用"智能问数"Skill 模板，**以便**开箱即用地获得标准问数能力 | Skill 模板包含 RAG 配置、Prompt 模板、安全策略 |
| **US-8** | 作为**业务人员**，对话结果支持复制原始数据和导出 CSV，**以便**在 Excel 中进一步分析 | 一键复制表格数据、一键导出 CSV |

#### P2（MVP 可以延后）

| ID | 用户故事 | 验收标准 |
|----|----------|----------|
| **US-9** | 作为**系统管理员**，我可以查看查询历史审计日志，**以便**追溯数据访问行为 | 记录用户、时间、原始问题、生成 SQL、执行结果摘要 |
| **US-10** | 作为**业务人员**，热门查询能被缓存加速（Redis），**以便**重复问题的响应更快 | 相同问题命中缓存时响应时间显著降低 |

---

## 3. 技术规范

### 3.1 功能需求池（Requirements Pool）

#### P0 — 必须交付

| ID | 需求 | 说明 |
|----|------|------|
| **R-P0-01** | MySQL 数据源连接管理 | 管理后台配置连接信息（host/port/user/password/database），连接测试，保存加密存储 |
| **R-P0-02** | 自动 Schema 扫描 | 读取 `information_schema`，提取表名、字段名、类型、注释、索引信息，存入元数据库 |
| **R-P0-03** | 元数据管理（浏览+编辑） | 管理后台展示表/字段列表，支持编辑中文名、业务描述、枚举值映射、关联关系标注 |
| **R-P0-04** | 自然语言对话界面 | 输入框 + 发送按钮，支持展示：数据表格 + AI 文字分析 + 生成的 SQL（可折叠） |
| **R-P0-05** | 8 步 Agent 链路 | 意图识别 → 权限预校验 → RAG 并行检索（Schema + Few-shot） → SQL 生成（CoT） → SQL 校验+安全注入 → 执行 → 结果包装 → 返回 |
| **R-P0-06** | RAG 检索 — Schema 检索 | 基于用户问题语义检索相关表结构和字段注释，ChromaDB 实现 |
| **R-P0-07** | RAG 检索 — Few-shot 示例检索 | 基于用户问题语义检索历史正确 SQL 示例 |
| **R-P0-08** | SQL 生成（CoT 思维链） | 先推理再输出 SQL，DeepSeek API 调用 |
| **R-P0-09** | SQL 自动重试 | 执行失败自动重试 2 次，每次携带错误信息让模型修正 |
| **R-P0-10** | SQL 安全校验 | 拦截 DROP/DELETE/UPDATE/INSERT/ALTER/TRUNCATE 等写操作；拦截 SQL 注入特征 |
| **R-P0-11** | 结果行数限制 | 强制 `LIMIT 1000`，超限时截断并提示用户 |
| **R-P0-12** | JWT 认证 | 用户登录获取 Token，所有 API 需携带有效 Token |
| **R-P0-13** | POST `/api/query` | 核心查询 API：接收自然语言问题 + 数据源 ID，返回表格数据 + AI 分析 + SQL |
| **R-P0-14** | 数据源 CRUD API | GET/POST `/api/datasources`，GET/PUT/DELETE `/api/datasources/{id}` |
| **R-P0-15** | Schema API | GET `/api/schema?datasource_id=`，POST `/api/schema/scan` |
| **R-P0-16** | 加载/错误/空状态处理 | 前端对所有异步操作提供 loading spinner、错误提示、空数据占位 |

#### P1 — 应该交付

| ID | 需求 | 说明 |
|----|------|------|
| **R-P1-01** | Few-shot 示例管理 CRUD | 管理后台：问题文本 + SQL + 数据源关联，增删改查 |
| **R-P1-02** | 通用 Skill 模板 | 预置"智能问数"Skill：包含默认 Prompt 模板、RAG 配置、安全策略 |
| **R-P1-03** | Skill 模板管理后台 | 浏览 Skill 模板、编辑 Prompt 模板参数 |
| **R-P1-04** | 结果复制 | 一键复制表格数据（TSV 格式到剪贴板） |
| **R-P1-05** | CSV 导出 | 导出当前查询结果为 CSV 文件 |
| **R-P1-06** | Redis 查询缓存 | 热门查询结果缓存（问题文本 + 数据源 ID 作为 key），TTL 可配置 |
| **R-P1-07** | Redis Schema/权限缓存 | 数据源 Schema 和用户权限缓存，减少 DB 查询 |

#### P2 — 可以延后

| ID | 需求 | 说明 |
|----|------|------|
| **R-P2-01** | 查询历史 | 记录用户查询历史，支持回看和重复执行 |
| **R-P2-02** | 审计日志 | 全链路操作日志：谁、何时、问了什么、生成了什么 SQL、执行结果 |
| **R-P2-03** | RBAC 权限 | 用户角色管理，数据源级别访问控制 |
| **R-P2-04** | 行级权限注入 | 根据用户身份自动注入数据范围过滤条件 |
| **R-P2-05** | 多数据源支持 | PostgreSQL、ClickHouse 等 |

### 3.2 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                   用户交互层                              │
│  对话界面 (React)  │  管理后台 (React)  │  API 服务       │
├─────────────────────────────────────────────────────────┤
│                   业务功能层                              │
│  对话上下文管理  │  元数据管理  │  Skill 管理  │  Few-shot  │
├─────────────────────────────────────────────────────────┤
│                   核心能力层                              │
│  Agent 编排 (LangGraph)  │  RAG 检索  │  Text2SQL (DeepSeek) │
├─────────────────────────────────────────────────────────┤
│                   安全控制层                              │
│  JWT 认证  │  SQL 注入拦截  │  危险操作拦截  │  行数限制   │
├─────────────────────────────────────────────────────────┤
│                   基础设施层                              │
│  DeepSeek API  │  ChromaDB  │  MySQL  │  Redis           │
└─────────────────────────────────────────────────────────┘
```

### 3.3 8 步 Agent 处理链路

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

### 3.4 数据模型概要

```
datasources
  id, name, db_type, host, port, database, username, password(encrypted),
  status, created_at, updated_at

tables_metadata
  id, datasource_id, table_name, display_name, business_description,
  created_at, updated_at

columns_metadata
  id, table_id, column_name, display_name, data_type, business_description,
  enum_values(JSON), is_primary_key, is_foreign_key, foreign_ref,
  created_at, updated_at

few_shot_examples
  id, datasource_id, question, sql, description, tags,
  created_at, updated_at

skill_templates
  id, name, description, prompt_template, rag_config(JSON),
  security_policy(JSON), is_active, created_at, updated_at

query_history (P2)
  id, user_id, datasource_id, question, generated_sql, executed_sql,
  result_summary, status, error_message, latency_ms, created_at
```

### 3.5 UI 设计要点

#### 对话界面

```
┌────────────────────────────────────────────┐
│  🔍 灵问 · 智能问数引擎                      │
│  ┌──────────────────────────────────────┐  │
│  │ 数据源: [一网监生产库 ▼]               │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ 📊 本月各部门销售额                    │  │
│  │                                      │  │
│  │ ┌────────┬──────────┬──────────┐    │  │
│  │ │ 部门   │ 销售额(万)│ 环比(%)  │    │  │
│  │ ├────────┼──────────┼──────────┤    │  │
│  │ │ 市场部 │ 1,250    │ +12.3    │    │  │
│  │ │ 销售部 │ 2,100    │ +5.7     │    │  │
│  │ │ ...    │ ...      │ ...      │    │  │
│  │ └────────┴──────────┴──────────┘    │  │
│  │                                      │  │
│  │ 📝 AI分析：本月销售部销售额最高，达    │  │
│  │ 2100万元。市场部环比增长最快(12.3%)。  │  │
│  │                                      │  │
│  │ 🔽 查看生成的 SQL                     │  │
│  │ [复制数据] [导出CSV]                   │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ 输入您的问题...                  [发送]│  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

**关键交互**：
- 输入框支持 Enter 发送、Shift+Enter 换行
- SQL 默认折叠，点击展开
- 加载态：骨架屏 + "正在分析您的問題…"
- 错误态：红色提示 + 错误摘要 + "重试"按钮
- 空态：首次进入展示示例问题列表

#### 管理后台

左侧导航：数据源管理 / 元数据管理 / Skill 模板 / Few-shot 示例

**数据源管理页**：表格列表 + 新增/编辑对话框（表单：名称、类型、主机、端口、数据库、用户名、密码）+ 操作按钮（测试连接、扫描 Schema、编辑、删除）

**元数据管理页**：数据源选择器 → 表列表（左侧树） + 字段详情（右侧表格，可内联编辑显示名、业务描述、枚举值）

**Skill 模板页**：卡片列表 + 查看/编辑 Prompt 模板（代码编辑器）+ RAG 配置面板

**Few-shot 示例页**：搜索 + 表格列表 + 新增/编辑对话框（问题文本、SQL、标签、关联数据源）

### 3.6 API 设计概要

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录，返回 JWT Token |
| `/api/query` | POST | 核心问数接口：`{question, datasource_id}` → `{data, analysis, sql, chart_suggestion}` |
| `/api/datasources` | GET | 数据源列表 |
| `/api/datasources` | POST | 创建数据源 |
| `/api/datasources/{id}` | GET/PUT/DELETE | 单个数据源 CRUD |
| `/api/datasources/{id}/test` | POST | 测试连接 |
| `/api/schema` | GET | 获取 Schema（支持 `?datasource_id=`） |
| `/api/schema/scan` | POST | 触发 Schema 扫描 `{datasource_id}` |
| `/api/metadata/tables` | GET/PUT | 表元数据查询/更新 |
| `/api/metadata/columns` | GET/PUT | 字段元数据查询/更新 |
| `/api/few-shot` | GET/POST | Few-shot 示例列表/创建 |
| `/api/few-shot/{id}` | GET/PUT/DELETE | 单个示例 CRUD |
| `/api/skills` | GET/POST | Skill 模板列表/创建 |
| `/api/skills/{id}` | GET/PUT/DELETE | 单个 Skill CRUD |
| `/api/query/history` | GET | 查询历史（P2） |

---

## 4. 待确认问题（Open Questions）

| # | 问题 | 优先级 |
|---|------|--------|
| **Q1** | 一网监现有 SQL 示例有多少条？质量如何？能否直接作为 Few-shot 种子数据？ | 🔴 高（影响 RAG 冷启动效果） |
| **Q2** | DeepSeek API 的并发限制和超时策略是什么？是否需要配置备用模型？ | 🔴 高（影响可用性设计） |
| **Q3** | 用户体系如何设计？MVP 采用自建账号还是对接一网监现有认证系统（SSO/LDAP）？ | 🟡 中 |
| **Q4** | 80% 准确率的衡量标准是什么？"正确"的定义：SQL 语法正确？执行结果完全一致？用户主观满意？ | 🟡 中 |
| **Q5** | 元数据管理中的"业务语义"由谁来维护？管理员手动填写还是有自动化流程？ | 🟡 中 |
| **Q6** | MVP Redis 缓存粒度和过期策略？是否需要缓存失效机制（Schema 变更时失效）？ | 🟢 低 |

---

## 5. v1.0+ 已实现扩展功能（超 MVP 范围）

以下功能在 PRD 原始范围之外，已于开发过程中实现并通过 E2E 验证。

### 5.1 多数据源适配（8 种）

| 数据源 | 适配器 | 驱动 | E2E 状态 |
|--------|--------|------|----------|
| MySQL | `mysql_adapter` | aiomysql | ✅ |
| PostgreSQL | `postgresql_adapter` | asyncpg | ✅ |
| Apache Doris | `doris_adapter` | aiomysql (MySQL 兼容) | ✅ |
| ClickHouse | `clickhouse_adapter` | clickhouse-connect + to_thread | ✅ |
| Oracle | `oracle_adapter` | oracledb | ✅ |
| Apache Hive | `hive_adapter` | pyhive + to_thread | ✅ |
| Elasticsearch | `elasticsearch_adapter` | elasticsearch-py (ES|QL) | ✅ |
| 达梦 DM8 | `dm_adapter` | dmPython + to_thread | ✅ |

**架构特点**：
- 插件化注册机制：`@register_adapter` 装饰器 + `get_adapter(db_type)` 工厂
- 方言提示自动注入：SQL 生成时根据数据源类型注入对应 SQL 方言
- Async/Sync 降级：同步驱动自动包装 `asyncio.to_thread()`
- 非 SQL 查询支持：ES|QL、HiveQL 通过原生客户端执行

### 5.2 SSE 流式推送

`POST /api/query/stream` 端点，实时推送管线各步骤进度 + LLM 推理过程：

```
data: {"event":"step","step":"意图识别","status":"completed","elapsed_ms":5,"reasoning":"..."}
data: {"event":"step","step":"SQL生成","status":"completed","elapsed_ms":2239,"reasoning":"..."}
data: {"event":"done","data":{...}}
```

### 5.3 Agent 测评模块

| 功能 | 说明 |
|------|------|
| 测试集管理 | CSV 上传（question, expected_answer），CRUD |
| 测评任务 | 选择测试集 + 数据源 → 创建执行任务 |
| 实时进度 | 逐题更新 passed/total，前端 2s 轮询 + 进度条 + 闪烁指示 |
| 详情报告 | 每题期望/实际答案、生成 SQL、管线步骤、相似度评分、延迟 |
| 评分机制 | 关键词匹配 + 错误答案识别（`ERROR:`/`查询失败` 自动 0 分） |

API 端点：`/api/benchmark/sets`、`/api/benchmark/runs`、`/api/benchmark/runs/{id}/execute`

### 5.4 多轮对话

- 请求支持 `history` 上下文（`[{question, answer}, ...]`）
- `max_context_turns` 控制上下文窗口大小（默认 6 轮）
- 追问建议：每条回复自动生成 3 个相关后续问题

### 5.5 多 LLM 模型管理

| 功能 | 说明 |
|------|------|
| 模型 CRUD | DeepSeek / Kimi / OpenAI / GLM / Minimax 配置管理 |
| 动态切换 | `POST /api/models/{id}/set-default` 切换默认模型 |
| 连接测试 | `POST /api/models/{id}/test` 测试 API 连通性 |

### 5.6 预警与案件管理

- 预警创建 → 升级为案件 → 案件列表
- 支持目标单位、预警内容、案件编号、处理人、是否立案

### 5.7 数据可视化增强

- Chart.js 原生实现（非 react-chartjs-2），自定义 `useChart` hook
- 图表类型切换（bar/line/pie）+ 全屏模式
- 数据表格 + 截断提示
- CSV/Excel 导出（UTF-8 BOM + xlsx）
- 一键 TSV 复制
- 语音输入（STT）+ 语音播报（TTS，Web Speech API）

### 5.8 运维与监控

- Dashboard 仪表盘（KPI 卡片 + 趋势图 + 性能指标）
- 在线日志查看（按级别过滤 + 分页 + 自动刷新）
- 个人设置（主题 dark/light + 语言 zh/en）
- CSV 文件上传（自动创建临时数据源并支持问答）

### 5.9 Agent 管线增强

- **SQL 安全校验**：`sql_gen → sql_validate → sql_exec`，SqlGuard 拦截危险操作（DROP/DELETE 等）+ LIMIT 1000 注入
- **方言提示注入**：根据数据源 db_type 自动注入对应 SQL 方言到 LLM prompt
- **Markdown 清洗**：自动去除 LLM 输出中的 markdown fence
- **元数据回退**：RAG 无结果时自动从数据库查询表结构
| **Q7** | 对话是否需要多轮上下文？MVP 仅支持单轮问答，还是支持追问和澄清？ | 🟢 低 |
