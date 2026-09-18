# 镜像构建与发布说明

## 版本号规则

生产禁止只依赖 `latest`。建议使用语义化版本：

- `1.0.0`：首次生产版本
- `1.0.1`：兼容性修复，不改变主要业务能力
- `1.1.0`：包含新功能或较大变更

同一次发布 backend 和 web 可以使用同一个 `IMAGE_TAG`。若只更新其中一个镜像，另一个也可以保留旧 tag，但生产 `.env` 的 tag 维度会更简单地推动两个服务一起对齐版本。

## 构建前检查

```bash
git status --short
pytest tests/ -q
cd admin-web && npm ci && npm run build
cd ../enterprise-h5 && npm ci && npm run build
```

确认通过后回到仓库根目录。

## 构建镜像

```bash
export REGISTRY_HOST=<REGISTRY_HOST>
export IMAGE_NAMESPACE=<IMAGE_NAMESPACE>
export IMAGE_TAG=1.0.0

docker build   -t ${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-backend:${IMAGE_TAG}   -f Dockerfile .

docker build   -t ${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-web:${IMAGE_TAG}   --build-arg ADMIN_BASE_PATH=/admin/   --build-arg H5_BASE_PATH=/   --build-arg API_BASE_URL=   -f Dockerfile.web .
```

`API_BASE_URL` 留空表示前端请求同源 `/api`，由 Nginx 转发 backend。

## 登录并推送 Registry

```bash
docker login ${REGISTRY_HOST}

docker push ${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-backend:${IMAGE_TAG}
docker push ${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-web:${IMAGE_TAG}
```

## 记录发布信息

建议每次发布记录：Git commit、镜像 tag、Alembic head、构建人、构建时间、测试结果。

```bash
git rev-parse HEAD
```

## 不要做的事

- 不要把 `.env`、真实密码、`APP_SECRET_KEY` COPY 进镜像。
- 不要在生产只使用 `latest`。
- 不要把 `requirements-dev.txt` 装进生产 backend 镜像。
- 不要把 `node_modules` 或前端源码带入最终 web 镜像。
