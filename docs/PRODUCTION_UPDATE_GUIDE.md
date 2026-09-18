# 生产更新操作手册

## 开发机发布新版本

1. 合并代码并确认 Git 版本。
2. 运行回归测试：

```bash
pytest tests/ -q
```

3. 构建两个前端：

```bash
cd admin-web && npm ci && npm run build
cd ../enterprise-h5 && npm ci && npm run build
```

4. 构建、tag、push 镜像，见 `docs/IMAGE_BUILD_AND_PUBLISH_GUIDE.md`。

## 生产服务器更新流程

进入部署目录：

```bash
cd /opt/enterprise-center
```

1. 备份数据库和 uploads。
2. 修改 `.env` 中 `IMAGE_TAG` 为新版本，例如：

```bash
sed -i 's/^IMAGE_TAG=.*/IMAGE_TAG=1.0.1/' .env
```

3. 拉取镜像：

```bash
docker compose pull
```

4. 执行数据库迁移：

```bash
docker compose run --rm backend alembic upgrade head
```

5. 迁移成功后启动新版本：

```bash
docker compose up -d
docker compose ps
./scripts/healthcheck.sh
```

## 只更新 backend

适用：只改后端逻辑、迁移、Python 依赖，前端构建产物不变。

建议仍使用新的 `IMAGE_TAG` 推送 backend。若 web 镜像无同 tag，可临时在 Compose 中拆分 `BACKEND_IMAGE_TAG`/`WEB_IMAGE_TAG`，但当前简洁方案默认两个镜像同 tag，便于回滚和记录。

## 只更新 web

适用：只改 admin-web 或 enterprise-h5 页面、样式、前端请求封装，不涉及后端接口和数据库。

可跳过 migration，但仍建议执行：

```bash
docker compose pull
docker compose up -d nginx
docker compose ps
./scripts/healthcheck.sh
```

## backend 和 web 都更新

适用：接口字段、权限、状态展示、数据库迁移、前后端联动调整。必须按完整流程执行，migration 成功后再 `up -d`。

## 回滚提醒

应用镜像回滚不等于数据库自动回滚。如果新版本执行过 Alembic migration，必须评估旧程序是否兼容新 schema。禁止自动执行危险 downgrade。
