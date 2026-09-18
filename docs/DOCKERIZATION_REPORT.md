# Docker 化最终报告

## 最终容器架构

生产运行 2 个容器：

1. `backend`：FastAPI + Uvicorn。
2. `nginx`：企业 H5、管理端静态资源、`/api` 反向代理。

MySQL 8 安装在独立数据库服务器，不进入生产 Compose。

## Dockerfile

- `Dockerfile`：backend 生产镜像，多阶段 Python 依赖安装，runtime 使用 `python:3.11-slim-bookworm`，非 root 用户 `app` 运行，内置 `/api/health` healthcheck。
- `Dockerfile.web`：Node 20 Alpine 构建 admin-web 与 enterprise-h5，最终 `nginx:1.27-alpine` 只保留 dist 和 Nginx 配置。

## Compose

`deploy/docker-compose.yml` 包含：

- `backend`
- `nginx`
- bridge network
- uploads bind mount
- healthcheck
- restart policy
- Docker 日志轮转

不包含 MySQL。

## Nginx

`deploy/nginx/default.conf`：

- `/` -> enterprise-h5 dist
- `/admin/` -> admin-web dist
- `/api/` -> backend:8000
- SPA `try_files` 防刷新 404
- `client_max_body_size 50m`

## Volume

生产使用 bind mount：

```text
/data/enterprise-center/uploads:/data/uploads
```

backend `.env` 中 `UPLOAD_DIR=/data/uploads`。

## 环境变量

新增/确认：

- `APP_ENV=production`
- `APP_SECRET_KEY`
- `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `UPLOAD_DIR`
- `UPLOADS_HOST_DIR`
- `REGISTRY_HOST`
- `IMAGE_NAMESPACE`
- `IMAGE_TAG`

`.env` 不提交 Git，不打入镜像。

## MySQL 连接方式

通过远程 MySQL 8：

```text
mysql+pymysql://USER:PASSWORD@DB_SERVER:3306/DATABASE?charset=utf8mb4
```

代码已支持 `DATABASE_URL`，也保留 `DB_HOST/DB_USER/DB_PASSWORD/DB_NAME` 兼容模式。

## Migration 策略

backend 启动不自动执行 migration。生产发布显式执行：

```bash
docker compose run --rm backend alembic upgrade head
```

失败则停止发布。

## Registry 策略

使用版本化镜像：

```text
${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-backend:${IMAGE_TAG}
${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-web:${IMAGE_TAG}
```

不绑定具体云厂商，不把 `latest` 作为唯一版本。

## 更新策略

数据库备份 -> 修改 `IMAGE_TAG` -> `docker compose pull` -> migration -> `docker compose up -d` -> health check。

## 回滚策略

修改 `IMAGE_TAG` 为上一版本后 pull/up。数据库 migration 不自动回滚，必须单独评估 schema 兼容性。

## Ubuntu 实际验证结果

已在当前开发环境完成的验证：

- `admin-web npm run build`：通过。仅有既有 Rollup PURE 注释提示和主 chunk 超过 500KB 的性能提示。
- `enterprise-h5 npm run build`：通过。
- `.venv/bin/pytest tests/ -q`：`40 passed, 826 warnings in 12.27s`。
- `.venv/bin/alembic current`：`011_sys_daily_serial (head)`。
- 后端配置读取路径确认，Alembic 从 settings 读取数据库连接确认。
- 前端 Vite/router base 最小调整完成。
- Compose 不包含 MySQL，Nginx SPA 路由配置完成，uploads bind mount 设计完成。

未完成的 Docker 实机验证：

- `docker --version`：当前执行环境返回 `docker: command not found`。
- `docker compose version`：当前执行环境返回 `docker: command not found`。
- 因当前环境未安装 Docker CLI，无法在本机执行 `docker build`、`docker compose config`、`docker compose up -d`、容器内 health check、上传下载持久化重建验证。

## Docker 环境 smoke test

仍需在具备 Docker 与 MySQL 8 的 Ubuntu 开发环境执行：

- `docker build -f Dockerfile .`
- `docker build -f Dockerfile.web .`
- `docker compose config`
- `docker compose up -d`
- `/api/health`
- 企业 H5 `/`
- admin-web `/admin/`
- 企业登录
- 管理端登录
- backend 访问 MySQL
- `alembic current`
- 上传文件
- 下载文件
- 删除并重建 backend 容器后附件仍可下载

## 已知问题

- 需要在有 Docker 和 MySQL 8 的 Ubuntu 开发环境执行真实构建与容器 smoke test 后，把结果补录到本报告。
- 生产登录方式需按业务方真实身份认证方案配置；生产环境 mock-login 已被代码阻断。

## 麒麟 V10 注意事项

- Docker/Compose 安装命令需以现场软件源为准。
- firewalld 只开放必要端口，不关闭整体防火墙。
- SELinux 启用时给 uploads 设置容器可写上下文，不直接永久关闭 SELinux。
- uploads 权限使用 UID/GID 10001，不使用 `chmod -R 777`。

## READY FOR KYLIN V10 PRODUCTION DEPLOYMENT

NO

原因：工程化文件与操作手册已完成，但还缺少在 Ubuntu + Docker + MySQL 8 环境中的实际 `docker build`、`docker compose up -d`、smoke test 验证记录。验证通过后可改为 YES。
