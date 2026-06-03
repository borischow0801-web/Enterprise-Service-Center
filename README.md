# 企业服务中心系统 - 后端

## 技术栈

- Python 3.11+
- FastAPI 0.111
- SQLAlchemy 2.0
- Alembic
- MySQL 8 (开发环境)
- JWT 认证（企业端 / 管理端双 token）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写数据库连接信息
```

### 3. 创建数据库

```sql
CREATE DATABASE enterprise_service_center CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 启动项目

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 Swagger 文档：http://localhost:8000/docs

### 5. 测试 mock 登录

企业端登录：
```bash
curl -X POST http://localhost:8000/api/auth/enterprise/mock-login \
  -H "Content-Type: application/json" \
  -d '{
    "enterpriseName": "测试企业有限公司",
    "creditCode": "91371000XXXXXXXXXX",
    "legalPersonName": "张三",
    "legalPersonIdNo": "370000000000000000",
    "legalPersonMobile": "13800000000"
  }'
```

管理端登录：
```bash
curl -X POST http://localhost:8000/api/auth/admin/mock-login \
  -H "Content-Type: application/json" \
  -d '{
    "platformUserId": "u001",
    "username": "admin",
    "realName": "管理员",
    "departmentId": "dept001",
    "departmentName": "企业服务中心",
    "regionCode": "371000",
    "regionName": "威海市",
    "roleCodes": ["CENTER_ADMIN"],
    "dataScope": "REGION"
  }'
```

获取当前企业信息（使用企业端 token）：
```bash
curl http://localhost:8000/api/enterprise/me \
  -H "Authorization: Bearer <enterprise_access_token>"
```

获取当前管理员信息（使用管理端 token）：
```bash
curl http://localhost:8000/api/admin/me \
  -H "Authorization: Bearer <admin_access_token>"
```

## 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "init"

# 执行迁移
alembic upgrade head
```

## 数据库迁移（第二阶段）

```bash
# 执行基础表迁移
alembic upgrade head

# 回滚
alembic downgrade base
```

## 初始化字典数据

```bash
python scripts/init_dict.py
```

## 验证 mock 登录写入数据库

企业端登录后查询 enterprise 表：
```sql
SELECT id, enterprise_name, credit_code, auth_source, last_login_time FROM enterprise;
```

管理端登录后查询 sys_user_snapshot 表：
```sql
SELECT id, platform_user_id, username, real_name, role_codes, last_login_time FROM sys_user_snapshot;
```

## 项目结构

```
app/
  main.py                  # FastAPI 应用入口
  core/
    config.py              # 配置（读取 .env）
    database.py            # SQLAlchemy 引擎 & Session
    security.py            # JWT 生成与解析
    response.py            # 统一返回格式工具
    exceptions.py          # 错误码 & 全局异常处理
    deps.py                # FastAPI 依赖注入（token 验证）
  models/                  # ORM 模型
  schemas/                 # Pydantic 请求/响应模型
  api/
    auth/                  # 认证接口（mock 登录）
    enterprise/            # 企业端接口（/api/enterprise）
    admin/                 # 管理端接口（/api/admin）
    common/                # 通用接口（/api/common）
  services/
    auth_adapter.py        # 统一身份认证适配层（预留）
  repositories/            # 数据访问层
  utils/                   # 工具函数
migrations/                # Alembic 迁移脚本
tests/                     # 测试
```
