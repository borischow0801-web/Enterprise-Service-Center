# 企业服务中心系统 — 后端接口测试文档

## 1. 启动项目

### 环境准备

```bash
cd /app/Enterprise-Service-Center

# 安装依赖
.venv/bin/pip install -r requirements.txt

# 配置环境变量（复制 .env.example 并修改）
cp .env.example .env
```

### 启动开发服务器

```bash
# 开发模式（热重载）
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

启动后访问：
- **健康检查**：http://localhost:8000/api/common/health
- **Swagger 文档**：http://localhost:8000/docs
- **ReDoc 文档**：http://localhost:8000/redoc

---

## 2. 数据库迁移

```bash
cd /app/Enterprise-Service-Center

# 查看当前迁移状态
.venv/bin/python -m alembic current

# 升级到最新版本
.venv/bin/python -m alembic upgrade head

# 查看迁移历史
.venv/bin/python -m alembic history

# 回滚到上一版本
.venv/bin/python -m alembic downgrade -1
```

当前迁移版本：
| 版本 | 说明 |
|------|------|
| 001  | 基础表（企业、系统用户、字典、附件等） |
| 002  | 企业诉求表 |
| 003  | 共享会议室表 |
| 004  | 政企约见表 |

---

## 3. 初始化字典数据

```bash
cd /app/Enterprise-Service-Center

# 初始化基础字典（可重复执行，幂等）
.venv/bin/python scripts/init_dict.py
```

包含字典类型：SATISFACTION_LEVEL、URGENCY_LEVEL、APPEAL_STATUS、MEETING_BOOKING_STATUS、GOV_MEETING_STATUS、DATA_SCOPE

---

## 4. 初始化演示数据

```bash
cd /app/Enterprise-Service-Center

# 初始化完整演示数据（可重复执行，幂等）
.venv/bin/python scripts/init_demo_data.py
```

初始化内容：
- **字典数据**：16 个 dict_type，共 100+ 条（含 APPEAL_TYPE、INDUSTRY_TYPE、MEETING_ROOM_TYPE 等）
- **企服中心**：2 个（威海市企业综合服务中心、环翠区企业综合服务中心）
- **会议室**：2 个（一号会议室20人、多功能厅80人），含开放规则（工作日 08:30-17:30）和必传材料规则
- **特殊日期**：国庆节假日关闭（10-01、10-02）、调休工作日（10-07）

---

## 5. 执行接口流程测试脚本

```bash
cd /app/Enterprise-Service-Center

# 安装依赖（首次）
.venv/bin/pip install requests

# 执行三大业务主流程测试
.venv/bin/python scripts/test_api_flow.py

# 自定义 BASE_URL
BASE_URL=http://127.0.0.1:8000 .venv/bin/python scripts/test_api_flow.py
```

测试脚本覆盖：
- **企业诉求**：提交→受理→自行办理→评价（9步）
- **共享会议室**：查看→预约→审核→冲突检测→完成（10步）
- **政企约见**：提交→受理→安排→确认→完成→纪要→评价（8步）
- **安全隔离**：Token 隔离、数据隔离（5项）

---

## 6. 企业端 Mock 登录示例

```http
POST /api/auth/enterprise/mock-login
Content-Type: application/json

{
  "creditCode": "91370000MA3PXXX001",
  "enterpriseName": "威海创新科技有限公司",
  "legalPersonName": "张三",
  "legalPersonIdNo": "370102199001011234",
  "legalPersonMobile": "13800138000"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJ...",
    "tokenType": "Bearer",
    "expiresIn": 43200
  }
}
```

企业端接口均需携带 Header：`Authorization: Bearer {accessToken}`

---

## 7. 管理端 Mock 登录示例

```http
POST /api/auth/admin/mock-login
Content-Type: application/json

{
  "platformUserId": "admin_001",
  "username": "lihua",
  "realName": "李华",
  "departmentId": "dept_center_001",
  "departmentName": "企业服务中心",
  "regionCode": "371000",
  "regionName": "威海市",
  "roleCodes": ["CENTER_ADMIN"],
  "dataScope": "ALL"
}
```

`dataScope` 可选值：
| 值 | 含义 |
|----|------|
| ALL | 全部数据 |
| REGION | 本区县数据 |
| DEPARTMENT | 本部门数据 |
| SELF | 本人数据 |

---

## 8. 企业诉求主流程接口顺序

| 步骤 | 端 | 接口 | 说明 |
|------|----|----|------|
| 1 | 企业 | `POST /api/enterprise/appeals` | 提交诉求 |
| 2 | 企业 | `GET /api/enterprise/appeals` | 查看我的诉求列表 |
| 3 | 企业 | `GET /api/enterprise/appeals/{id}` | 查看诉求详情 |
| 4 | 管理 | `GET /api/admin/appeals` | 查看所有诉求列表 |
| 5 | 管理 | `POST /api/admin/appeals/{id}/accept` | 受理诉求 |
| 6a | 管理 | `POST /api/admin/appeals/{id}/center-handle` | 企服中心自行办理 |
| 6b | 管理 | `POST /api/admin/appeals/{id}/assign` | 分派责任部门 |
| 7 | 管理 | `POST /api/admin/appeals/{id}/department-reply` | 部门反馈 |
| 8 | 管理 | `POST /api/admin/appeals/{id}/review-reply` | 审核部门反馈 |
| 9 | 企业 | `POST /api/enterprise/appeals/{id}/evaluation` | 企业评价 |
| 10 | 管理 | `POST /api/admin/appeals/{id}/return-supplement` | 退回补充（分支） |
| 11 | 管理 | `POST /api/admin/appeals/{id}/reject` | 不予受理（分支） |

**诉求状态流转：**
```
PENDING_ACCEPT → ACCEPTED → CENTER_HANDLING → REPLIED → PENDING_EVALUATION → EVALUATED → COMPLETED
             ↘ NEED_SUPPLEMENT → (补充后) → PENDING_ACCEPT
             ↘ REJECTED
```

---

## 9. 共享会议室主流程接口顺序

| 步骤 | 端 | 接口 | 说明 |
|------|----|----|------|
| 1 | 管理 | `POST /api/admin/meeting-rooms` | 创建会议室 |
| 2 | 管理 | `PUT /api/admin/meeting-rooms/{id}/open-rules` | 配置开放规则 |
| 3 | 管理 | `POST /api/admin/meeting-rooms/material-rules` | 配置材料规则 |
| 4 | 企业 | `GET /api/enterprise/meeting-rooms` | 查看会议室列表 |
| 5 | 企业 | `GET /api/enterprise/meeting-rooms/{id}` | 查看会议室详情（含材料规则） |
| 6 | 通用 | `POST /api/common/attachments/upload` | 上传必传材料（如有） |
| 7 | 企业 | `POST /api/enterprise/meeting-bookings` | 提交预约 |
| 8 | 企业 | `GET /api/enterprise/meeting-bookings` | 查看我的预约列表 |
| 9 | 管理 | `GET /api/admin/meeting-bookings` | 查看所有预约列表 |
| 10 | 管理 | `POST /api/admin/meeting-bookings/{id}/approve` | 审核通过 |
| 11 | 管理 | `POST /api/admin/meeting-bookings/{id}/complete` | 确认使用完成 |
| 12 | 管理 | `POST /api/admin/meeting-bookings/{id}/no-show` | 标记爽约（分支） |
| 13 | 企业 | `POST /api/enterprise/meeting-bookings/{id}/cancel` | 取消预约（分支） |

**预约约束规则：**
- 至少提前 2 天预约
- 单次预约 30 分钟 ~ 4 小时
- 不可预约周末（除非配置特殊工作日）
- 不可预约节假日关闭日期
- 有必传材料时必须上传附件
- 爽约 ≥ 2 次，企业预约权限被限制

---

## 10. 政企约见主流程接口顺序

| 步骤 | 端 | 接口 | 说明 |
|------|----|----|------|
| 1 | 企业 | `POST /api/enterprise/gov-meetings` | 提交约见申请（commitmentChecked=1） |
| 2 | 企业 | `GET /api/enterprise/gov-meetings` | 查看我的申请列表 |
| 3 | 企业 | `GET /api/enterprise/gov-meetings/{id}` | 查看申请详情 |
| 4 | 管理 | `GET /api/admin/gov-meetings` | 查看所有申请列表 |
| 5 | 管理 | `POST /api/admin/gov-meetings/{id}/audit` | 审核（ACCEPT/REJECT/RETURN_SUPPLEMENT） |
| 6 | 管理 | `POST /api/admin/gov-meetings/{id}/arrange` | 安排约见（含参与人） |
| 7 | 管理 | `PUT /api/admin/gov-meetings/{id}/arrangements/{arr_id}` | 修改安排（分支） |
| 8 | 管理 | `POST /api/admin/gov-meetings/{id}/confirm` | 确认通知企业 |
| 9 | 管理 | `POST /api/admin/gov-meetings/{id}/complete` | 标记约见完成 |
| 10 | 管理 | `POST /api/admin/gov-meetings/{id}/record` | 填写约见纪要 |
| 11 | 管理 | `POST /api/admin/gov-meetings/{id}/finish` | 触发评价或直接办结 |
| 12 | 企业 | `POST /api/enterprise/gov-meetings/{id}/evaluate` | 企业评价 |

**状态流转：**
```
PENDING_AUDIT → PENDING_ARRANGE → ARRANGED → WAIT_MEETING → MEETING_COMPLETED → PENDING_EVALUATION → EVALUATED → COMPLETED
             ↘ NEED_SUPPLEMENT → (补充后) → PENDING_AUDIT
             ↘ REJECTED
```

---

## 11. 附件上传接口

支持企业端和管理端 Token：

```http
POST /api/common/attachments/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <binary>
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "id": 1,
    "originalName": "申请表.pdf",
    "fileExt": "pdf",
    "fileSize": 102400,
    "storagePath": "./uploads/attachments/xxx.pdf"
  }
}
```

上传后将 `id` 传入业务接口的 `attachmentIds` 字段即可完成绑定。

---

## 12. 常见错误码说明

| 错误码 | 含义 | 常见原因 |
|--------|------|---------|
| 0 | 成功 | — |
| 40001 | 参数校验失败 | 必填字段缺失、格式不正确 |
| 40101 | 未登录 | 未携带 Token 或 Token 已过期 |
| 40301 | 无权限 | 企业 Token 访问管理端接口，或反之 |
| 40401 | 数据不存在 | ID 不存在，或无权访问他人数据 |
| 40901 | 状态不允许当前操作 | 业务状态机校验失败 |
| 40902 | 会议室预约冲突 | 所选时间段已被预约或占用 |
| 40903 | 企业已被限制预约 | 爽约次数 ≥ 2 |
| 50001 | 系统内部异常 | 服务器端错误，查看日志 |
| 50003 | 文件上传失败 | 文件超过大小限制或磁盘写入失败 |

---

## 13. 完整测试数据初始化流程（一键）

```bash
cd /app/Enterprise-Service-Center

# 1. 数据库迁移
.venv/bin/python -m alembic upgrade head

# 2. 初始化字典
.venv/bin/python scripts/init_dict.py

# 3. 初始化演示数据
.venv/bin/python scripts/init_demo_data.py

# 4. 运行完整流程测试
.venv/bin/python scripts/test_api_flow.py
```

---

## 14. Swagger 接口分组

访问 http://localhost:8000/docs 可查看完整接口文档，分组如下：

| 分组 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/auth` | Mock 登录 |
| 企业端-诉求 | `/api/enterprise/appeals` | 诉求提交、查询、补充、评价 |
| 企业端-会议室 | `/api/enterprise/meeting-rooms` | 会议室查询、日历 |
| 企业端-预约 | `/api/enterprise/meeting-bookings` | 预约提交、查询、取消 |
| 企业端-政企约见 | `/api/enterprise/gov-meetings` | 约见申请、补充、评价 |
| 管理端-诉求 | `/api/admin/appeals` | 诉求受理、办理、分派 |
| 管理端-会议室 | `/api/admin/meeting-rooms` | 会议室管理、规则配置 |
| 管理端-预约 | `/api/admin/meeting-bookings` | 审核、完成、爽约 |
| 管理端-政企约见 | `/api/admin/gov-meetings` | 审核、安排、纪要、办结 |
| 通用 | `/api/common` | 文件上传、健康检查 |
