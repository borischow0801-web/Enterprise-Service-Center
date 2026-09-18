# 上线前核心整改计划

本文档在**重新核查当前最新代码**（而非机械照搬 `PROJECT_AUDIT_REPORT.md`）的基础上，确认旧审计报告中哪些问题已经因"企业自主注册+密码登录"开发而解决、哪些仍然存在，并给出本轮整改计划。

核查方式：`git status` 确认哪些文件自上次审计后被修改过（只有认证相关文件），对 A1-A5/B1 涉及的其余文件（`app/api/common/router.py`、三大业务 service/repo、`app/core/deps.py`、admin-web 全部文件）逐一重新阅读确认当前内容。

---

## 核查结果一览

| 编号 | 问题 | 旧报告状态 | 当前代码状态 | 是否仍需修复 | 计划 |
|---|---|---|---|---|---|
| 1 | 附件下载接口零鉴权（P0-2） | 存在 | **仍然存在**：`app/api/common/router.py::download_attachment` 无任何 `Depends` 鉴权，`attachment_id` 为可枚举自增整数，代码自上次审计后未被触碰 | 是 | A1 |
| 2 | 附件上传无类型白名单（P1-6/P1-4） | 存在 | **仍然存在**：`upload_attachment` 仅按客户端 `Content-Type`/文件名后缀信任，无白名单 | 是 | A1 |
| 3 | 三大模块管理端"详情/操作"接口未做数据权限校验（P1-1） | 存在 | **仍然存在**：`appeal_service.py`（9处 `get_by_id`）、`meeting_room_service.py`（多处 `get_room_by_id`/`get_booking_by_id`）、`gov_meeting_service.py`（8处 `get_apply_by_id`）均未加 scope 校验；仅 `list_*` 系列方法做了过滤 | 是 | A2 |
| 4 | 未知 `data_scope` 默认放行（fail-open）（隐含于 P1-1） | 存在 | **仍然存在**：`data_scope not in ("REGION","DEPARTMENT","SELF")` 时列表查询不加任何过滤条件，等价于 ALL | 是 | A2（改为 fail-closed） |
| 5 | `role_codes` 全程未被校验（P1-2） | 存在 | **仍然存在**：`grep role_codes` 命中的 8 处均只是"存储/展示"，`app/core/deps.py` 和全部 admin-web 路由/菜单/按钮均未读取 `role_codes` 做任何判断 | 是 | A3 |
| 6 | admin-web 登录 `dataScope` 下拉与后端枚举不一致（P1-7） | 存在 | **仍然存在**：`admin-web/src/views/login/Login.vue` 提供 `NATIONAL/PROVINCE/REGION/DISTRICT/CENTER`，后端只识别 `REGION`/`DEPARTMENT`/`SELF`，其余一律放行全部数据 | 是（必须与 A2 的 fail-closed 改造同步修，否则现有测试账号会被直接拒绝） | A2 |
| 7 | 诉求"退回补充"在企业端 H5 无响应入口（P1-4） | 存在 | **仍然存在**：`enterprise-h5/src/api/appeal.ts` 无 `supplement` 相关函数，后端 `POST /api/enterprise/appeals/{id}/supplement` 早已存在但从未被前端调用 | 是 | A4 |
| 8 | 诉求 `EVALUATED` 无法进入 `COMPLETED`（P1-3） | 存在 | **仍然存在**：`app/constants/appeal.py::ALLOWED_STATUS_FOR_ACTION` 无 `COMPLETE` 条目，`appeal_service.py` 无对应方法，`api/admin/appeals.py` 无 `/complete` 路由 | 是 | A4 |
| 9 | 管理端诉求详情附件上传/下载 TODO（P2-7） | 存在 | **仍然存在**：`admin-web/src/views/appeal/AppealDetail.vue:104,263,302` 三处 TODO 原样未动 | 是 | A4 |
| 10 | 企业端 mock-login 生产环境零验证、无网关（P0-1 企业端部分） | 存在 | **已解决**：`app/api/auth/router.py::enterprise_mock_login` 已在 `settings.app_env=="production"` 时返回 40401；企业端已有正式的 `register`/`login` 接口，经真实 MySQL + pytest 验证通过 | **已解决，无需重复修改** | — |
| 11 | 管理端 mock-login 生产环境零验证、无网关（P0-1 管理端部分） | 存在 | **仍然存在**：`admin_mock_login` 完全没有环境判断，任何环境下都可无条件自报 `roleCodes`/`dataScope` 获得管理员 token；上一轮任务明确将其列为"范围外、留待后续"，本轮 A5 明确要求处理 | 是 | A5 |
| 12 | `APP_SECRET_KEY` 生产环境无强制校验（P1-5） | 存在 | **仍然存在**：`app/core/config.py::Settings.app_secret_key` 默认值 `"dev-secret-key"`，无论 `.env` 是否配置成占位符，启动时都不做任何校验 | 是 | A5 |
| 13 | Swagger `/docs`/`/openapi.json` 生产环境无网关（P2-4） | 存在 | **仍然存在**：`app/main.py` 的 `FastAPI(...)` 构造未按环境条件设置 `docs_url`/`redoc_url`/`openapi_url` | 是 | A5 |
| 14 | CORS 配置硬编码开发端口，无生产环境变量入口 | 存在（标记为部署事项） | **仍然存在**：`app/main.py` 中 `allow_origins` 为写死的本地开发端口列表 + 内网正则，没有读取任何环境变量的分支；当前配置本身对开发环境安全，但生产环境需要能够配置真实域名 | 是（补充可配置能力，不改变默认安全性） | A5 |
| 15 | enterprise-h5 `MockLogin.vue` console 泄露 PII/Token（P2-12） | 存在 | **已解决**：`MockLogin.vue` 已删除，替换为不打印敏感信息的 `Login.vue`/`Register.vue`/`DevMockLogin.vue`（已在上一轮验证） | **已解决，无需重复修改** | 本轮仅需确认 admin-web 是否有同类问题（见下） |
| 16 | admin-web 是否存在敏感信息 console 输出 | 未在旧报告中细查 | 需本轮核查 | 待查 | A5（核查后按需修） |
| 17 | 项目无可运行自动化测试（P2-13） | 存在 | **部分解决**：上一轮已建立 `tests/conftest.py` + `tests/test_enterprise_auth.py`（14 个用例，覆盖注册/登录），但未覆盖三大业务流程和越权场景 | 是（在已有基础上扩展，而非重建） | B1 |

## 需要补充核查的项（本计划撰写时一并确认）

- admin-web 全量 `console.*` 扫描：确认是否存在打印 token/身份证号/手机号等敏感字段的调用。
- `.env.example` 当前内容是否已经是"仅占位说明"而非可直接误用的真实值——需要确认现有措辞是否需要加强提示。
- `data_scope` 除 `REGION` 外，`DEPARTMENT`/`SELF` 在会议室、政企约见模块目前被当作与 `REGION` 等价处理（代码注释明确写了 "TODO — treated as REGION"）——本轮不重新设计部门级会议室/约见权限模型（业务从未要求过，超出范围），仅在新的统一权限服务中**保留该既有近似**，但把"未知值"与"REGION 近似"两种情况明确区分并对"未知值"做 fail-closed。

---

## 角色与数据权限来源确认

现有代码里唯一真实出现过的角色编码是 `CENTER_ADMIN`（`README.md` 示例、admin-web 登录页默认值）。系统未内置角色枚举。经查 `第一阶段数据库与后端接口设计说明.md` 第 13.2 节（"建议第一阶段预设以下角色编码"），存在明确的设计基线：

| 角色 | 说明 | 数据范围（设计文档原文） |
|---|---|---|
| PLATFORM_ADMIN | 平台管理员 | 全部 |
| CITY_ADMIN | 市级管理员 | 全部 |
| CENTER_ADMIN | 企服中心管理员 | 本区县/本企服中心 |
| CENTER_STAFF | 企服中心工作人员 | 本区县/本企服中心 |
| DEPT_USER | 部门办理人员 | 本部门相关事项 |
| ROOM_ADMIN | 会议室管理员 | 本区县会议室和预约 |

本轮角色权限体系（A3）以此表为唯一权威依据构建，不额外发明角色。功能权限（哪个角色能点哪个按钮）在设计文档中没有给出细粒度定义，将结合各模块现有业务流程语义推导，推导依据和不确定项在 `docs/ADMIN_PERMISSION_MATRIX.md` 中逐条说明，无法从现有材料判断的一律标注"需要业务确认"并采用最小权限。

---

## 本轮实施顺序（对应任务书 Phase 1-6）

1. **Phase 1 / A1**：附件下载鉴权 + 权限判断（先建立可复用的 `DataPermissionService` 基础能力，供 A1 的管理端附件权限判断和 A2 复用）+ 上传安全加固。
2. **Phase 2 / A2**：三大模块管理端详情/操作接口接入 `DataPermissionService`；`data_scope` 改为 fail-closed；同步修正 admin-web 登录 `dataScope` 下拉选项。
3. **Phase 3 / A3**：角色常量与角色-权限映射、`require_roles` 依赖、三大模块+字典+日志+工作台接口接入角色校验；admin-web 路由/菜单/按钮权限（`hasRole`/`v-permission`）。
4. **Phase 4 / A4**：诉求补充材料（企业端 H5）、诉求办结（后端+前端）、诉求附件上传/下载 TODO 清理（复用 A1 附件安全机制）。
5. **Phase 5 / A5**：管理端 mock-login 环境网关、`APP_SECRET_KEY` 生产强校验、Swagger 生产网关、CORS 环境变量化、前端敏感信息 console 复查。
6. **Phase 6 / B1**：在已有测试基础上扩充——越权测试、三大业务全流程测试、附件权限测试，全部通过后产出定向审计报告。

每个 Phase 完成后执行 `git diff --stat` 确认改动范围仅限该 Phase 相关文件，再运行相关测试，然后进入下一 Phase。
