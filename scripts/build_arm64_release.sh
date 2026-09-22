#!/bin/bash

set -euo pipefail

# 必须在项目根目录执行
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

if [ $# -ne 1 ]; then
    echo "用法: $0 <版本号>"
    echo "示例: $0 1.0.1"
    exit 1
fi

VERSION="$1"

# 版本号格式校验，例如 1.0.1
if ! [[ "${VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "错误：版本号必须为 x.y.z 格式，例如 1.0.1"
    exit 1
fi

BACKEND_IMAGE="enterprise-center-backend:${VERSION}"
WEB_IMAGE="enterprise-center-web:${VERSION}"

RELEASE_DIR="${PROJECT_ROOT}/release/${VERSION}"
IMAGE_TAR="${RELEASE_DIR}/enterprise-center-${VERSION}-arm64-images.tar"
SHA_FILE="${IMAGE_TAR}.sha256"

echo "========================================"
echo "企业服务中心 ARM64 正式版本构建"
echo "版本：${VERSION}"
echo "========================================"

mkdir -p "${RELEASE_DIR}"

echo
echo "[1/4] 构建 Backend ARM64 镜像..."
docker buildx build \
    --platform linux/arm64 \
    -f Dockerfile \
    -t "${BACKEND_IMAGE}" \
    --load \
    .

echo
echo "[2/4] 构建 Web ARM64 镜像..."
docker buildx build \
    --platform linux/arm64 \
    -f Dockerfile.web \
    -t "${WEB_IMAGE}" \
    --load \
    .

echo
echo "[3/4] 检查镜像架构..."

BACKEND_ARCH=$(docker image inspect "${BACKEND_IMAGE}" --format '{{.Architecture}}')
WEB_ARCH=$(docker image inspect "${WEB_IMAGE}" --format '{{.Architecture}}')

if [ "${BACKEND_ARCH}" != "arm64" ]; then
    echo "错误：Backend 镜像架构不是 arm64，而是 ${BACKEND_ARCH}"
    exit 1
fi

if [ "${WEB_ARCH}" != "arm64" ]; then
    echo "错误：Web 镜像架构不是 arm64，而是 ${WEB_ARCH}"
    exit 1
fi

echo "Backend: ${BACKEND_ARCH}"
echo "Web:     ${WEB_ARCH}"

echo
echo "[4/4] 导出生产镜像包..."

rm -f "${IMAGE_TAR}" "${SHA_FILE}"

docker save \
    "${BACKEND_IMAGE}" \
    "${WEB_IMAGE}" \
    -o "${IMAGE_TAR}"

(
    cd "${RELEASE_DIR}"
    sha256sum "$(basename "${IMAGE_TAR}")" > "$(basename "${SHA_FILE}")"
)

echo
echo "========================================"
echo "构建完成"
echo "========================================"
echo "Backend : ${BACKEND_IMAGE}"
echo "Web     : ${WEB_IMAGE}"
echo "镜像包  : ${IMAGE_TAR}"
echo "校验文件: ${SHA_FILE}"
echo
echo "SHA256:"
cat "${SHA_FILE}"
