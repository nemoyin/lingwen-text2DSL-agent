# 天府一网监 Docker 快速部署指南

> 适用版本：v0.1.0 · 更新时间：2026-06-09

---

## 目录

1. [环境要求](#一环境要求)
2. [快速启动（5 分钟）](#二快速启动5-分钟)
3. [配置说明](#三配置说明)
4. [服务访问](#四服务访问)
5. [数据库管理](#五数据库管理)
6. [日志查看](#六日志查看)
7. [常见问题](#七常见问题)
8. [架构说明](#八架构说明)

---

## 一、环境要求

| 组件 | 要求 |
|------|------|
| **Docker** | Docker Desktop 4.x+（Windows/Mac）或 Docker CE 24+（Linux） |
| **Docker Compose** | Docker Compose v2（已集成在 Docker Desktop 中） |
| **CPU** | 建议 4 核及以上 |
| **内存** | 建议 8 GB 及以上 |
| **磁盘** | 建议 50 GB 可用空间 |

---

## 二、快速启动（5 分钟）

### 2.1 克隆项目

```bash
cd /path/to/project
```

### 2.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填写真实的 API Key
# 关键必填项：
# - LINGWEN_LLM_API_KEY      # DeepSeek API Key
# - LINGWEN_EMBED_API_KEY    # Gitee AI Embedding API Key
# - MYSQL_ROOT_PASSWORD      # MySQL root 密码（可选，有默认值）
```

### 2.3 启动所有服务

```bash
docker compose up -d
```

首次启动会自动：
1. 拉取 `mysql:8.0`、`python:3.11-slim`、`node:20-alpine`、`nginx:alpine` 镜像
2. 构建后端和前端镜像
3. 创建 `lingwen_metadata`、`lingwen_temp`、`lingwen_xiaofu` 三个数据库
4. 运行 Alembic 数据库迁移（创建表结构）
5. 启动 Uvicorn 服务

### 2.4 查看启动日志

```bash
# 查看所有服务的日志
docker compose logs -f

# 查看指定服务的日志
docker compose logs -f backend
docker compose logs -f mysql
docker compose logs -f nginx
```

### 2.5 确认服务状态

```bash
# 查看服务状态
docker compose ps

# 预期输出：
# NAME              IMAGE                   STATUS          PORTS
# tianfu-mysql      mysql:8.0               Up (healthy)    0.0.0.0:3307->3306/tcp
# tianfu-backend    lingwen-backend         Up (healthy)    0.0.0.0:8001->8000/tcp
# tianfu-nginx      lingwen-nginx           Up (healthy)    0.0.0.0:8080->80/tcp
```

### 2.6 访问应用

首次启动时，`init.sql` 会自动完成以下初始化：
- 创建 3 个数据库（`lingwen_metadata`、`lingwen_temp`、`lingwen_xiaofu`）
- 创建全部 18 张数据表
- 导入种子数据（管理员用户、角色权限、模型配置、技能模板等）

在浏览器中打开 **http://localhost:8080**

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

---

## 三、配置说明

### 3.1 环境变量清单（.env）

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 | `andy_l007` | 否 |
| `LINGWEN_LLM_API_KEY` | DeepSeek API 密钥 | - | **是** |
| `LINGWEN_LLM_MODEL` | LLM 模型名 | `deepseek-chat` | 否 |
| `LINGWEN_EMBED_API_KEY` | Embedding API 密钥 | - | **是** |
| `LINGWEN_EMBED_BASE_URL` | Embedding 服务地址 | `https://ai.gitee.com/v1` | 否 |
| `LINGWEN_LLM_EMBED_MODEL` | Embedding 模型名 | `Qwen3-Embedding-8B` | 否 |
| `LINGWEN_JWT_SECRET` | JWT 签名密钥 | `lingwen-docker-secret-2026` | 否 |
| `LINGWEN_JWT_EXPIRE_MINUTES` | JWT 过期时间（分钟）| `480` | 否 |

### 3.2 端口映射说明

| 容器端口 | 宿主机端口 | 说明 | 冲突时修改 |
|----------|-----------|------|-----------|
| MySQL 3306 | **3307** | 数据库（避让本地 MySQL） | 修改 `docker-compose.yml` |
| 后端 8000 | **8001** | API 服务（避让本地开发） | 修改 `docker-compose.yml` |
| Nginx 80 | **8080** | 前端应用 | 修改 `docker-compose.yml` |

> **自定义端口示例**：如要将前端改为 80 端口，在 `docker-compose.yml` 中改 `"8080:80"` → `"80:80"`

### 3.3 持久化数据

| 数据 | 挂载路径 | 说明 |
|------|---------|------|
| MySQL 数据 | `mysql-data` 卷 | 数据库表数据，停止容器不会丢失 |
| ChromaDB 向量数据 | `chromadb-data` 卷 | RAG 检索的向量索引 |
| 后端日志 | `./backend/logs` | 应用运行日志（本地目录） |

---

## 四、服务访问

| 服务 | 内部地址（容器间） | 外部地址（宿主机） |
|------|-------------------|-------------------|
| 前端页面 | - | http://localhost:8080 |
| API 文档 | http://backend:8000/docs | http://localhost:8001/docs |
| MySQL 数据库 | mysql:3306 | localhost:3307 |

### 4.1 测试 API

```bash
# 健康检查
curl http://localhost:8001/api/health
# 预期输出：{"status": "ok"}

# 登录
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## 五、数据库管理

### 5.1 本地连接（Docker MySQL）

```bash
# 使用命令行连接
mysql -h 127.0.0.1 -P 3307 -u root -p

# 查看数据库
mysql> SHOW DATABASES;
# lingwen_metadata
# lingwen_temp
# lingwen_xiaofu

# 查看用户表
mysql> USE lingwen_metadata;
mysql> SHOW TABLES;
# users, datasources, tables_metadata, columns_metadata,
# few_shot_examples, skill_templates, query_history
```

### 5.2 备份与恢复

```bash
# 备份数据库
docker exec tianfu-mysql mysqldump -u root -p lingwen_metadata > backup.sql

# 恢复数据库
docker exec -i tianfu-mysql mysql -u root -p lingwen_metadata < backup.sql
```

---

## 六、日志查看

```bash
# 后端日志（实时流）
docker compose logs -f backend

# 后端日志（最近 100 行）
docker compose logs --tail=100 backend

# Nginx 访问日志
docker compose logs -f nginx

# 查看持久化的后端日志文件
cat backend/logs/lingwen.log
```

---

## 七、常见问题

### Q1: 端口冲突怎么办？

启动时若提示端口被占用，修改 `docker-compose.yml` 中的映射端口：

```yaml
services:
  mysql:
    ports:
      - "3308:3306"   # 改为其他未占用端口
  backend:
    ports:
      - "8002:8000"   # 改为其他未占用端口
  nginx:
    ports:
      - "8081:80"     # 改为其他未占用端口
```

### Q2: 如何重建所有容器？

```bash
# 停止并删除所有容器、网络
docker compose down

# 清理数据卷（⚠️ 会丢失所有数据）
docker compose down -v

# 重新构建并启动
docker compose up -d --build
```

### Q3: 数据库迁移失败怎么办？

```bash
# 手动运行迁移
docker compose exec backend alembic upgrade head

# 查看迁移状态
docker compose exec backend alembic current
```

### Q4: 如何查看容器内的文件？

```bash
# 进入后端容器
docker compose exec backend bash

# 进入 MySQL 容器
docker compose exec mysql bash
```

### Q5: 如何更新到新版本？

```bash
# 拉取最新代码后
docker compose down
docker compose up -d --build
```

### Q6: 启动后页面空白 / 接口 502？

```bash
# 检查后端是否就绪
docker compose logs backend

# 检查 MySQL 是否就绪
docker compose logs mysql

# 检查 Nginx 配置
docker compose exec nginx nginx -t
```

---

## 八、架构说明

```
┌─────────────────────────────────────────────────────────┐
│                   用户浏览器                              │
└──────────────────────┬──────────────────────────────────┘
                       │ http://localhost:8080
                       ▼
┌──────────────────────────────────────────────────────────┐
│  Nginx (tianfu-nginx)                                    │
│  ┌──────────────────────────────────────────────────┐    │
│  │  / → 前端静态文件 (dist/)                          │    │
│  │  /api/* → 反向代理到 http://backend:8000          │    │
│  └──────────────────────────────────────────────────┘    │
│  端口: 80(容器内) → 8080(宿主机)                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  Backend (tianfu-backend)                                │
│  FastAPI + LangGraph Text2SQL Pipeline                   │
│  ChromaDB (嵌入进程内)                                    │
│  端口: 8000(容器内) → 8001(宿主机)                        │
└──────┬──────────────────┬─────────────────────────────┬──┘
       │                  │                             │
       ▼                  ▼                             ▼
┌──────────────┐  ┌──────────────┐     ┌──────────────────┐
│  MySQL :3306  │  │  DeepSeek    │     │  Gitee AI        │
│  容器内:3306   │  │  LLM API     │     │  Embedding API   │
│  宿主机:3307   │  │  (外部)      │     │  (外部)           │
└──────────────┘  └──────────────┘     └──────────────────┘
```

### 镜像大小预估

| 服务 | 基础镜像 | 最终大小 |
|------|---------|---------|
| MySQL | `mysql:8.0` | ~600 MB |
| 后端 | `python:3.11-slim` + 依赖 | ~1.2 GB |
| Nginx | `nginx:alpine` + 前端静态文件 | ~50 MB |
| **总计** | | **~1.9 GB** |

---

## 附录：验证清单

部署完成后，可通过以下命令验证所有服务正常运行：

```bash
# 1. 查看服务状态
docker compose ps
# 所有服务应为 Up (healthy)

# 2. 测试健康检查
curl http://localhost:8080/api/health
# 预期: {"status":"ok"}

# 3. 测试登录
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# 预期: code=200, 返回 access_token

# 4. 访问前端页面
# 浏览器打开 http://localhost:8080
# 应显示登录页面

# 5. 访问 API 文档
# 浏览器打开 http://localhost:8001/docs
```
