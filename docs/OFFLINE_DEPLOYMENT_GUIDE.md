# 离线部署应急说明

主部署方案是 Registry。以下流程仅用于 Registry 不可用或现场网络受限时应急。

## 开发机导出镜像

```bash
export REGISTRY_HOST=<REGISTRY_HOST>
export IMAGE_NAMESPACE=<IMAGE_NAMESPACE>
export IMAGE_TAG=1.0.0

mkdir -p offline-images

docker save   ${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-backend:${IMAGE_TAG}   -o offline-images/enterprise-center-backend-${IMAGE_TAG}.tar

docker save   ${REGISTRY_HOST}/${IMAGE_NAMESPACE}/enterprise-center-web:${IMAGE_TAG}   -o offline-images/enterprise-center-web-${IMAGE_TAG}.tar
```

## 传输到应用服务器

```bash
scp offline-images/*.tar user@<APP_SERVER_IP>:/opt/enterprise-center/offline-images/
```

## 应用服务器导入镜像

```bash
cd /opt/enterprise-center

docker load -i offline-images/enterprise-center-backend-1.0.0.tar
docker load -i offline-images/enterprise-center-web-1.0.0.tar

docker images | grep enterprise-center
```

## 启动

`.env` 中的 `REGISTRY_HOST`、`IMAGE_NAMESPACE`、`IMAGE_TAG` 必须与导入镜像名完全一致。

```bash
docker compose run --rm backend alembic upgrade head
docker compose up -d
docker compose ps
./scripts/healthcheck.sh
```

## 注意事项

- 离线包只包含镜像，不包含数据库备份、uploads、`.env`。
- 离线更新仍必须先备份数据库和 uploads。
- 离线回滚同样只回滚应用镜像，不自动回滚数据库 schema。
