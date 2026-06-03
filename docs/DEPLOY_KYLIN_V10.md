# 企业服务中心系统麒麟 V10 服务器部署操作说明

> **文档版本**：基于当前仓库真实结构编写（审计日期：2026-05-28）  
> **适用系统**：麒麟 V10（政务/单位内网）  
> **部署方式**：非 Docker 为主（当前仓库**未发现** Dockerfile、Nginx 配置、systemd 单元文件，下文提供可参考模板）

---

## 审计摘要（实施前必读）

| 审计项 | 当前项目实际情况 |
|--------|------------------|
| 仓库根目录 | `app/`、`migrations/`、`alembic.ini`、`requirements.txt`、`.env` 均在**仓库根目录**（无单独 `backend/` 子目录） |
| 后端入口 | `app/main.py` → **`uvicorn app.main:app`** |
| 健康检查 | `GET /api/health`（`app/main.py`）；另有 `GET /api/common/health` |
| API 前缀 | `/api/auth`、`/api/enterprise`、`/api/admin`、`/api/common` |
| 附件上传 | `POST /api/common/attachments/upload` |
| 附件下载 | `GET /api/common/attachments/{attachment_id}/download` |
| 上传物理目录 | `{UPLOAD_DIR}/attachments/`（默认 `{项目根}/uploads/attachments/`） |
| 环境变量模板 | 根目录 `.env.example`（共 11 项，**无** mock 开关、**无** CORS 环境变量） |
| CORS | **写死在** `app/main.py`，仅允许 localhost/127.0.0.1 及 `10.*.*.*:5173-5175` |
| Mock 登录 | `POST /api/auth/enterprise/mock-login`、`POST /api/auth/admin/mock-login`（**无**统一关闭开关） |
| admin-web 构建 | `npm run build` → 产物目录 **`admin-web/dist/`** |
| enterprise-h5 构建 | `npm run build` → 产物目录 **`enterprise-h5/dist/`** |
| 初始化脚本 | `scripts/init_dict.py`、`scripts/init_demo_data.py`、`scripts/test_api_flow.py` |
| uploads 权限风险 | 开发环境实测 `uploads/` 属主为 **root:root**，后端若以 `esc` 用户运行将**无法写入** |

---

## 1. 部署目标

在麒麟 V10 内网服务器上部署「企业服务中心系统」，实现：

1. 后端 FastAPI 通过 **systemd** 常驻运行，仅监听本机 `127.0.0.1:8000`；
2. 管理端 **admin-web**、企业端 **enterprise-h5** 静态资源由 **Nginx** 提供；
3. 对外统一通过 Nginx 反向代理 `/api/` 访问后端；
4. 附件目录 **uploads** 独立持久化，运行用户可写；
5. 企业端 H5 配置到微信公众号菜单；
6. **生产环境**关闭 Mock 登录，接入省级统一身份认证（企业端）与政务服务平台统一用户体系（管理端）。

---

## 2. 系统组成

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| 后端 | Python 3.11+、FastAPI 0.111、SQLAlchemy 2.0、Alembic | 仓库根目录即后端根目录 |
| 管理端 | Vue 3 + Vite 5 + Element Plus | 目录 `admin-web/`，默认开发端口 **5173** |
| 企业端 H5 | Vue 3 + Vite 5 + Vant 4 | 目录 `enterprise-h5/`，默认开发端口 **5174** |
| 数据库 | MySQL 8（开发）；生产可用 MySQL 8 或兼容国产库/瀚高 | 连接串由 `.env` 配置 |
| 认证 | JWT（HS256） | 企业端/管理端双 token，密钥 `APP_SECRET_KEY` |

---

## 3. 服务器环境要求

### 3.1 操作系统与基础软件

| 项目 | 建议值 | 说明 |
|------|--------|------|
| 操作系统 | 麒麟 V10 | 以单位镜像为准 |
| Python | **3.11+**（建议 3.11 或 3.12） | README 要求 3.11+；开发环境实测 3.12.3 |
| Node.js | **18 LTS+**（建议 18 或 20） | 用于前端构建；开发环境实测 v20.18.2 |
| npm | 随 Node 安装 | 构建 admin-web / enterprise-h5 |
| Nginx | 1.18+ | 静态资源 + 反向代理 |
| MySQL | 8.0+ 或兼容实例 | 字符集 **utf8mb4** |
| systemd | 系统自带 | 管理后端进程 |
| Git | 可选 | 拉取代码 |
| chrony/ntp | 建议启用 | 时间同步影响 JWT、日志 |

### 3.2 网络与存储

| 项目 | 说明 |
|------|------|
| 监听端口 | Nginx **80/443**（对外）；后端 **8000**（仅本机） |
| 防火墙 | 仅开放必要端口；数据库端口不对公网暴露 |
| 域名/IP | 使用占位符 `your-domain-or-ip` 替换 |
| 上传存储 | 预留足够空间；`uploads` 与数据库均需备份 |
| 日志 | `/opt/enterprise-service-center/logs/` |

### 3.3 编译依赖（麒麟常见）

安装 Python 依赖若编译失败，可安装（包名以麒麟 yum 源为准）：

```bash
# 示例，按实际源调整
sudo yum install -y gcc python3-devel openssl-devel libffi-devel
```

---

## 4. 部署目录规划

建议统一部署根目录：

```text
/opt/enterprise-service-center/
├── backend/                 # 后端：app、migrations、alembic.ini、requirements.txt、.env
│   └── scripts/             # 可与根级 scripts 合并；下文命令假定 init 脚本在此
├── admin-web/               # 管理端源码；构建产物 dist/
├── enterprise-h5/           # 企业端源码；构建产物 dist/
├── uploads/                 # 附件持久化（与 backend 分离，通过 UPLOAD_DIR 指向）
├── logs/                    # Nginx / 应用日志
├── backup/                  # 数据库与 uploads 备份
└── scripts/                 # 可选：部署/备份脚本（与仓库 scripts/ 对应）
```

**与 Git 仓库的对应关系**：

当前克隆下来的仓库根目录**就是后端根目录**（含 `app/`）。部署时有两种做法：

- **做法 A（推荐）**：将整个仓库放到 `/opt/enterprise-service-center/`，将 `app`、`migrations`、`alembic.ini`、`requirements.txt`、`.env` 视为 `backend` 逻辑目录，systemd 的 `WorkingDirectory` 指向 `/opt/enterprise-service-center`（即后端根）。
- **做法 B**：仅将后端相关文件拷贝到 `/opt/enterprise-service-center/backend/`，`WorkingDirectory=/opt/enterprise-service-center/backend`。

下文命令以 **做法 A** 为例（`WorkingDirectory=/opt/enterprise-service-center`）。若采用做法 B，请将所有路径中的该目录替换为 `.../backend`。

---

## 5. 依赖软件安装

### 5.1 MySQL 客户端与 Server

按单位规范安装 MySQL 8 或连接现有数据库实例，确保可从应用服务器访问 `DB_HOST:DB_PORT`。

### 5.2 Python 虚拟环境

```bash
cd /opt/enterprise-service-center
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` 当前包含（节选）：`fastapi==0.111.0`、`uvicorn[standard]==0.29.0`、`sqlalchemy==2.0.30`、`pymysql==1.1.1`、`alembic==1.13.1`、`python-jose`、`passlib`、`python-multipart`、`python-dotenv` 等。

### 5.3 Node.js（构建机或服务器）

```bash
node -v    # 建议 v18+
npm -v
```

---

## 6. 数据库准备

### 6.1 创建库与用户

```sql
CREATE DATABASE enterprise_service_center
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'esc_user'@'应用服务器内网IP' IDENTIFIED BY '请替换为强密码';

GRANT ALL PRIVILEGES ON enterprise_service_center.* TO 'esc_user'@'应用服务器内网IP';

FLUSH PRIVILEGES;
```

> **生产注意**：不建议长期使用 `'esc_user'@'%'`；应按应用服务器 IP 限制来源。  
> 若使用瀚高/其他兼容库，由 DBA 提供等价建库语句，`.env` 中连接参数以 DBA 为准（当前代码使用 `mysql+pymysql` 驱动）。

### 6.2 连接配置项（写入 `.env`）

| 变量 | 说明 | 示例 |
|------|------|------|
| `DB_HOST` | 数据库地址 | `192.168.x.x` |
| `DB_PORT` | 端口 | `3306` |
| `DB_NAME` | 库名 | `enterprise_service_center` |
| `DB_USER` | 业务账号 | `esc_user` |
| `DB_PASSWORD` | 密码 | `请替换` |
| `DB_ECHO` | SQL 日志 | 生产 `false` |

---

## 7. 后端部署

### 7.1 获取代码

```bash
sudo mkdir -p /opt/enterprise-service-center
sudo chown -R esc:esc /opt/enterprise-service-center   # 见第 8 节创建用户

# 示例：git 拉取（按单位镜像源调整）
cd /opt/enterprise-service-center
git clone <仓库地址> .
# 或 rsync/scp 上传压缩包后解压
```

### 7.2 配置环境变量

```bash
cd /opt/enterprise-service-center
cp .env.example .env
chmod 600 .env
```

编辑 `.env`（**必须修改**占位项）：

```ini
APP_ENV=production
APP_SECRET_KEY=请替换为足够长的随机密钥

DB_HOST=请替换
DB_PORT=3306
DB_USER=esc_user
DB_PASSWORD=请替换
DB_NAME=enterprise_service_center
DB_ECHO=false

JWT_ALGORITHM=HS256
JWT_ENTERPRISE_EXPIRE_MINUTES=720
JWT_ADMIN_EXPIRE_MINUTES=480

UPLOAD_DIR=/opt/enterprise-service-center/uploads
MAX_UPLOAD_SIZE=10485760
```

说明：

- `UPLOAD_DIR` 建议使用**绝对路径**（见第 9 章）。
- `MAX_UPLOAD_SIZE` 当前默认 **10485760**（10MB）；与 Nginx `client_max_body_size` 配合调整。
- **当前项目未发现**：`ENABLE_MOCK_LOGIN`、日志目录、前端地址等环境变量；生产 CORS 需改代码（见 7.5）。

### 7.3 数据库迁移

```bash
cd /opt/enterprise-service-center
source .venv/bin/activate

# Alembic 从 app.core.config 读取 database_url，无需改 alembic.ini 中的 sqlalchemy.url
alembic upgrade head
```

当前已有迁移版本（`migrations/versions/`）包括：`001`～`007` 等，执行 `head` 即可到最新。

### 7.4 初始化字典与演示数据

**字典（生产必须）**：

```bash
cd /opt/enterprise-service-center
source .venv/bin/activate
python scripts/init_dict.py
```

脚本说明：可重复执行，已存在记录会跳过（见 `scripts/init_dict.py` 文件头注释）。

**演示数据（仅测试环境）**：

```bash
python scripts/init_demo_data.py
```

> **生产环境**：**不建议**执行 `init_demo_data.py`，避免导入演示会议室、演示企业等测试数据。

### 7.5 生产 CORS 配置（必做）

当前 CORS **未**从 `.env` 读取，写死在 `app/main.py`：

```python
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # ... 5174、5175 ...
],
allow_origin_regex=r"http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}:517[3-5]",
```

**生产部署**在前后端**同域**且 API 走 Nginx `/api/` 代理时，浏览器为同源请求，一般**不触发 CORS**。  
若管理端/企业端使用**独立域名**访问 API，必须在发版前修改 `app/main.py`，将正式前端域名加入 `allow_origins`，或后续增加环境变量配置。

> 本轮仅文档说明，**不修改业务代码**；上线前由开发发版处理。

### 7.6 启动测试

```bash
cd /opt/enterprise-service-center
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开终端健康检查：

```bash
curl -s http://127.0.0.1:8000/api/health
# 期望含 "status":"ok" 或 code=0 的统一响应结构
```

Swagger（内网按需开放）：`http://127.0.0.1:8000/docs`

---

## 8. 创建运行用户

不建议使用 root 运行后端。

```bash
# 麒麟 V10 若不支持 -r，可改为：useradd esc
sudo useradd -r -m -s /sbin/nologin esc

sudo mkdir -p /opt/enterprise-service-center/{uploads,logs,backup}
sudo chown -R esc:esc /opt/enterprise-service-center
sudo chmod -R 750 /opt/enterprise-service-center
```

代码目录归属 `esc` 后，后续 systemd 使用 `User=esc` 启动。

---

## 9. 文件上传目录配置（重点）

### 9.1 业务说明

系统附件经后端 API 写入磁盘，涉及：

1. 企业诉求附件；
2. 会议室封面/照片；
3. 会议室申请材料；
4. 政企约见申请附件；
5. 约见记录附件等。

上传接口：`POST /api/common/attachments/upload`  
下载接口：`GET /api/common/attachments/{id}/download`（**不要**用 Nginx 直接 alias 暴露 uploads 目录）。

物理路径规则（`app/api/common/router.py`）：

```text
{UPLOAD_DIR}/attachments/{uuid}.{ext}
```

`app/core/config.py` 中 `upload_dir_resolved` 会将相对路径解析为**项目根目录**下的绝对路径。

### 9.2 目录创建与授权

```bash
sudo mkdir -p /opt/enterprise-service-center/uploads/attachments
sudo chown -R esc:esc /opt/enterprise-service-center/uploads
sudo chmod -R 750 /opt/enterprise-service-center/uploads
```

`.env` 中**必须**指向该目录：

```ini
UPLOAD_DIR=/opt/enterprise-service-center/uploads
```

### 9.3 写权限验证（必做）

在 systemd 使用 `User=esc` 的前提下：

```bash
sudo -u esc touch /opt/enterprise-service-center/uploads/test.txt
sudo -u esc rm -f /opt/enterprise-service-center/uploads/test.txt
```

- **成功**：说明 `esc` 对 uploads 可写，附件上传应正常。  
- **失败**：上传接口返回 500，日志可能出现 `Permission denied`；需检查属主、属组、`chmod`、SELinux（若启用）。

### 9.4 开发环境已知的权限风险

当前开发机审计结果：`uploads/` 为 **root:root 755**，若进程以普通用户运行会写入失败。`scripts/test_api_flow.py` 曾报告 uploads 不可写。**生产务必避免** root 创建目录后未 `chown` 给 `esc`。

### 9.5 运维要点

| 要点 | 说明 |
|------|------|
| 不要放在前端 dist 内 | `admin-web/dist`、`enterprise-h5/dist` 仅静态资源 |
| 必须备份 | 与数据库同等重要 |
| 迁移服务器 | 同时迁移 DB + uploads |
| 权限 | 不要长期 `chmod 777`；排查后可恢复 750 |
| 大小与类型 | 应用层 `MAX_UPLOAD_SIZE=10MB`；Nginx 可设 `client_max_body_size 50m` |
| 启动时创建目录 | `app/main.py` lifespan 会 `makedirs(upload_dir_resolved)`，但**无写权限仍会失败** |

---

## 10. 数据库迁移

（与 7.3 相同，生产发版流程可重复执行）

```bash
cd /opt/enterprise-service-center
source .venv/bin/activate
alembic upgrade head
```

回滚（谨慎，需 DBA 确认）：

```bash
alembic downgrade -1
```

---

## 11. 初始化字典和基础数据

| 脚本 | 命令 | 环境 |
|------|------|------|
| 字典 | `python scripts/init_dict.py` | **生产必须** |
| 演示数据 | `python scripts/init_demo_data.py` | **仅测试** |
| API 流程测试 | `BASE_URL=http://127.0.0.1:8000 .venv/bin/python scripts/test_api_flow.py` | 测试（需 `pip install requests`） |

---

## 12. 后端 systemd 服务配置

仓库内**无**现成 unit 文件，新建：

`/etc/systemd/system/enterprise-service-center.service`

```ini
[Unit]
Description=Enterprise Service Center Backend (FastAPI)
After=network.target mysqld.service
Wants=mysqld.service

[Service]
Type=simple
User=esc
Group=esc
WorkingDirectory=/opt/enterprise-service-center
EnvironmentFile=/opt/enterprise-service-center/.env
ExecStart=/opt/enterprise-service-center/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
# 可选：限制打开文件数
# LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

启用与管理：

```bash
sudo systemctl daemon-reload
sudo systemctl enable enterprise-service-center
sudo systemctl start enterprise-service-center
sudo systemctl status enterprise-service-center
```

---

## 13. admin-web 管理端构建与部署

### 13.1 构建

```bash
cd /opt/enterprise-service-center/admin-web
npm install
npm run build
```

- **构建命令**（`package.json`）：`vue-tsc && vite build`  
- **产物目录**：`admin-web/dist/`  
- **开发端口**：5173（`vite.config.ts`）

### 13.2 生产环境变量

复制并编辑（仓库已有 `admin-web/.env.production`）：

```bash
cd /opt/enterprise-service-center/admin-web
cat > .env.production <<'EOF'
# 与 Nginx 同域且 /api 反向代理时，可留空使用相对路径
VITE_API_BASE_URL=
VITE_APP_TITLE=企业服务中心管理端
EOF
```

| 场景 | `VITE_API_BASE_URL` |
|------|---------------------|
| Nginx 同域 `/api` 代理 | **留空**（推荐，与 `admin-web/.env.development` 一致） |
| API 独立域名 | `https://api.your-domain.com` 或 `http://内网IP` |

> 修改 `.env.production` 后必须重新 `npm run build`。

### 13.3 部署静态文件

```bash
# 示例：仅部署 dist
sudo mkdir -p /opt/enterprise-service-center/admin-web/dist
sudo cp -r /opt/enterprise-service-center/admin-web/dist/* \
  /opt/enterprise-service-center/admin-web/dist/
sudo chown -R esc:esc /opt/enterprise-service-center/admin-web/dist
```

---

## 14. enterprise-h5 企业端构建与部署

### 14.1 构建

```bash
cd /opt/enterprise-service-center/enterprise-h5
npm install
```

创建生产环境变量（仓库**仅有** `.env.development`，生产需新建）：

```bash
cat > .env.production <<'EOF'
# 与 Nginx 同域时推荐留空；微信菜单使用 https 域名时也可写完整地址
VITE_API_BASE_URL=
VITE_APP_TITLE=企业服务中心
EOF
```

```bash
npm run build
```

- **构建命令**：`vue-tsc -b && vite build`  
- **产物目录**：`enterprise-h5/dist/`  
- **开发端口**：5174（`vite.config.ts`，`strictPort: false`）

### 14.2 附件/封面 URL

企业端 `src/utils/api.ts` 会将相对路径拼接到 `VITE_API_BASE_URL`。生产同域留空时，封面与下载链接走当前站点 `/api/...`，与 Nginx 配置一致。

---

## 15. Nginx 配置

仓库内**无**现成 Nginx 配置。以下为可参考模板（需替换 `your-domain-or-ip`）。

### 15.1 方案 A：同域名 + 子路径（需注意 Vite base）

当前 `admin-web/vite.config.ts`、`enterprise-h5/vite.config.ts` **未设置** `base`，默认为 `/`。  
若使用 `/admin/`、`/h5/` 子路径部署，**必须**修改配置后重新构建：

```ts
// admin-web/vite.config.ts
export default defineConfig({
  base: '/admin/',
  // ...
})

// enterprise-h5/vite.config.ts
export default defineConfig({
  base: '/h5/',
  // ...
})
```

并修改路由 history base（`createWebHistory('/admin/')` 等），否则静态资源 404。

**子路径 Nginx 示例**：

```nginx
server {
    listen 80;
    server_name your-domain-or-ip;

    client_max_body_size 50m;

    access_log /opt/enterprise-service-center/logs/nginx_access.log;
    error_log  /opt/enterprise-service-center/logs/nginx_error.log;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        alias /opt/enterprise-service-center/admin-web/dist/;
        try_files $uri $uri/ /admin/index.html;
    }

    location /h5/ {
        alias /opt/enterprise-service-center/enterprise-h5/dist/;
        try_files $uri $uri/ /h5/index.html;
    }
}
```

### 15.2 方案 B：独立域名或根路径（推荐，改动最小）

不修改 Vite `base`，分别为管理端、企业端配置虚拟主机或不同端口：

| 站点 | 根目录 | 示例 URL |
|------|--------|----------|
| 管理端 | `admin-web/dist` | `http://admin.your-domain.com/` |
| 企业端 | `enterprise-h5/dist` | `https://h5.your-domain.com/` |
| API | 反代到 8000 | 两站点均代理 `location /api/` |

**企业端 server 示例（根路径）**：

```nginx
server {
    listen 443 ssl;
    server_name h5.your-domain.com;

    client_max_body_size 50m;
    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    root /opt/enterprise-service-center/enterprise-h5/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**管理端**同理，`root` 指向 `admin-web/dist`。

加载配置：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 16. 微信公众号菜单地址配置

企业端路由（`enterprise-h5/src/router/index.ts`）与菜单对应关系见 `docs/WECHAT_MENU_CONFIG.md`。

### 16.1 菜单结构

| 层级 | 名称 |
|------|------|
| 主菜单 | 企业服务 |
| 子菜单 1 | 企业诉求 |
| 子菜单 2 | 共享会议室 |
| 子菜单 3 | 政企约见 |

类型：**view**（跳转网页）。

### 16.2 正式环境 URL 示例

**方案 B（企业端独占域名，根路径部署）**——推荐：

| 子菜单 | URL |
|--------|-----|
| 企业诉求 | `https://h5.your-domain.com/appeals` |
| 共享会议室 | `https://h5.your-domain.com/meeting-rooms` |
| 政企约见 | `https://h5.your-domain.com/gov-meetings/notice` |

**方案 A（子路径 `/h5/`）**：

| 子菜单 | URL |
|--------|-----|
| 企业诉求 | `https://your-domain-or-ip/h5/appeals` |
| 共享会议室 | `https://your-domain-or-ip/h5/meeting-rooms` |
| 政企约见 | `https://your-domain-or-ip/h5/gov-meetings/notice` |

### 16.3 登录与回跳

| 环境 | 行为 |
|------|------|
| 当前测试 | Mock 登录 `/login`；未登录访问业务页 → `/login?redirect=<原路径>`，登录后回跳**原菜单页**（非强制 `/home`） |
| 正式生产 | 须接入**省级统一身份认证**；关闭 Mock；菜单直链应跳转统一认证后再回到 `redirect` 目标 |

---

## 17. 启动与访问验证

### 17.1 后端

```bash
curl -s http://127.0.0.1:8000/api/health
sudo systemctl status enterprise-service-center
```

### 17.2 经 Nginx

```bash
curl -s http://your-domain-or-ip/api/health
```

### 17.3 前端页面

| 端 | 方案 A | 方案 B |
|----|--------|--------|
| 管理端 | `http://your-domain-or-ip/admin/` | `http://admin.your-domain.com/` |
| 企业端 | `http://your-domain-or-ip/h5/` | `https://h5.your-domain.com/` |

### 17.4 附件上传验证

1. 登录企业端或管理端；  
2. 上传会议室照片或申请材料；  
3. 检查目录：

```bash
ls -la /opt/enterprise-service-center/uploads/attachments/
```

4. 页面预览/下载是否正常（走 `/api/common/attachments/{id}/download`）。

### 17.5 微信公众号菜单

用手机微信打开三个菜单 URL，确认：

- 未登录 → 跳转登录（当前为 Mock `/login`）；  
- 登录后 → 进入对应列表/须知页，而非错误首页。

### 17.6 API 测试脚本（可选）

```bash
cd /opt/enterprise-service-center
source .venv/bin/activate
pip install requests
BASE_URL=http://127.0.0.1:8000 python scripts/test_api_flow.py
```

---

## 18. 日志查看

| 类型 | 命令/路径 |
|------|-----------|
| 后端 systemd | `journalctl -u enterprise-service-center -f` |
| Nginx 访问 | `tail -f /opt/enterprise-service-center/logs/nginx_access.log` |
| Nginx 错误 | `tail -f /opt/enterprise-service-center/logs/nginx_error.log` |
| Alembic | 执行迁移时的终端输出 |
| 前端构建 | `npm run build` 终端输出 |

当前后端**未发现**独立应用日志目录环境变量；业务日志主要依赖 systemd journal。

---

## 19. 服务重启、停止、开机自启

```bash
sudo systemctl restart enterprise-service-center
sudo systemctl stop enterprise-service-center
sudo systemctl start enterprise-service-center
sudo systemctl enable enterprise-service-center

sudo systemctl reload nginx
```

---

## 20. 常见问题排查

### 20.1 后端启动失败

- 检查 `.env` 数据库连接、`systemctl status` 与 `journalctl -u enterprise-service-center -n 100`  
- 确认 `WorkingDirectory` 为后端根目录（含 `app/`）  
- 确认 `.venv/bin/uvicorn` 路径正确  

### 20.2 数据库连接失败

- `mysql -h DB_HOST -u esc_user -p` 是否可连  
- 防火墙与 `esc_user` 授权主机是否匹配  

### 20.3 Alembic 迁移失败

- 数据库是否已创建、账号是否有 DDL 权限  
- `alembic current` / `alembic history` 查看版本  

### 20.4 Nginx 404 / 前端刷新 404

- SPA 是否配置 `try_files ... /index.html`  
- 子路径部署是否已设置 Vite `base` 与 `createWebHistory(base)`  

### 20.5 静态资源 404

- 浏览器开发者工具查看 JS/CSS 请求路径是否缺少 `/admin/` 或 `/h5/` 前缀  

### 20.6 API 502

- 后端是否监听 `127.0.0.1:8000`  
- `proxy_pass` 是否以 `/api/` 结尾并与 location 匹配  

### 20.7 跨域（CORS）

- 同域 + `/api` 代理一般无跨域  
- 跨域时检查 `app/main.py` 的 `allow_origins` 是否包含前端源  

### 20.8 文件上传失败 / uploads 权限不足（重点）

| 现象 | 可能原因 |
|------|----------|
| 上传接口 500 | 目录不存在、无写权限、磁盘满 |
| 日志 `Permission denied` | `uploads` 属主为 root，与 systemd `User=esc` 不一致 |
| `文件保存失败` | `UPLOAD_DIR` 配置错误或路径不可写 |

**处理步骤**：

1. 检查 `.env` 中 `UPLOAD_DIR`；  
2. `ls -la /opt/enterprise-service-center/uploads`；  
3. `systemctl show enterprise-service-center -p User`；  
4. `sudo chown -R esc:esc .../uploads`；  
5. `sudo -u esc touch .../uploads/test.txt` 验证。  

### 20.9 附件下载 404

- 数据库 `storage_path` 指向的文件是否仍在；  
- 迁移服务器后是否同步 uploads；  
- 勿只部署 dist 不部署 uploads  

### 20.10 登录 401

- Token 是否过期（企业端默认 720 分钟）；  
- `APP_SECRET_KEY` 变更会导致旧 token 失效  

### 20.11 Mock 登录在生产环境

- **禁止**对公网开放 `/login` Mock 页与 mock-login 接口（见第 21 节）  

### 20.12 微信菜单空白

- 企业端域名是否 HTTPS（微信要求）；  
- `VITE_API_BASE_URL` 生产构建是否正确；  
- 是否 404 或 API 不可达  

### 20.13 端口占用

```bash
ss -lntp | grep 8000
```

### 20.14 pip / npm 失败

- 麒麟缺少 `gcc`、`python3-devel`；Node 版本过低无法构建 Vite 5  

---

## 21. Mock 登录与统一身份认证切换说明

### 21.1 当前测试能力（代码已实现）

| 端 | 页面/接口 | 路径 |
|----|-----------|------|
| 企业端 Mock 页 | `enterprise-h5` → `/login`（`MockLogin.vue`） | 前端路由 |
| 企业端 Mock 接口 | `POST /api/auth/enterprise/mock-login` | `app/api/auth/router.py` |
| 管理端 Mock 页 | `admin-web` → `/login` | 前端路由 |
| 管理端 Mock 接口 | `POST /api/auth/admin/mock-login` | `app/api/auth/router.py` |

认证适配预留：`app/services/auth_adapter.py`（当前为 `MockAuthAdapter`）。

### 21.2 生产环境必须完成的事项

1. **禁用或隐藏**企业端 Mock 登录页（`/login`）；  
2. **禁用或限制** `POST /api/auth/enterprise/mock-login`（网关或代码层）；  
3. **禁用或限制** `POST /api/auth/admin/mock-login`；  
4. 企业端接入**省级统一身份认证**；  
5. 管理端接入**政务服务平台统一用户体系**；  
6. 确认 `redirect` 回跳：菜单直链进入 → 认证 → 回到原路径（如 `/appeals`），**不应强制仅回 `/home`**；  
7. 微信公众号菜单入口在认证后能正常进入业务页。  

### 21.3 配置项说明

> **当前项目未发现**统一的 `ENABLE_MOCK_LOGIN` 环境变量。  
> **建议后续增加**例如 `ENABLE_MOCK_LOGIN=false`，并在 `app/api/auth/router.py` 与前端路由守卫中读取；生产部署前需开发发版配合。

在开关未实现前，生产可采取：

- Nginx 对 `/api/auth/*/mock-login` 返回 403；  
- 不部署企业端 `/login` 相关入口（需构建时移除或路由拦截，依赖发版）；  
- 仅内网 IP 白名单访问管理端。

---

## 22. 备份与恢复建议

### 22.1 数据库

```bash
mysqldump -h 请替换DB_HOST -u esc_user -p enterprise_service_center \
  > /opt/enterprise-service-center/backup/esc_$(date +%F).sql
```

### 22.2 uploads

```bash
tar -czf /opt/enterprise-service-center/backup/uploads_$(date +%F).tar.gz \
  -C /opt/enterprise-service-center uploads
```

### 22.3 配置与编排

定期备份：

- `/opt/enterprise-service-center/.env`  
- `/etc/nginx/conf.d/` 中相关 server 配置  
- `/etc/systemd/system/enterprise-service-center.service`  

### 22.4 发版与回滚

- 发版前：数据库 + uploads + `.env` 备份；  
- 回滚：恢复上一版 `dist`、降级 Alembic（需评估）、恢复 uploads 快照。  

---

## 23. 安全加固建议

1. 不使用 root 运行后端（使用 `esc`）；  
2. 数据库不使用 root 业务账号；  
3. **必须**更换 `APP_SECRET_KEY`；  
4. `.env` 权限 `600`，勿提交 Git；  
5. 限制数据库访问来源 IP；  
6. `uploads` 目录 750，属主 `esc`；  
7. 应用层 `MAX_UPLOAD_SIZE` 与 Nginx `client_max_body_size` 协调；  
8. 上传类型在业务代码中校验（按现有接口逻辑）；  
9. Nginx **不**直接 `alias` 暴露 uploads；  
10. 日志避免输出身份证号、手机号明文；  
11. **生产关闭 Mock 登录**；  
12. 定期备份数据库与附件；  
13. 防火墙仅开放 80/443；  
14. 对外启用 **HTTPS**（微信菜单强烈建议）。  

---

## 24. 上线前检查清单

- [ ] 后端 systemd 已 `enable` 且 `active (running)`  
- [ ] `alembic upgrade head` 已执行  
- [ ] `python scripts/init_dict.py` 已执行  
- [ ] **未**在生产执行 `init_demo_data.py`（除非明确需要）  
- [ ] `uploads` 目录存在且 `UPLOAD_DIR` 为绝对路径  
- [ ] `sudo -u esc touch` uploads 验证通过  
- [ ] `APP_SECRET_KEY`、数据库密码已更换  
- [ ] admin-web、`enterprise-h5` 已 `npm run build` 并部署 dist  
- [ ] Nginx `nginx -t` 通过且已 reload  
- [ ] `curl http://127.0.0.1:8000/api/health` 正常  
- [ ] `curl http://your-domain-or-ip/api/health` 正常  
- [ ] 管理端页面可访问、可登录（测试或正式认证）  
- [ ] 企业端页面可访问  
- [ ] 微信菜单三个 URL 可打开且回跳正确  
- [ ] 附件上传、下载验证通过  
- [ ] 生产 Mock 登录已关闭或已限制（接口 + 页面）  
- [ ] 统一身份认证已接入，或文档化仍为测试环境  
- [ ] CORS / 跨域方案已按部署方式处理（改 `main.py` 或同域代理）  
- [ ] 数据库与 uploads 备份策略已建立  

---

## 25. 仍需人工确认的部署参数清单

| 参数 | 说明 |
|------|------|
| `your-domain-or-ip` | 对公网/内网访问域名或 IP |
| 企业端 HTTPS 证书 | 微信公众号要求 |
| `DB_HOST` / `DB_PORT` / 账号密码 | 由 DBA 提供 |
| 数据库类型 | MySQL 8 或兼容库驱动是否需调整 |
| `APP_SECRET_KEY` | 生产随机强密钥 |
| `UPLOAD_DIR` | 建议 `/opt/enterprise-service-center/uploads` |
| Nginx 方案 | A 子路径（改 Vite base）或 B 独立域名（推荐） |
| `VITE_API_BASE_URL` | 同域留空；跨域写完整 API 根地址 |
| systemd `WorkingDirectory` | 后端根目录（含 `app/` 的目录） |
| CORS `allow_origins` | 跨域时需改 `app/main.py` 并发版 |
| Mock 关闭方式 | 暂靠 Nginx/发版；无环境变量开关 |
| 统一身份认证对接参数 | 由省级平台、政务平台提供 |
| 防火墙与 SELinux | 是否放行 Nginx、MySQL、本地 8000 |
| 备份保留周期与异地策略 | 单位运维规范 |

---

## 附录 A：API 路由一览（便于 Nginx 与联调）

| 模块 | 前缀 |
|------|------|
| 认证 | `/api/auth` |
| 企业端 | `/api/enterprise` |
| 管理端 | `/api/admin` |
| 通用（字典、附件） | `/api/common` |

常用接口：

- `GET /api/health`  
- `POST /api/auth/enterprise/mock-login`  
- `POST /api/auth/admin/mock-login`  
- `POST /api/common/attachments/upload`  
- `GET /api/common/attachments/{id}/download`  

---

## 附录 B：Docker 可选方案

当前仓库**无** Dockerfile。若单位要求容器化，需自行编写镜像，并**单独挂载** `uploads` 卷、注入 `.env`、配置数据库网络。非本文默认路径。

---

## 附录 C：相关文档

- `docs/WECHAT_MENU_CONFIG.md` — 微信公众号菜单与 redirect  
- `docs/FULL_FLOW_TEST_REPORT.md` — 全流程测试记录  
- `docs/API_TESTING.md` — API 测试说明  
- `README.md` — 后端快速开始与 mock 登录示例  

---

*文档结束。实施过程中若仓库结构或配置项发生变化，请以实际代码与 `.env.example` 为准同步更新本文档。*
