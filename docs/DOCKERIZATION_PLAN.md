# Docker 化实施计划

## 部署前代码检查结论

| 检查项 | 当前结论 | Docker 化处理 |
|---|---|---|
| FastAPI 启动方式 | `app/main.py` 暴露 `app`，可用 `uvicorn app.main:app` 启动 | backend 镜像以 Uvicorn 启动，不在入口中自动迁移 |
| Uvicorn | `requirements.txt` 已固定 `uvicorn[standard]==0.29.0` | backend runtime 使用 `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| SQLAlchemy | `app/core/database.py` 通过 settings 创建 MySQL engine，`pool_pre_ping=True` | 生产通过环境变量连接独立 MySQL 8 |
| Alembic | `migrations/env.py` 从 `settings.database_url` 读取连接 | 使用 `docker compose run --rm backend alembic upgrade head` 显式执行 |
| uploads | `UPLOAD_DIR` 可配置，实际文件位于 `{UPLOAD_DIR}/attachments` | 生产 bind mount `/data/enterprise-center/uploads:/data/uploads` |
| 日志 | 后端输出到 stdout/stderr，Nginx 输出 access/error log | Compose `json-file` 轮转 `max-size/max-file` |
| 静态资源 | 两个 Vue 项目均为 Vite build 产物 | 单独 web 镜像构建 dist，由 Nginx 提供 |
| admin-web | API 支持相对路径；已改为支持 `VITE_BASE_PATH=/admin/` | 部署在 `/admin/`，刷新路由由 Nginx `try_files` 兜底 |
| enterprise-h5 | API 支持相对路径；已改为支持 `VITE_BASE_PATH=/` | 部署在 `/`，刷新路由由 Nginx `try_files` 兜底 |
| API Base URL | `VITE_API_BASE_URL` 留空时同源访问 `/api` | 生产同域部署，构建时留空 |
| Vue Router | 已使用 `createWebHistory(import.meta.env.BASE_URL)` | 与 Vite `base` 保持一致 |
| CORS | 后端支持 `CORS_ALLOWED_ORIGINS` | 同域部署通常不触发 CORS；跨域时显式配置域名 |
| APP_ENV | 生产下关闭 Swagger/mock-login | Compose `.env` 设置 `APP_ENV=production` |
| APP_SECRET_KEY | 生产下强校验，默认/短密钥拒绝启动 | 仅通过 `.env` 注入，不打入镜像 |
| 数据库连接 | 已支持 `DATABASE_URL`，兼容旧 `DB_*` 字段 | 使用远程 MySQL 8 URL，不硬编码 IP |
| health endpoint | `/api/health` 与 `/api/common/health` 存在 | 容器 healthcheck 使用 `/api/health` |

## 最终容器架构

生产 Compose 只运行两个容器：

1. `backend`：FastAPI + Uvicorn，连接独立数据库服务器 MySQL 8，挂载 uploads。
2. `nginx`：提供 enterprise-h5 `/`、admin-web `/admin/`，并反向代理 `/api/` 到 backend。

MySQL 不进入 Docker Compose。数据库安装在独立麒麟 V10 数据库服务器，通过 TCP 3306 从应用服务器访问。

## 镜像

- backend：`python:3.11-slim-bookworm` 多阶段构建，只安装 `requirements.txt`，不包含 tests 和 dev 依赖，非 root 用户运行。
- web：Node 20 Alpine 构建两个前端，最终 `nginx:1.27-alpine` 只保留 dist 与 Nginx 配置。

生产使用版本化镜像：

```bash
${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-backend:${IMAGE_TAG}
${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-web:${IMAGE_TAG}
```

## 迁移策略

不在 backend 启动时自动执行 Alembic。上线和更新必须显式执行：

```bash
docker compose run --rm backend alembic upgrade head
```

如果 migration 失败，停止发布，不执行 `docker compose up -d`。

## 持久化策略

上传目录使用宿主机 bind mount：

```text
/data/enterprise-center/uploads -> /data/uploads
```

`.env` 中设置：

```dotenv
UPLOAD_DIR=/data/uploads
UPLOADS_HOST_DIR=/data/enterprise-center/uploads
```

容器删除、重建、升级不会删除宿主机 uploads。

## 日志策略

后端与 Nginx 均写 stdout/stderr，由 Docker `json-file` 保存，并通过 Compose 设置轮转：

```yaml
max-size: 50m
max-file: 5
```

Nginx 容器内仍使用标准 `/var/log/nginx/access.log` 与 `error.log`，由官方镜像链接到容器输出。
