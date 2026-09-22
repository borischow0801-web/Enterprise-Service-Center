# 麒麟 V10 生产部署操作手册

本手册面向现场实施人员。生产为两台服务器：应用服务器运行 Docker / Docker Compose / Nginx / FastAPI / 前端静态资源；数据库服务器直接安装 MySQL 8，不进入 Docker。

## 1. 部署架构

- 应用服务器：`<APP_SERVER_IP>`，麒麟 Linux Advanced Server V10，开放 HTTP/HTTPS，对内访问数据库服务器 3306。
- 数据库服务器：`<DB_SERVER_IP>`，麒麟 Linux Advanced Server V10，安装 MySQL 8，仅允许应用服务器访问 3306。
- 容器：`backend`、`nginx`。
- 路由：企业端 `/`，管理端 `/admin/`，后端 `/api/`。

## 2. 部署前信息收集表

| 项目 | 现场填写 |
|---|---|
| APP_SERVER_IP | `<APP_SERVER_IP>` |
| DB_SERVER_IP | `<DB_SERVER_IP>` |
| 域名 | `<DOMAIN>` |
| 数据库名 | `enterprise_service_center` |
| 数据库用户 | `esc_app` |
| 数据库密码 | `<DB_PASSWORD>` |
| Registry 地址 | `<REGISTRY_HOST>` |
| 镜像命名空间 | `<IMAGE_NAMESPACE>` |
| 镜像版本 | `<IMAGE_TAG>` |
| CORS Origin | `https://<DOMAIN>` |
| APP_SECRET_KEY | 使用 `openssl rand -base64 48` 生成 |
| BSPPLUS_API_ROOT | 由统一身份平台负责人提供（管理端登录依赖，生产启动前必须非空） |
| BSPPLUS_APP_CODE | 由统一身份平台负责人提供（管理端登录依赖，生产启动前必须非空） |

## 3. 应用服务器系统检查

```bash
cat /etc/os-release
uname -a
hostname -I
df -h
free -h
ip addr
ping -c 4 <DB_SERVER_IP>
```

检查时间和时区：

```bash
timedatectl
```

建议设置为上海时区：

```bash
sudo timedatectl set-timezone Asia/Shanghai
```

## 4. 数据库服务器系统检查

```bash
cat /etc/os-release
uname -a
hostname -I
df -h
free -h
ip addr
ping -c 4 <APP_SERVER_IP>
timedatectl
```

## 5. MySQL 8 安装

麒麟 V10 的软件源配置可能因现场环境不同而不同。先检查是否已有 MySQL 8 包：

```bash
sudo dnf repolist
sudo dnf module list mysql || true
sudo dnf info mysql-server || true
```

若现场仓库提供 MySQL 8：

```bash
sudo dnf install -y mysql-server
mysql --version
sudo systemctl enable --now mysqld
sudo systemctl status mysqld
```

若现场使用单位标准 MySQL 8 RPM 源，按单位源配置后再执行上面安装命令。不要安装 MariaDB 替代 MySQL 8，除非业务方重新验收兼容性。

## 6. MySQL 初始化和安全配置

```bash
sudo mysql_secure_installation
```

检查服务：

```bash
sudo systemctl status mysqld
sudo journalctl -u mysqld -n 100 --no-pager
```

确认字符集建议值：

```sql
SHOW VARIABLES LIKE 'character_set_server';
SHOW VARIABLES LIKE 'collation_server';
SHOW VARIABLES LIKE 'time_zone';
```

如需配置，编辑 MySQL 配置文件（路径以现场为准，常见为 `/etc/my.cnf` 或 `/etc/my.cnf.d/mysql-server.cnf`）：

```ini
[mysqld]
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
default-time-zone='+08:00'
bind-address=0.0.0.0
```

重启：

```bash
sudo systemctl restart mysqld
```

## 7. 创建数据库

```bash
mysql -uroot -p
```

```sql
CREATE DATABASE enterprise_service_center CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 8. 创建应用数据库用户

不要使用 root 作为应用用户。将 `<APP_SERVER_IP>` 替换为应用服务器 IP：

```sql
CREATE USER 'esc_app'@'<APP_SERVER_IP>' IDENTIFIED BY '<DB_PASSWORD>';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES ON enterprise_service_center.* TO 'esc_app'@'<APP_SERVER_IP>';
FLUSH PRIVILEGES;
```

最小权限说明：运行期主要需要 DML；首次迁移和后续 Alembic 需要 DDL。若单位要求运行期和迁移账户分离，可另建迁移账户，仅在发布时使用。

## 9. 配置远程访问

检查监听：

```bash
sudo ss -ltnp | grep 3306
```

应看到 MySQL 监听 `0.0.0.0:3306` 或 `<DB_SERVER_IP>:3306`。若只监听 `127.0.0.1:3306`，检查 `bind-address`。

## 10. firewalld

数据库服务器只允许应用服务器访问 3306，不要关闭整个 firewalld：

```bash
sudo systemctl enable --now firewalld
sudo firewall-cmd --state
sudo firewall-cmd --permanent --new-zone=esc-app || true
sudo firewall-cmd --permanent --zone=esc-app --add-source=<APP_SERVER_IP>/32
sudo firewall-cmd --permanent --zone=esc-app --add-port=3306/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --zone=esc-app --list-all
```

应用服务器开放 HTTP，如有 HTTPS 也开放 443：

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 11. 应用服务器安装 Docker

优先使用单位批准的软件源。检查：

```bash
sudo dnf info docker-ce || true
sudo dnf info docker || true
```

安装示例：

```bash
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

若仓库包名为 `docker`，按现场源实际包名安装，但必须确认 Docker Engine 和 Compose Plugin 可用。

## 12. 安装 Docker Compose Plugin

```bash
docker compose version
```

如果没有该命令，安装插件包：

```bash
sudo dnf install -y docker-compose-plugin
```

## 13. Docker 开机启动

```bash
sudo systemctl enable --now docker
sudo systemctl status docker
```

## 14. 创建生产目录

```bash
sudo mkdir -p /opt/enterprise-center
sudo mkdir -p /data/enterprise-center/uploads/attachments
sudo chown -R root:root /opt/enterprise-center
sudo chmod 755 /opt/enterprise-center
sudo chmod -R 750 /data/enterprise-center/uploads
```

uploads 目录通过 bind mount 给容器内 UID 10001 用户写入。设置属主：

```bash
sudo chown -R 10001:10001 /data/enterprise-center/uploads
```

SELinux 如启用，优先设置目录上下文，不要直接永久关闭 SELinux：

```bash
getenforce
sudo semanage fcontext -a -t container_file_t '/data/enterprise-center/uploads(/.*)?' || true
sudo restorecon -Rv /data/enterprise-center/uploads || true
```

如果 `semanage` 不存在，安装策略工具包后再执行，包名以现场源为准。

## 15. 获取部署文件

将仓库中的以下文件复制到应用服务器 `/opt/enterprise-center`：

```text
deploy/docker-compose.yml
deploy/.env.example
deploy/nginx/default.conf
deploy/scripts/deploy.sh
deploy/scripts/update.sh
deploy/scripts/rollback.sh
deploy/scripts/healthcheck.sh
```

生产服务器原则上不需要 Git 源代码，只需要部署文件和可拉取的镜像。

## 16. Registry 登录

```bash
cd /opt/enterprise-center
docker login <REGISTRY_HOST>
```

## 17. 创建 .env

```bash
cd /opt/enterprise-center
cp .env.example .env
vi .env
```

关键字段：

```dotenv
REGISTRY_HOST=<REGISTRY_HOST>
IMAGE_NAMESPACE=<IMAGE_NAMESPACE>
IMAGE_TAG=<IMAGE_TAG>
APP_ENV=production
APP_SECRET_KEY=<openssl rand -base64 48 的结果>
DATABASE_URL=mysql+pymysql://esc_app:<DB_PASSWORD>@<DB_SERVER_IP>:3306/enterprise_service_center?charset=utf8mb4
CORS_ALLOWED_ORIGINS=https://<DOMAIN>
UPLOAD_DIR=/data/uploads
UPLOADS_HOST_DIR=/data/enterprise-center/uploads
HTTP_PORT=80
BSPPLUS_API_ROOT=<统一身份平台提供的地址，如 http://172.29.91.36:9099>
BSPPLUS_APP_CODE=<统一身份平台提供的应用编码>
```

`.env` 不得提交 Git，不得填占位 Secret。

管理端正式登录（`POST /api/auth/admin/login`）依赖 `BSPPLUS_API_ROOT`/`BSPPLUS_APP_CODE`；
`APP_ENV=production` 时若这两项未配置，应用会在启动阶段直接报错退出（同 `APP_SECRET_KEY`
校验逻辑一致，见下方"常见故障"）。管理端账号本身（角色/区划/数据权限）在
"系统管理 → 管理员管理"里维护，登录只做身份核验，不会自动开通新管理员。

## 18. 数据库连通测试

从应用服务器测试 TCP：

```bash
nc -vz <DB_SERVER_IP> 3306 || telnet <DB_SERVER_IP> 3306
```

如已安装 mysql client：

```bash
mysql -h <DB_SERVER_IP> -P 3306 -u esc_app -p enterprise_service_center -e 'SELECT 1;'
```

## 19. 拉取镜像

```bash
cd /opt/enterprise-center
docker compose pull
```

pull 拉的是 Registry 中的镜像，不是 Git 源码。

## 20. 首次数据库迁移

```bash
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend alembic current
```

期望输出 head 为 `011_sys_daily_serial (head)` 或更新版本。migration 失败时不要继续启动新版本。

## 21. 启动系统

```bash
docker compose up -d
```

## 22. 查看状态

```bash
docker compose ps
```

backend 与 nginx 应为 running/healthy。

## 23. 查看日志

```bash
docker compose logs --tail=200 backend
docker compose logs --tail=200 nginx
docker compose logs -f nginx
```

日志轮转在 `docker-compose.yml` 中通过 `max-size`、`max-file` 控制。

## 24. Health Check

```bash
curl -fsS http://127.0.0.1/api/health
./scripts/healthcheck.sh
```

## 25. 浏览器访问

- 企业端：`http://<APP_SERVER_IP>/` 或 `https://<DOMAIN>/`
- 管理端：`http://<APP_SERVER_IP>/admin/` 或 `https://<DOMAIN>/admin/`
- API health：`http://<APP_SERVER_IP>/api/health`

## 26. 首次业务验证

最小 smoke test：

1. 企业端打开首页。
2. 企业账号登录或注册。
3. 提交一条测试诉求或预约。
4. 管理端登录。
5. 查看对应列表和详情。
6. 上传一个 PDF 附件。
7. 下载该附件。
8. 刷新管理端子路由，确认不 404。

## 27. 开机自启动验证

```bash
sudo reboot
```

重启后：

```bash
cd /opt/enterprise-center
docker compose ps
curl -fsS http://127.0.0.1/api/health
```

Docker 服务开机启动，Compose 容器因 `restart: unless-stopped` 自动恢复。

## 28. 日志检查

```bash
docker inspect enterprise-center-backend-1 2>/dev/null || true
docker compose logs --tail=100 backend
docker compose logs --tail=100 nginx
sudo du -sh /var/lib/docker/containers/* 2>/dev/null | sort -h | tail
```

## 29. 上传目录权限

```bash
ls -ld /data/enterprise-center/uploads /data/enterprise-center/uploads/attachments
docker compose exec backend sh -c 'id && test -w /data/uploads && echo writable'
```

不要使用 `chmod -R 777`。若不可写，设置：

```bash
sudo chown -R 10001:10001 /data/enterprise-center/uploads
sudo chmod -R 750 /data/enterprise-center/uploads
```

## 30. 数据备份

数据库备份：

```bash
mkdir -p /opt/enterprise-center/backup
mysqldump -h <DB_SERVER_IP> -u esc_app -p --single-transaction --routines --triggers enterprise_service_center   > /opt/enterprise-center/backup/enterprise_service_center_$(date +%F_%H%M%S).sql
```

uploads 备份：

```bash
tar -czf /opt/enterprise-center/backup/uploads_$(date +%F_%H%M%S).tar.gz -C /data/enterprise-center uploads
```

## 31. 日常更新

```bash
cd /opt/enterprise-center
# 1. 备份数据库和 uploads
# 2. 修改 IMAGE_TAG
vi .env
# 3. 拉取镜像
docker compose pull
# 4. 数据库迁移，失败则停止
docker compose run --rm backend alembic upgrade head
# 5. 重建应用
docker compose up -d
# 6. 检查
docker compose ps
./scripts/healthcheck.sh
```

## 32. 回滚

应用镜像回滚：

```bash
cd /opt/enterprise-center
./scripts/rollback.sh 1.0.0
```

或手工修改 `.env`：

```bash
sed -i 's/^IMAGE_TAG=.*/IMAGE_TAG=1.0.0/' .env
docker compose pull
docker compose up -d
./scripts/healthcheck.sh
```

重要：应用镜像回滚不等于数据库自动回滚。如果新版本执行过 migration，需要评估旧程序是否兼容新 schema。禁止在未评估时自动执行 Alembic downgrade。

## 33. 常见故障

### Docker 启动失败

检查：

```bash
sudo systemctl status docker
sudo journalctl -u docker -n 200 --no-pager
```

依据：服务 inactive/failed 或日志有配置错误。处理：按日志修复 Docker 配置或软件源安装问题后 `sudo systemctl restart docker`。

### 容器反复重启

检查：

```bash
docker compose ps
docker compose logs --tail=200 backend
docker compose logs --tail=200 nginx
```

依据：backend 常见为环境变量错误、数据库不可达、Secret 校验失败。处理：修正 `.env` 后 `docker compose up -d`。

### backend 连不上 MySQL

检查：

```bash
nc -vz <DB_SERVER_IP> 3306
docker compose logs --tail=100 backend
```

依据：超时多为网络/firewalld；拒绝多为 MySQL 未监听或防火墙拒绝。处理：检查 MySQL `bind-address`、firewalld zone、应用服务器 IP 是否正确。

### Access denied

检查：

```sql
SELECT user, host FROM mysql.user WHERE user='esc_app';
SHOW GRANTS FOR 'esc_app'@'<APP_SERVER_IP>';
```

依据：用户 host 不匹配、密码错误、权限不足。处理：修正用户 host 为应用服务器 IP，重新授权。

### Connection refused

检查：

```bash
sudo ss -ltnp | grep 3306
sudo systemctl status mysqld
```

依据：MySQL 未启动或只监听 localhost。处理：启动 MySQL，修正 `bind-address`。

### CORS

检查浏览器控制台和 `.env`：

```bash
grep CORS_ALLOWED_ORIGINS .env
```

同域 `/api` 部署一般不触发 CORS；跨域时必须填写准确 origin，如 `https://example.com`，不要写路径。

### 502 Bad Gateway

检查：

```bash
docker compose ps
docker compose logs --tail=100 nginx
docker compose logs --tail=100 backend
```

依据：backend unhealthy 或 Nginx 无法解析/连接 backend。处理：先修 backend，再重启 nginx。

### Vue 页面刷新 404

检查：

```bash
docker compose exec nginx nginx -T | grep -A8 'location /admin/'
```

依据：`try_files` 缺失或 web 镜像不是以 `/admin/` base 构建。处理：确认 web 镜像构建参数 `ADMIN_BASE_PATH=/admin/`。

### 上传 Permission denied

检查：

```bash
ls -ld /data/enterprise-center/uploads
docker compose exec backend sh -c 'id && test -w /data/uploads'
```

处理：

```bash
sudo chown -R 10001:10001 /data/enterprise-center/uploads
sudo chmod -R 750 /data/enterprise-center/uploads
```

### APP_SECRET_KEY 校验失败

检查日志若出现“APP_ENV=production 但 APP_SECRET_KEY 仍是占位/默认值或长度不足”。处理：

```bash
openssl rand -base64 48
vi .env
docker compose up -d
```

### BSPPLUS_API_ROOT / BSPPLUS_APP_CODE 校验失败

检查日志若出现“APP_ENV=production 但 BSPPLUS_API_ROOT / BSPPLUS_APP_CODE 未配置”，说明
`.env` 里这两项为空或未设置。找统一身份平台负责人拿到实际地址和应用编码后填入 `.env`
重启即可；开发/测试环境（`APP_ENV` 非 `production`）不受此校验影响。

### 管理端登录报"统一身份认证服务暂时不可用"

说明后端到 `BSPPLUS_API_ROOT` 网络不通，或 BSPPLUS 服务本身异常。可用以下脚本单独排查
（交互式输入账号密码，密码不回显、不落日志，只打印脱敏后的用户字段）：

```bash
docker compose exec backend python scripts/bspplus_login_check.py
```

若脚本本身也超时/连接失败，先确认应用服务器到 `BSPPLUS_API_ROOT` 的网络（防火墙/路由/
是否需要专线），这一步和本系统代码无关。

### migration 失败

检查：

```bash
docker compose run --rm backend alembic current
docker compose run --rm backend alembic history
```

处理：停止发布，保留日志，恢复数据库备份或修复 migration 后重新发布。不要自动 downgrade。

### Registry pull 失败

检查：

```bash
docker login <REGISTRY_HOST>
docker pull <REGISTRY_HOST>/<IMAGE_NAMESPACE>/enterprise-center-backend:<IMAGE_TAG>
```

依据：认证失败、镜像不存在、网络/DNS 问题。处理：重新登录、确认 tag 已 push、检查代理/DNS。

### 磁盘空间不足

检查：

```bash
df -h
docker system df
```

处理：先备份，再清理无用镜像：

```bash
docker image prune
```

不要删除 `/data/enterprise-center/uploads`。
