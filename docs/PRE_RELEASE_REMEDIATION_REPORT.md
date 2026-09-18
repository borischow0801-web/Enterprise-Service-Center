# 上线前核心整改报告

本报告对应 `docs/PRE_RELEASE_REMEDIATION_PLAN.md` 中确认仍需修复的问题，记录 A1-A5、B1 六个阶段的实际整改结果。所有结论均基于对当前最新代码的重新核查与实际运行验证（真实 MySQL 开发库 + 两个前端真实构建），而非机械照搬 `PROJECT_AUDIT_REPORT.md` 的历史结论。

---

## 1. 本轮修改摘要

- **修改文件**：44
- **新增文件**：27（含 3 份文档、7 个测试文件、2 个后端核心权限模块、1 个附件权限服务、1 个 Alembic 迁移在此前"企业注册登录"阶段已完成——本轮 A1-B1 **未新增数据库迁移**）
- **删除文件**：1（`enterprise-h5/src/views/login/MockLogin.vue`，此前阶段已拆分为 `Login.vue`/`Register.vue`/`DevMockLogin.vue`，本轮未涉及）
- 六个阶段（A1→A2→A3→A4→A5→B1）按顺序逐一实施，每阶段完成后单独跑通对应验证再进入下一阶段，未出现"改到一半发现方案不通再返工"的情况。

---

## 2. A1 附件安全整改结果

**重新核查结论**：`PROJECT_AUDIT_REPORT.md` 指出的"附件下载零鉴权、attachment_id 可枚举"问题**依然存在**（代码自上次审计后未被触碰），予以修复。

- 下载接口 `GET /api/common/attachments/{id}/download` 改为：先查附件记录，若不是"会议室封面/图册/材料模板"这类天然公开的引用资源，则强制要求登录并调用新建的 `app/services/attachment_access_service.py::assert_attachment_accessible` 做归属校验——企业端按 `business_type` 复用各模块已有的 `get_by_id_and_enterprise` 方法；管理端复用 A2 建立的 `DataPermissionService` + 角色权限。
- 会议室封面图/图册/材料模板这类"公开展示"附件（`<img>` 标签无法携带 Authorization 头）**刻意保持匿名可访问**——这是经过核实的有意设计，不是遗留漏洞：这类内容本来就应该在企业浏览会议室阶段可见，锁死会免费展示的封面图会直接破坏现有的会议室浏览功能，与需求文档"企业端会议室图片可见"矛盾。判定逻辑集中在 `is_public_reference_asset()` 一处，不与业务敏感附件共用规则。
- 上传接口新增：扩展名白名单（pdf/doc/docx/xls/xlsx/ppt/pptx/jpg/jpeg/png/gif/bmp/webp）、危险 Content-Type 前缀黑名单（text/html、application/javascript 等）、文件名净化（去路径分量/控制字符）、下载时 media_type 由服务端按扩展名白名单派生（不再信任存量数据里的客户端声明值）。
- **前端连带修复**：下载接口加鉴权后，原本用 `window.open(url)`/`<img>` 直接访问的 4 处业务敏感附件调用点（admin-web 的 `GovMeetingDetail.vue`、`BookingDetail.vue`×2、enterprise-h5 的 `MeetingBookingDetail.vue`）会因浏览器不带 Authorization 头而失败——已全部改为 fetch 携带 token 取 Blob 后再展示/下载（`admin-web/src/utils/attachment.ts`、`enterprise-h5/src/utils/attachment.ts`），验证 UX 与原行为基本一致。会议室封面图/材料模板等 3 处公开资源调用点无需改动。

**实际验证**（真实 MySQL 开发库 + 真实 uvicorn 进程）：匿名下载被拒绝、企业跨账号下载被拒绝（403）、正确账号下载成功、管理端跨区域/无权限角色下载被拒绝、正确区域+角色下载成功、未知 data_scope 下载被拒绝（fail closed）、上传后未绑定前仅上传者本人可见、绑定到会议室后任意匿名用户可见——全部符合预期。

## 3. A2 数据权限整改结果

**重新核查结论**：三大模块管理端"详情/操作"接口大量使用不带数据权限过滤的 `get_by_id`/`get_room_by_id`/`get_booking_by_id`/`get_apply_by_id` 的问题**依然存在**，且经交叉核实是横跨三个模块的系统性模式，予以统一修复。

- 新建 `app/constants/permission.py`（`DataScope`/`resolve_scope_branch`/`ScopeBranch`）+ `app/core/permission.py::DataPermissionService.assert_can_access(operator, region_code, dept_ids)`，作为唯一的数据权限判断入口，不在各接口里重复手写 `if region_code != ...`。
- **Fail Closed**：未识别的 `data_scope` 值一律拒绝（详情/操作接口抛 403，列表接口返回 0 条），不再像原来那样对未知值默认不加过滤、等同于放行全部数据。同步修复的位置：`appeal_repo.list_for_admin`、`meeting_room_repo.list_rooms_admin`/`list_bookings_admin`、`gov_meeting_repo.list_applies_admin`、`dashboard_service.py` 四个统计查询方法、`admin/router.py` 的服务中心列表接口。
- 覆盖范围（任务书"至少覆盖"清单全部落实）：
  - **企业诉求**：详情、受理、退回、不予受理、分派、企服中心办理、部门反馈、审核回复、办结（A4 新增）、回访记录、附件（A1）。
  - **共享会议室**：会议室资源新增/修改/启停/开放规则/手工占用/特殊日期（原文虽未点名，但"改变业务状态的接口都要做数据权限检查"这一总原则要求覆盖）、预约详情、审批、驳回、退回补充、完成、爽约、附件（A1）。
  - **政企约见**：详情、审核（受理/驳回/退回补正）、安排、修改安排、确认、完成、填写纪要、办结、附件（A1）。
- 部门维度：诉求模块本身有"责任部门/历史分派部门"概念，`_assert_scope` 精确核对 `responsible_dept_id` 与历史 `AppealAssignment` 记录；会议室与政企约见没有部门级归属概念，`DEPARTMENT`/`SELF` 按区域近似处理——这是延续代码里早已存在的设计（`# DEPARTMENT/SELF: TODO — treated as REGION`），不是本轮引入的新简化。

**实际验证**：跨区域管理员访问/操作诉求、会议室、预约、会议室资源、政企约见均返回 403；本区域管理员正常操作；`dataScope=ALL` 不受区域限制；未知 `data_scope` 值列表返回 0 条、详情/操作返回 403。

**连带修复**：admin-web 登录页 `dataScope` 下拉选项（`NATIONAL/PROVINCE/REGION/DISTRICT/CENTER`）与后端识别值不一致，选择非 REGION 选项会被后端 fail-closed 直接拒绝导致管理端不可用——已改为 `ALL/REGION/DEPARTMENT` 三个真实识别值。

## 4. A3 角色权限整改结果

**重新核查结论**：`role_codes` 全程未被任何代码校验的问题**依然存在**，予以补齐"最小可上线"版本（不建设完整 IAM/RBAC 平台）。

- 角色来源：现有代码/文档中唯一出现过的真实角色是 `CENTER_ADMIN`。经查 `第一阶段数据库与后端接口设计说明.md` §13.2，这是项目材料中唯一给出角色列表的地方，本轮以此为唯一权威依据，未凭空创造角色：`PLATFORM_ADMIN`/`CITY_ADMIN`/`CENTER_ADMIN`/`CENTER_STAFF`/`DEPT_USER`/`ROOM_ADMIN`。
- 权限编码（11个，`app/constants/permission.py::Permission`）+ 角色-权限映射 `ROLE_PERMISSIONS`，覆盖：业务查看/业务办理（含审批）/部门反馈/会议室管理/政企约见管理/字典维护/操作日志查看/管理端工作台，任务书列出的全部类别均已覆盖。无法从现有材料判断的归属（如平台/市级管理员是否应做日常业务操作）已在 `docs/ADMIN_PERMISSION_MATRIX.md` 明确标注"需要业务确认"，未擅自猜测。
- 后端：`app/core/permission.py::require_permissions(...)` 作为 FastAPI 依赖，替换全部管理端接口原有的 `current: CurrentAdmin`，一次性接入 appeals/meeting_rooms/meeting_bookings/gov_meetings/dictionaries/operation_logs/dashboard/service-centers 全部相关接口，未在几十个接口里重复手写角色判断逻辑。
- 前端：`admin-web/src/constants/permission.ts`（镜像后端映射）+ `admin-web/src/utils/permission.ts::hasPermission()` + `v-permission` 指令（`admin-web/src/directives/permission.ts`）+ 路由 `meta.permission` 守卫 + 菜单按权限过滤（`AdminLayout.vue`）+ 关键操作按钮按权限隐藏（诉求/预约/约见详情页操作区、会议室新增/编辑/启停、材料规则新增/编辑/删除）。**前端权限只影响 UI 显示，后端才是最终边界**——已通过直接调用 API（绕过前端）验证后端独立拒绝无权限请求。

**实际验证**：ROOM_ADMIN 无诉求权限时操作诉求返回 403；CENTER_STAFF 有诉求处理权限时操作成功；ROOM_ADMIN 有会议室管理权限时操作成功；DEPT_USER 无字典维护权限时操作返回 403 但可查看本部门范围内诉求列表；无角色（`roleCodes: []`）访问工作台返回 403。

## 5. A4 企业诉求闭环结果

**重新核查结论**：任务书指出的三个问题**全部依然存在**，逐一修复。

1. **诉求退回补充无法响应**：`enterprise-h5/src/api/appeal.ts` 新增 `supplementAppeal()`，`AppealDetail.vue` 新增补充材料区块（说明文字 + 附件上传，复用 A1 的附件上传机制），提交后调用现有后端接口。已实测走完 **企业提交 → 管理端退回补充 → 企业看到退回原因 → 企业补充 → 管理端继续办理** 完整链路。
2. **`EVALUATED` 无法进入 `COMPLETED`**：按现有状态机模式补齐，不绕过状态机直接改字段：`app/constants/appeal.py` 新增 `ALLOWED_STATUS_FOR_ACTION[COMPLETE] = [EVALUATED]`；`AppealService.complete_appeal()`（校验状态 → 写状态 → 写审核轨迹 `AppealRecord` → 写操作日志 `SysOperationLog` → 设置 `completed_at`）；新增路由 `POST /api/admin/appeals/{id}/complete`（`APPEAL_HANDLE` 权限 + A2 数据权限校验）；admin-web 新增"办结"按钮与弹窗。已实测诉求从 `PENDING_ACCEPT` 一路走到 `COMPLETED`，且办结后再次调用返回 40901（状态机拒绝重复办结）。
3. **管理端诉求详情附件上传/下载 TODO**：下载按钮接入 A1 建立的鉴权下载机制；企服中心办理/部门反馈弹窗补齐 `el-upload` 组件，提交时把 `attachmentIds` 一并传给已支持该字段的后端接口（`AppealCenterHandleRequest`/`AppealDeptReplyRequest` 本就支持，此前只是前端没有采集入口）。

**未处理但发现的关联问题**：诉求"分派责任部门 → 部门反馈 → 企服中心审核"分支路径中，`DEPT_REPLIED`（部门已反馈）这一状态常量定义了但代码从未实际设置（`dept_reply` 直接跳到 `CENTER_REVIEWING`）——这是旧审计报告 P3 级技术债，与本轮 A4 明确要修的三项无关，未处理，列入第14节。

## 6. A5 生产安全整改结果

**重新核查结论**：

| 项目 | 状态 | 处理 |
|---|---|---|
| 企业端 mock-login 生产网关 | 已解决（上一阶段） | 无需重复修改 |
| 管理端 mock-login 生产网关 | **依然存在** | 本轮补齐：`settings.app_env=="production"` 时返回 40401，不注册真实逻辑 |
| `APP_SECRET_KEY` 生产强校验 | **依然存在** | `app/core/config.py` 新增 `model_validator`：生产环境下密钥为空/等于已知占位值/长度不足32位，直接抛错阻止启动；不自动生成随机密钥（避免容器重启后全部 Token 失效） |
| Swagger 生产网关 | **依然存在** | 生产环境 `docs_url`/`redoc_url`/`openapi_url` 全部设为 `None`；开发环境不受影响 |
| CORS 环境变量化 | **部署隐患，非漏洞** | 新增 `CORS_ALLOWED_ORIGINS` 环境变量（逗号分隔），未配置时回退到原有开发环境白名单，不会因漏配就放开成 `*` |
| 前端敏感信息 console | 部分已解决 | enterprise-h5 `MockLogin.vue` 已在上一阶段清理；本轮核查发现 admin-web `Login.vue`、enterprise-h5 `Home.vue` 各有一处未加 `import.meta.env.DEV` 判断的 `console.error`/`console.warn`，均已修复；其余 console 输出（`request.ts` 等）本就已正确使用 DEV 判断 |

**实际验证**（development / production 环境行为对比）：
- production + 弱密钥：应用启动时直接抛 `ValidationError` 退出（符合"应用直接启动失败"要求）。
- production + 强密钥：正常启动。
- production 下：`/docs`、`/openapi.json` 返回业务层 40401（HTTP 状态码仍是 200，这是本项目"统一返回结构"的既有约定，不是本轮改动引入的行为）；企业端/管理端 mock-login 均返回 40401；真实的企业注册/登录接口不受影响，正常返回。
- development 下：`/docs` 正常显示 Swagger UI；两个 mock-login 正常工作。

## 7. B1 自动化测试建设结果

**基础设施**：项目此前只有企业注册/登录阶段建立的 14 个测试用例，使用 SQLite 内存库。本轮按任务书"不要为了方便强行使用 SQLite，优先确保测试结果能代表实际 MySQL 8 行为"的明确要求，**将测试基础设施迁移为对接真实 MySQL**：

- `requirements-dev.txt`（新增，`-r requirements.txt` + `pytest`/`httpx`）——测试依赖与生产依赖分离，不随生产部署安装。
- `tests/conftest.py` 重写：连接真实 MySQL（复用 `settings.database_url`，不硬编码任何数据库地址）；本想为测试单独建库，但发现配置的数据库账号没有 `CREATE DATABASE` 权限（真实的最小权限部署，运行时才发现）——因此改为直接对接现有开发库，通过"外部事务 + SAVEPOINT 自动重启"的标准 SQLAlchemy 隔离技巧，让每个测试的所有写入（包括应用代码内部的 `session.commit()`）在测试结束后被整体回滚，已实测验证跑完全部35个用例后 `Enterprise`/`AppealMain`/`MeetingRoom`/`MeetingRoomBooking`/`GovMeetingApply` 五张核心表近3分钟内零新增数据。
- 顺带修复了 `SysEvaluation`/`SysOperationLog` 两处模型定义与本次审计前修复的 `Enterprise` 同类的"index=True 与显式 Index() 重复声明"问题——纯 SQLAlchemy 元数据去重，不产生任何新的 MySQL DDL，是让 `pytest` 能够正常运行所必须的前置修复。
- 附件上传测试会在磁盘上产生真实文件，不在数据库事务范围内、SAVEPOINT 回滚不会撤销——新增 `_cleanup_uploaded_files` 自动清理夹具，每个测试前后快照 `uploads/attachments/` 目录并删除测试期间新增的文件，已实测验证运行全部测试前后文件数量不变。
- `tests/helpers.py`（新增）：统一的唯一标识符生成器（信用代码/手机号/平台用户ID均带随机后缀），从根源避免测试数据与开发库中已存在的真实/历史测试数据发生冲突（本轮排查中确实发现过一次真实冲突：旧的写死信用代码与此前手工验证阶段产生的真实数据重名，已改为动态生成后解决）。

**测试文件与覆盖范围**：

| 文件 | 用例数 | 覆盖内容 |
|---|---|---|
| `tests/test_enterprise_auth.py` | 15 | 企业注册/登录、密码非明文、重复注册、账号枚举防护、JWT可用性、企业+管理端 mock-login 生产网关、参数校验 |
| `tests/test_authorization.py` | 15 | **越权测试为主**：跨区域诉求/会议室/政企约见访问与操作、无对应角色调用操作接口、未知 data_scope fail-closed、匿名/跨企业/跨权限附件下载、非法文件类型上传 |
| `tests/test_appeal_flow.py` | 2 | 诉求完整闭环至 COMPLETED（含退回补充分支）+ 分派部门反馈分支 |
| `tests/test_meeting_room_flow.py` | 2 | 预约提交→审核通过→完成闭环 + 终态后非法状态跳转被拒绝 |
| `tests/test_gov_meeting_flow.py` | 1 | 政企约见完整闭环至 COMPLETED |
| **合计** | **35** | — |

---

## 8. 权限矩阵

见 `docs/ADMIN_PERMISSION_MATRIX.md`（角色来源、权限编码定义、角色×权限矩阵、4 项需业务确认事项）。

## 9. 自动化测试结果

```
总测试数：35
通过：35
失败：0
跳过：0
```

（`pytest tests/ -q` 实际输出：`35 passed, 519 warnings in 13.41s`；警告全部是项目既有代码中 `datetime.utcnow()` 的 Python 3.12 弃用提示，与本轮改动无关，不影响测试结果。）

## 10. 三大业务流程验证结果

- **Appeal（企业诉求）**：**是否闭环：是**。已验证完整走完 `PENDING_ACCEPT → NEED_SUPPLEMENT → PENDING_ACCEPT(补充后) → ACCEPTED → PENDING_EVALUATION → EVALUATED → COMPLETED`，以及"分派部门 → 部门反馈 → 企服中心审核通过"分支。终态后重复办结被状态机拒绝（40901）。
- **Meeting Room（共享会议室）**：**是否闭环：是**（本身在整改前就是三个模块中状态机最完整的一个）。已验证 `PENDING_AUDIT → APPROVED → COMPLETED`，以及终态后再次驳回被状态机拒绝。本轮不涉及 TOCTOU 并发竞态修复，按任务书要求未处理。
- **Gov Meeting（政企约见）**：**是否闭环：是**。已验证完整走完 `PENDING_AUDIT → PENDING_ARRANGE → ARRANGED → WAIT_MEETING → MEETING_COMPLETED → PENDING_EVALUATION(填纪要自动触发) → EVALUATED → COMPLETED`。

## 11. 安全验证

| 项目 | 是否已阻断 |
|---|---|
| 匿名附件下载 | **是**（业务附件；会议室封面图/材料模板为有意保留的公开资源，非漏洞） |
| 跨企业附件访问 | **是** |
| 跨区县数据访问（诉求/会议室/预约/政企约见，详情与操作接口） | **是** |
| 无角色/无对应权限操作 | **是** |
| 生产环境 mock-login（企业端+管理端） | **是** |
| 生产环境默认/占位 Secret | **是**（启动即失败，不允许带默认值上线） |
| Swagger 生产暴露 | **是** |

## 12. 前端构建

- **admin-web**：`vue-tsc -b && vite build` **成功**，0 TypeScript 错误。仅有第三方库 `@vueuse/core` 的无害 Rollup 提示与主 chunk 超过 500KB 的性能建议（既有问题，未在本轮处理范围内）。
- **enterprise-h5**：`vue-tsc -b && vite build` **成功**，0 TypeScript 错误，无警告。

## 13. 数据库变化

**本轮（A1-A5、B1）未新增 Alembic migration。** 涉及的模型文件改动均不影响实际 MySQL 结构：
- `enterprise.py`/`system.py` 中 3 处 `index=True` 与 `__table_args__` 显式 `Index()` 重复声明的清理，属于纯 SQLAlchemy 元数据去重（实际 MySQL 索引一直只由 Alembic 迁移脚本创建，从未依赖 SQLAlchemy 的 `index=True` 推断），不产生任何 DDL 变化。
- 此前"企业自主注册/登录"阶段已建立的 `010_enterprise_identity` migration（`revision=010_enterprise_identity`，`down_revision=009_booking_enterprise_type`）继续有效，本轮通过 `alembic current` 确认仍处于 head，未受影响。
- upgrade/downgrade：本轮无新增内容需要验证；010 号迁移的 upgrade 已在此前阶段验证通过（37→37条企业数据无丢失）。

## 14. 未处理问题

**本轮明确不处理（按任务书 §一 排除范围）**：消息中心、FAQ、会议室日历、统计图表、Excel 导出、独立附件管理、UI 大规模美化、性能优化、P3 代码重构、Dockerfile/docker-compose、麒麟V10部署、CI/CD。

**执行过程中发现但与本轮目标无关、未顺手处理的问题**：
1. `AppealStatus.DEPT_REPLIED`（部门已反馈）状态常量定义但从未被代码实际设置——`dept_reply` 直接跳到 `CENTER_REVIEWING`，跳过了这一中间状态。属于 P3 级技术债，不影响当前闭环（企服中心仍能正确审核部门反馈），未处理。
2. 会议室审批环节存在的 TOCTOU 并发竞态窗口（两个管理员近乎同时审核通过两个时间冲突的预约）——任务书明确"不要求本轮解决"，未处理。
3. 诉求流水号生成（`generate_daily_serial`）的非原子并发竞态——旧审计报告 P1-8，任务书未列入本轮范围，未处理。
4. `admin-web` 主 JS chunk 超过 500KB 的构建性能提示——不在本轮范围（属于 P3 性能优化）。
5. 服务中心（`ServiceCenter`）资源的权限归属在设计文档中缺乏依据，本轮采取"列表任意已登录管理端可见（供创建会议室选择归属中心用）+ 新增/修改/启停归入 DICT_MANAGE"的保守处理，已在 `docs/ADMIN_PERMISSION_MATRIX.md` 中标注为需业务确认事项，不视为本轮遗留 bug。

## 15. 是否具备进入 Docker 化阶段的条件

**READY**（有条件）——A1-A5 六项安全/权限阻断性问题均已修复并通过实测验证，三大业务流程真实闭环，35 个自动化回归测试全部通过，可以进入容器化准备阶段。

需要注意但不阻断 Docker 化启动的事项：
- 本轮未处理 Dockerfile/docker-compose/Nginx/麒麟V10相关工作，这些仍需单独立项（按任务书要求，本轮不做）。
- 进入 Docker 化阶段后，`CORS_ALLOWED_ORIGINS`、`APP_SECRET_KEY`（生产强密钥）、`APP_ENV=production` 三个环境变量必须在容器编排层正确注入，否则应用会按本轮新增的校验逻辑直接拒绝以不安全配置启动——这是有意为之的保护机制，不是需要修复的缺陷。
- 数据库测试目前依赖真实 MySQL 可达（无法退化为 SQLite），后续 CI/Docker 环境需要为测试阶段提供一个 MySQL 服务实例。
