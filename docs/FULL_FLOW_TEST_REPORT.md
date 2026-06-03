# 三大业务全流程联调测试报告

**测试时间**：2026-05-28  
**测试方式**：`scripts/test_api_flow.py`（BASE_URL=http://127.0.0.1:8000）+ 代码审查 + 构建验证  
**测试脚本**：`BASE_URL=http://127.0.0.1:8000 .venv/bin/python scripts/test_api_flow.py`

---

## 一、运行检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| `python -m compileall app` | ⚠️ 部分通过 | 需使用 `.venv/bin/python`；`app/services/__pycache__` 目录权限导致个别文件无法写 pyc（不影响运行） |
| `alembic upgrade head` | ✅ 成功 | 使用 `.venv/bin/alembic` |
| `admin-web npm run build` | ✅ 成功 | |
| `enterprise-h5 npm run build` | ✅ 成功 | |
| `GET /api/health` | ✅ 200 | |
| 企业端 mock 登录 | ✅ | `enterprise_token` |
| 管理端 mock 登录 | ✅ | `esc_admin_token`（与管理端隔离） |

**企业端访问地址**：`http://127.0.0.1:5174/login`（勿用 5173，为管理端）

---

## 二、流程一：企业诉求

**测试数据编号**：`APPEAL-{timestamp}`（脚本自动生成 creditCode / 诉求）

| 步骤 | 结果 |
|------|------|
| 企业提交诉求 | ✅ PENDING_ACCEPT |
| 企业列表/详情 | ✅ |
| 管理端列表/详情 | ✅ |
| 管理端受理 | ✅ ACCEPTED |
| 企服中心自行办理 | ✅ **PENDING_EVALUATION**（未进入 CENTER_REVIEWING） |
| 企业查看办理回复（records.opinion） | ✅ |
| 企业评价 | ✅ POST `/api/enterprise/appeals/{id}/evaluation` |
| 管理端查看评价 | ✅ EVALUATED |

**本流程 API 路径（已核对）**：
- 评价：`POST /api/enterprise/appeals/{id}/evaluation`（非 `/evaluate`）

---

## 三、流程二：共享会议室

**测试数据编号**：`BOOK-{timestamp}`，会议室 ID 由列表动态选取

| 步骤 | 结果 |
|------|------|
| 管理端会议室列表 | ✅ |
| 企业端会议室列表/详情 | ✅ |
| 企业提交预约（+3 天时段） | ✅ PENDING_AUDIT |
| 管理端审核通过 | ✅ APPROVED |
| 时间冲突检测 | ✅ 40902 |
| 管理端确认完成 | ✅ COMPLETED |

**说明**：
- 脚本使用的会议室可能无材料规则（历史数据）；`scripts/init_demo_data.py` 为新会议室自动配置工作日开放规则 + 盖章申请表必传规则。
- 企业端封面图/附件 URL 已修复：相对路径会拼接 `VITE_API_BASE_URL`。

**本流程 API 路径**：
- 取消预约：`POST /api/enterprise/meeting-bookings/{id}/cancel`
- 材料规则：`GET /api/enterprise/meeting-rooms/{id}/material-rules`（优先区划/企服中心规则）

---

## 四、流程三：政企约见

**测试数据编号**：`GOV-{timestamp}`

| 步骤 | 结果 |
|------|------|
| 企业提交（含 expectedLevel） | ✅ PENDING_AUDIT |
| 管理端受理（含 finalLevel） | ✅ PENDING_ARRANGE |
| 安排约见（日期/时间/地点/参会人） | ✅ WAIT_MEETING |
| 标记完成 + 纪要 + 发送评价 | ✅ PENDING_EVALUATION |
| 企业评价 | ✅ POST `/api/enterprise/gov-meetings/{id}/evaluate` |
| 管理端办结 | ✅ COMPLETED |

**本流程 API 路径**：
- 评价：`POST /api/enterprise/gov-meetings/{id}/evaluate`（非 `/evaluation`）
- 须知：`GET /api/enterprise/gov-meetings/notice` ✅ **本次已补充后端接口**

---

## 五、自动化测试结果汇总

```
TOTAL=60  PASS=59  FAIL=1
```

**唯一失败项**：附件上传 `POST /api/common/attachments/upload`  
- **原因**：服务器 `uploads/attachments` 目录属主为 root，应用进程无写权限（环境权限，非业务逻辑错误）  
- **代码修复**：`upload_dir_resolved` 使用项目根目录绝对路径，避免 `./uploads` 因工作目录错误写入失败  
- **运维处理**：`chown/chmod` 将 `uploads` 目录赋予运行 uvicorn 的用户写权限后上传即可通过

---

## 六、本次修复清单

### 后端
| 文件 | 修复内容 |
|------|----------|
| `app/core/config.py` | `upload_dir` 默认绝对路径；新增 `upload_dir_resolved` |
| `app/main.py` | 启动时创建绝对路径上传目录 |
| `app/api/common/router.py` | 附件保存使用 `upload_dir_resolved` |
| `app/api/enterprise/gov_meetings.py` | 新增 `GET /notice` 须知接口 |
| `app/main.py`（CORS） | 此前已配置 5173–5175 及内网 IP |

### enterprise-h5
| 文件 | 修复内容 |
|------|----------|
| `src/utils/api.ts` | **新增** `apiBaseUrl` / `apiAssetUrl` |
| `src/utils/format.ts` | 新增 `getField` 字段兼容 |
| `src/api/common.ts` | 上传接口使用完整 baseURL |
| `src/api/meetingRoom.ts` | 封面图 URL 拼接；取消路径注释 |
| `src/api/appeal.ts` | 评价路径注释（`/evaluation`） |
| `src/api/govMeeting.ts` | 评价路径注释（`/evaluate`） |
| `src/views/meeting-room/*` | 封面/附件/模板下载 URL |
| `src/views/appeal/AppealDetail.vue` | `onActivated` 刷新详情 |
| `src/views/gov-meeting/GovMeetingDetail.vue` | `onActivated` 刷新详情 |

### admin-web
| 文件 | 修复内容 |
|------|----------|
| `src/views/appeal/AppealDetail.vue` | 审核通过/退回 Toast 文案修复 |

### 文档/脚本
| 文件 | 说明 |
|------|------|
| `scripts/init_demo_data.py` | 已存在，可重复执行演示数据 |
| `docs/FULL_FLOW_TEST_REPORT.md` | 本报告 |

---

## 七、三大流程是否跑通

| 流程 | 后端 API 联调 | 前端构建 | 说明 |
|------|---------------|----------|------|
| 企业诉求 | ✅ 全流程通过 | ✅ | 自办后状态正确 |
| 共享会议室 | ✅ 主流程通过 | ✅ | 附件上传依赖目录权限 |
| 政企约见 | ✅ 全流程通过 | ✅ | 须知接口已补 |

---

## 八、遗留问题

1. **附件上传目录权限**：需运维将 `/app/Enterprise-Service-Center/uploads` 赋予应用用户写权限（当前 root 拥有，导致 50003）。
2. **`python` 命令**：环境需使用 `.venv/bin/python` 或 `python3`。
3. **compileall pycache**：`app/services/__pycache__` 权限异常，可用 `PYTHONDONTWRITEBYTECODE=1` 或清理后重试。
4. **补充材料附件**：政企约见/诉求补充仍仅文字，附件上传 TODO 保留。
5. **历史会议室**：部分旧会议室可能无区划级材料规则，请执行 `init_demo_data.py` 或管理端配置。
6. **企业端端口**：开发服务器为 **5174**（非 5173）。

---

## 九、后续建议

1. 部署前统一 `UPLOAD_DIR` 为绝对路径并确保目录可写。
2. CI 中增加 `scripts/test_api_flow.py` 作为冒烟测试。
3. 管理端附件下载按钮可对接 `GET /api/common/attachments/{id}/download`（当前部分为 disabled TODO）。
