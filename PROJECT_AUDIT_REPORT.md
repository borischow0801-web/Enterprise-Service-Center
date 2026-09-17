# 企业服务中心系统 — 项目审计报告

**审计日期**: 2026-09-17
**审计方式**: 全量静态代码审查（后端 62 个 Python 文件、admin-web 32 个前端文件、enterprise-h5 46 个前端文件、9 个数据库迁移文件）+ 实际运行验证（应用导入、数据库连接、Alembic 迁移状态、pytest、临时启动 uvicorn、两个前端 `npm run build`）。
**审计范围**: `app/`（FastAPI 后端）、`admin-web/`（管理端 PC 前端）、`enterprise-h5/`（企业端 H5 前端）、`migrations/`、`scripts/`、`docs/`、根目录设计文档。
**审计原则**: 本报告只根据实际调用链路和运行结果给出结论，不以"存在某文件/某接口"直接判定功能已完成。本轮审计未修改任何业务代码。

---

## 目录

1. 项目概况
2. 技术栈
3. 项目目录及架构分析
4. 核心业务流程
5. 功能完成度清单
6. 前端检查结果
7. 后端检查结果
8. 数据库检查结果
9. 权限与安全检查
10. 前后端接口一致性检查
11. 运行/编译/测试验证结果
12. Docker 化准备度检查
13. 麒麟 V10 部署兼容性风险
14. 问题清单（P0/P1/P2/P3）
15. 尚未完成的功能清单
16. 技术债务清单
17. 推荐的后续开发顺序
18. 下一阶段 Claude Code 开发任务

---

## 1. 项目概况

本项目是威海市（文档中明确提到"环翠区企业综合服务中心"）企业服务中心系统，面向企业和政府工作人员两类用户，围绕**企业诉求、共享会议室、政企约见**三大业务板块，提供企业端在线申请（微信公众号 H5）与管理端后台办理（PC 后台）的完整业务闭环。系统按"多区县、多部门、多企服中心"架构设计，通过 `dataScope`（数据权限范围：ALL 全量 / REGION 区县 / DEPARTMENT 部门）实现数据隔离。

项目附带两份详细的中文设计文档（根目录 `企业服务中心系统需求边界确认稿.md` 与 `第一阶段数据库与后端接口设计说明.md`），本次审计以这两份文档作为"设计要求"基准，与实际代码逐项核对。**总体结论：这是一个已经过多轮真实迭代、业务逻辑深度显著高于"脚手架"水平的项目**，三大业务模块的状态机、审核流程、数据权限过滤、附件绑定、评价体系等均有真实的数据库读写与业务校验支撑，而非占位代码。但在**权限强制、部分模块的流程闭环收尾、生产安全加固、自动化测试和容器化部署**四个方面存在明确、可定位的缺口。

git 提交历史显示项目以"Auto sync"方式周期性归档（最近一次 2026-08-13），`docs/` 目录下的联调文档全部写于 2026-06-03，此后经历了 6 次同步提交，因此**文档相对当前代码存在滞后**（详见第 11 节）。

---

## 2. 技术栈

### 后端
- Python 3.11+（实测环境 3.12.3）
- FastAPI 0.111.0 + Uvicorn 0.29.0（ASGI）
- SQLAlchemy 2.0.30（Declarative + `Mapped`/`mapped_column` 新式写法）
- Alembic 1.13.1（数据库迁移，9 个迁移文件，链路完整）
- MySQL 8（`pymysql` 驱动，`utf8mb4` 字符集）
- 认证：`python-jose[cryptography]` 实现 JWT，双 Token 体系（企业端 / 管理端 `token_type` 区分）
- `passlib[bcrypt]` 在 `requirements.txt` 中声明，但**全仓库零引用**，属于死依赖（见 P3-2）

### 管理端前端（admin-web）
- Vue 3.4 + TypeScript 5.4 + Vite 5.3
- Element Plus 2.7（UI 组件库，全量引入未按需加载）
- Pinia 2.1（状态管理）+ Vue Router 4.3
- Axios 1.7

### 企业端前端（enterprise-h5）
- Vue 3.4 + TypeScript 5.4 + Vite 5.4
- Vant 4.9（移动端 UI 组件库，适配微信公众号场景）
- Pinia + Vue Router + Axios（与 admin-web 同构）

### 其他
- 无消息队列、无 Redis/缓存层、无定时任务框架（`APScheduler`/`Celery` 均未使用）
- 无前后端共用的 OpenAPI Client 生成（前端手写 API 封装）
- 无 Dockerfile / docker-compose / systemd unit / nginx 配置文件存在于仓库中

---

## 3. 项目目录及架构分析

```
app/
  main.py                # FastAPI 入口，CORS、异常处理器、健康检查、路由挂载
  core/                  # config(env读取)/database(engine+session)/security(JWT)/
                          # deps(依赖注入鉴权)/exceptions(统一错误码)/response(统一返回体)
  models/                # SQLAlchemy ORM：base/enterprise/system/appeal/meeting_room/gov_meeting
  schemas/                # Pydantic 请求/响应模型
  api/
    auth/                # 双 mock-login
    enterprise/          # 企业端接口（诉求/会议室/预约/政企约见）
    admin/                # 管理端接口（诉求/会议室/预约/政企约见/字典/日志/工作台）
    common/               # 字典查询、附件上传下载（无鉴权路由）
  services/              # 业务逻辑层（appeal/meeting_room/gov_meeting/dashboard + auth_adapter 预留）
  repositories/           # 数据访问层，按聚合根划分
  constants/              # 状态机常量 + 允许状态转移表
  utils/serial_no.py       # 每日流水号生成
migrations/versions/       # 9 个 Alembic 迁移（001~009，链路完整、无分叉）
admin-web/src/             # views(9个业务目录)/api/router/stores/layouts/utils
enterprise-h5/src/          # views/api/router/stores/utils（Vant 移动端组件）
scripts/                   # init_dict.py / init_demo_data.py / init_material_rules.py /
                            # test_api_flow.py + 3 个 curl 黑盒流程测试 .sh 脚本
tests/                     # 仅有空 __init__.py，无任何测试用例（见 11.4）
docs/                      # 7 份联调/部署文档（写于同一天，滞后于后续 6 次同步提交）
```

**架构评价**：后端分层清晰（api → service → repository → model），三大业务模块严格对称（每个模块都有独立的 service/repo/constants 文件），共用基础设施（企业档案、附件、评价、操作日志、字典）确实被三个模块共同复用，符合设计文档"十、后续开发原则"中"三大模块必须共用基础表"的要求。**未发现"为了图省事把三个模块糅进一个大文件"的反模式**，这是一个积极信号。

---

## 4. 核心业务流程

以下状态机均已与代码中的 `ALLOWED_STATUS_FOR_ACTION` 常量表逐条核对，标注了**实际可达性**（是否存在真实调用该转移的 API+Service 代码）：

### 4.1 企业诉求（Appeal）
```
待受理(PENDING_ACCEPT)
  → 退回补充(NEED_SUPPLEMENT) [✓可达，但企业端H5无响应入口，见 P1-9]
  → 不予受理(REJECTED) [✓可达]
  → 已受理(ACCEPTED)
      → 企服中心办理中(CENTER_HANDLING) [✓可达]
      → 部门办理中(DEPT_HANDLING) [✓可达]
          → 部门已反馈(DEPT_REPLIED) [✗常量已定义，代码从未设置该状态——DEPT_HANDLING 反馈后直接跳到 CENTER_REVIEWING]
          → 企服中心审核(CENTER_REVIEWING) [✓可达]
              → 审核退回(REVIEW_REJECTED) [✓可达]
              → 待评价(PENDING_EVALUATION) [✓可达]
                  → 已评价(EVALUATED) [✓可达]
                  → 已办结(COMPLETED) [✗全仓库无任何代码将状态置为 COMPLETED，终态不可达，见 P1-5]
```

### 4.2 共享会议室（Meeting Room Booking）
```
待提交 → 待审核(PENDING_AUDIT)
  → 退回补充材料(NEED_SUPPLEMENT) [✓可达，企业端有响应入口]
  → 审核驳回(REJECTED) [✓可达]
  → 审核通过(APPROVED) [✓可达，二次冲突校验]
      → 已取消(CANCELED) [✓可达，含提前时限校验]
      → 已完成(COMPLETED) [✓可达]
      → 爽约(NO_SHOW) [✓可达，累计2次自动禁用预约资格]
```
**该模块状态机完整闭环，是三个模块中实现最扎实的一个。**

### 4.3 政企约见（Gov Meeting）
```
企业提交 → 待审核(PENDING_AUDIT)
  → 退回补正(NEED_SUPPLEMENT) [✓可达]
  → 不予受理(REJECTED) [✓可达]
  → 受理通过 → 待安排(PENDING_ARRANGE) [✓可达]
      → 已安排(ARRANGED) [✓可达]
      → 待约见(WAIT_MEETING) [✓可达，confirm动作]
      → 约见完成(MEETING_COMPLETED) [✓可达]
          → 待评价(PENDING_EVALUATION) [✓可达——填写纪要时自动触发]
          → 已评价(EVALUATED) [✓可达]
          → 已办结(COMPLETED) [✓可达，finish 接口]
```
**该模块也完整闭环，是三个模块中唯一同时具备"完整闭环 + 全部管理端动作真正联调"的模块。**

**结论：诉求模块是三大模块中唯一存在"流程无法闭环"的模块**——已评价的诉求永远停留在 `EVALUATED`，没有任何操作能将其标记为 `COMPLETED`（已办结），这与需求文档 5.1.4 明确画出的状态图不符，也和会议室、政企约见两个模块形成对照（这两个模块都有对应的"完成/办结"动作）。

---

## 5. 功能完成度清单

| 模块 | 前端 | 后端 | 数据库 | 前后端打通 | 权限 | 状态流转 | 异常处理 | 占位/Mock | 完成状态 |
|---|---|---|---|---|---|---|---|---|---|
| 企业诉求-企业端 | Y | Y | Y | Y | 部分(仅IDOR层面，无角色) | 部分（补充材料无UI入口） | Y | 无 | **部分完成**——退回补充状态在H5端是死胡同 |
| 企业诉求-管理端 | Y | Y | Y | Y | 部分（数据权限仅列表生效，操作接口未校验；无角色校验） | 部分（终态COMPLETED不可达） | Y | 附件上传/下载2处显式TODO占位 | **部分完成** |
| 共享会议室-企业端 | Y | Y | Y | Y | 部分（同上IDOR模式，企业侧本身安全） | 已完成 | Y | 无 | **已完成**（三模块中最扎实） |
| 共享会议室-管理端 | Y | Y | Y | Y | 部分（同上） | 已完成 | Y | 台账导出为JSON非真实Excel（前后端均已标注TODO） | **基本完成**——缺日历可视化、真实导出 |
| 政企约见-企业端 | Y | Y | Y | Y | 部分（同上，企业侧安全） | 已完成 | Y | 无 | **基本完成** |
| 政企约见-管理端 | Y | Y | Y | Y | 部分（同上） | 已完成 | Y | 无 | **已完成** |
| 企业档案（共用） | — | Y | Y | Y | 企业侧安全 | N/A | Y | 无 | **已完成** |
| 附件体系（共用） | Y | Y | Y | Y | **无**（下载接口零鉴权） | N/A | Y | 无独立管理页面，TEMP孤儿记录无清理 | **部分完成**——功能可用但存在严重权限缺口 |
| 评价体系（共用） | Y | Y | Y | Y | 企业侧安全 | Y | Y | 无 | **已完成** |
| 消息记录（共用） | N | 模型存在 | Y(表存在) | **N** | — | — | — | **表定义后从未被任何service写入** | **仅有框架/占位** |
| 字典配置 | Y | Y | Y | Y | 无角色校验 | N/A | Y | 无 | **已完成** |
| 操作日志 | Y | Y | Y | Y | 无角色校验 | N/A | Y | ip_address/user_agent字段定义但从未写入 | **基本完成** |
| 统计分析/工作台 | Y | Y | Y | Y | 无角色校验 | N/A | Y | 真实数据，但无图表可视化，仅数字卡片 | **部分完成** |
| 台账导出 | Y | Y（stub） | — | Y（诚实提示） | — | — | Y | 明确TODO：JSON非Excel | **部分完成** |
| 用户/角色/权限管理 | **N** | **N** | 部分（role_codes/data_scope仅存于token快照） | — | — | — | — | 无任何维护界面或强制校验逻辑 | **未实现**（仅有数据字段，无管理能力，无强制执行） |
| 登录认证（企业端） | Y | Y（mock） | Y | Y | 符合一期设计允许 | N/A | Y | 自报身份，零验证，为一期文档明确允许的占位 | **仅有框架/占位**（按设计意图，但需在上线前替换） |
| 登录认证（管理端） | Y | Y（mock） | Y | Y | 符合一期设计允许 | N/A | Y | 自报角色+数据权限，零验证，且无环境网关 | **仅有框架/占位**（同上，风险更高） |

**统计口径与判断**：以上表格共列出 16 个功能条目（3 模块 × 2 端 = 6 + 8 个共用能力 + 2 个登录）。按"前后端已打通且状态流转在主路径上可闭环"为"已完成"标准：
- **已完成**：共享会议室-企业端、政企约见-管理端、企业档案、评价体系、字典配置 = 5 项
- **基本完成**：共享会议室-管理端、政企约见-企业端、操作日志 = 3 项
- **部分完成**：企业诉求-企业端、企业诉求-管理端、附件体系、统计分析、台账导出 = 5 项
- **仅有框架/占位**：消息记录、企业端登录认证、管理端登录认证 = 3 项
- **未实现**：用户/角色/权限管理 = 1 项

**不给整体百分比**——因为"完成度"在权限维度和"完成度"在业务流程维度是两个不同轴线，简单平均会掩盖"业务闭环基本做完，但权限体系几乎为零"这一最关键的结论。真正需要向决策者传达的是：**三大业务的"钱"（数据读写、状态流转、审核动作）已经花在了刀刃上，但"锁"（谁能做这些动作）几乎没有安装**。

---

## 6. 前端检查结果

### 6.1 admin-web（管理端 PC）
- `vue-tsc` 类型检查 0 错误，`npm run build` 构建成功（产物 1.19MB / gzip 384KB，超过 Vite 500KB 建议阈值，因未做按需加载/代码分割）。
- 诉求/会议室/预约/政企约见/字典/日志/工作台**全部页面都真实调用后端接口**，未发现用假数组冒充列表数据的情况。
- **最重要的发现**：全项目搜索路由守卫、菜单渲染、按钮 `v-if` 均未发现任何基于 `roleCodes` 的权限判断（`router/index.ts` 只判断 token 是否存在）。所有操作按钮仅按"业务状态"决定是否可点击，不按"当前登录角色"决定。
- 登录页 `dataScope` 下拉选项（NATIONAL/PROVINCE/REGION/DISTRICT/CENTER）与后端实际识别的值（`REGION`/`DEPARTMENT`/`SELF`，其余一律退化为不限权限的 `ALL`）不一致，选择"区县"以外的选项会导致**该用户获得比UI提示更大的数据可见范围**。
- 诉求详情页附件下载按钮硬编码 `disabled` 并注释 `TODO: 文件下载接口`（尽管接口本身可用），企服中心办理/部门反馈弹窗附件上传功能同样标注"待完善 TODO"。
- 会议室预约台账导出调用真实接口，但后端路由自身注释为 `TODO：改为真实Excel`，当前只回显 JSON；前端诚实地用提示告知用户，未伪装成"已完成"。
- 无会议室日历（日/周/月视图），无统计图表库依赖，无独立附件管理页面，无用户/角色/权限管理页面。

### 6.2 enterprise-h5（企业端 H5）
- `vue-tsc` + `vite build` 构建成功，无类型错误、无警告。
- 诉求提交/列表/详情/评价、会议室列表/详情/预约/取消/补充材料、政企约见发起/列表/详情/评价均真实联调后端，会议室预约的"提前2天/周末禁约/30分钟起/4小时上限/时段冲突校验"等业务规则**在前端真实实现**，非仅文案提示。
- **诉求补充材料功能完全缺失**：后端存在 `POST /api/enterprise/appeals/{id}/supplement`，前端 `api/appeal.ts` 无对应调用函数，`AppealDetail.vue` 无任何入口。诉求被退回补充后，企业用户在 H5 端**无法响应**，该分支状态机在企业端是死胡同（管理端可以看到，但企业侧无法操作）。
- 须知/规则路由（`MeetingRoomRules`、`GovMeetingNotice`）被错误设置为 `requiresAuth: true`，与需求"须知、规则、常见问题查看无需登录"矛盾；且**全项目没有"常见问题"页面/路由**，这是一个被完全遗漏的必需页面。
- 诉求提交无附件上传 UI（需求允许非必填，但应可上传），配合上一条"无补充材料入口"，导致诉求附件在企业端事实上不可用。
- `MockLogin.vue` 中 `console.log`/`console.error` 未做开发环境判断，会在生产构建中把法人身份证号、手机号等 PII 及登录 token 明文打印到浏览器控制台。
- 微信身份认证：确认为纯 mock-login，无真实 JS-SDK/OAuth 代码，`handleProvincialAuthCallback()` 直接抛出"尚未对接"异常——符合需求文档允许的一期范围，但需在下节安全审查中作为生产阻断项对待。

---

## 7. 后端检查结果

### 7.1 认证与依赖注入（app/core/deps.py, security.py）
- 双 Token 体系设计合理（`token_type` 区分企业/管理端，防止跨端误用）。
- **`get_current_admin` 只校验 JWT 签名和 `token_type == "admin"`，从不校验 `role_codes`/`data_scope` 与后端任何记录的一致性**——token 在其有效期内（最长480分钟）携带的角色和数据权限完全由登录时客户端自报的值决定，见第9节 P0/P1。

### 7.2 三大业务 Service/Repository 层
- 三个模块的 Service 类都遵循"取对象 → 状态前置校验(`_check_status`) → 更新 → 写审核轨迹(`AppealRecord`/`MeetingRoomBookingAudit`/`GovMeetingAudit`) → 写操作日志(`SysOperationLog`) → `commit`"的统一模式，**审批、受理、退回、分派、回复、评价均有留痕**，符合需求文档"九、开发原则"第9条。
- 会议室模块的材料规则支持"区划+企服中心精确 → 区划通用 → 企服中心通用 → 全局通用 → 兼容旧room_id"五级优先级合并逻辑（`_merge_material_rules_tiered`），实现复杂度和完整度超出典型一期项目预期。
- **系统性问题**：三个模块的管理端"列表"接口都实现了 `data_scope`/`region_code` 过滤，但**几乎所有"详情"和"操作"接口（受理/退回/分派/审核/安排/办结/驳回等）都是直接按主键 `get_by_id` 取记录，不做任何数据权限校验**——这是一个横跨全部三个模块、由代码模式一致性验证过的系统性缺陷，详见第9节 P1-1。
- 诉求模块缺少"办结"动作对应的 Service 方法和 API 路由（对比会议室的 `complete_booking`、政企约见的 `finish_apply`）。

### 7.3 附件与通用接口（app/api/common/router.py）
- 上传接口：服务端真实校验文件大小上限（读取到内存后校验，见 P2-2），使用 UUID 生成存储文件名（避免路径穿越），但**扩展名/MIME类型无白名单**，直接信任客户端。
- **下载接口 `download_attachment` 完全没有任何鉴权依赖**——对比同文件中的上传接口有 `_get_uploader` 依赖，下载接口是唯一的"裸奔"路由。附件主键为自增 `BigInteger`，天然可枚举。这是本次审计发现的最高优先级问题之一（P0）。

### 7.4 序列号生成（app/utils/serial_no.py）
- `generate_daily_serial` 采用"查询当日最大流水号 → +1 → 返回"的非原子模式，未使用 `SELECT ... FOR UPDATE` 或数据库自增序列。在并发提交场景下，两个几乎同时到达的请求可能读到相同的 `max_seq`，导致生成相同的 `appeal_no`/`booking_no`/`apply_no`，触发唯一约束冲突，最终被通用异常处理器吞掉返回"系统异常，请稍后重试"——**用户侧表现为提交失败但不知道具体原因，且没有自动重试机制**。

### 7.5 会议室预约冲突校验的竞态窗口
- `submit_booking`/`approve_booking` 都会调用 `_check_booking_conflict`，但该校验基于普通 `SELECT`，未加行锁。理论上两个管理员在极短时间窗口内同时审核通过两个时间冲突的预约申请，均可能在各自事务提交前通过冲突校验，从而产生两条状态为 `APPROVED` 且时间重叠的预约记录。发生概率低（需要人工并发操作），但确实是设计层面的竞态窗口。

---

## 8. 数据库检查结果

- **迁移链路完整**：`001 → 002 → 003 → 004 → 005 → 006(gov_meeting_fields_extend) → 007(gm_enterprise_fields) → 008(meeting_room_image) → 009(booking_enterprise_type)`，`revision`/`down_revision` 逐一核对无分叉、无缺失环节。实际执行 `alembic current` 确认数据库处于 `009`（head），与迁移文件目录完全一致，**无需人工手动建表**（`init_dict.py`/`init_demo_data.py`/`init_material_rules.py` 仅用于初始化数据，非建表）。
- 主键统一为 `BigInteger` 自增；业务主表（`appeal_main`/`meeting_room_booking`/`gov_meeting_apply`）均有唯一编号字段（`appeal_no`/`booking_no`/`apply_no`，`unique=True`）——但生成逻辑存在竞态（见7.4），一旦冲突会在应用层报错而非在数据库层无声失败，这点是好的（约束确实生效），但用户体验会受影响。
- 索引覆盖合理：区域码、状态、企业ID、信用代码、提交时间等高频查询字段基本都建了索引（如 `ix_appeal_main_region_code`、`ix_appeal_main_status` 等），未发现明显的全表扫描风险点。
- 软删除字段（`deleted_flag`）在绝大多数表中存在并在查询中被正确使用（`filter(..., deleted_flag == 0)`），但个别表如 `MeetingRoomBookingAudit`、`GovMeetingAudit`、`AppealRecord`（审计流水表）没有软删除字段——这是合理设计（审计记录不应允许删除），不是缺陷。
- `SysOperationLog` 表定义了 `ip_address`/`user_agent` 字段，但全仓库检索确认**没有任何调用点填写这两个字段**，永远为 `NULL`——数据模型比实际实现更完整，是典型的"设计先行、实现未跟上"案例。
- 与设计文档 7.1 节对照：文档列出的 `sys_department_snapshot`（部门快照表）在当前实现中未单独建表，而是将 `department_id`/`department_name` 直接内嵌进 `sys_user_snapshot`——功能上等价（部门信息本身就是快照，无需独立维护部门主数据），属于合理简化，非缺陷。
- 未发现孤儿数据风险的主要业务表（外键关系均通过应用层保证一致性，如 `appeal_id`/`booking_id`/`apply_id` 均由本系统生成后写入，不存在跨系统悬空引用）；但**附件表存在真实的孤儿数据风险**：上传接口先创建 `business_type="TEMP"` 的附件记录，只有在后续提交业务表单时才通过 `bind_attachments` 更新为正式业务类型；如果用户上传后放弃提交，该记录和对应的物理文件永久留存，没有任何定时清理任务或手动清理入口。

---

## 9. 权限与安全检查

> 完整分级问题清单见第14节；本节做归纳性说明，具体问题不再重复列出证据（详见对应编号）。

- **认证边界**：企业端/管理端登录目前均为"自报身份"的 mock-login，符合需求文档一期允许范围，但代码层面**没有任何环境变量网关**（如 `if settings.app_env == "production": raise`）能够阻止这两个接口在生产环境被误用，这是本次审计认定的最高优先级问题（P0-1）。
- **鉴权 vs 授权的落差**：`get_current_admin`/`get_current_enterprise` 解决的是"你是谁端"的问题（Authentication），完全没有解决"你能做什么"的问题（Authorization）。`role_codes` 字段存在、被前端登录表单收集、被写入 JWT，但从登录到具体业务操作的全链路中，**没有任何一处代码读取并校验它**。
- **数据权限（IDOR）**：三大模块的管理端"列表"接口有 `data_scope` 过滤，但"详情/操作"接口没有——这是本次审计通过交叉验证（后端 fork 发现诉求模块、独立的安全审计 agent 验证会议室与政企约见模块完全一致）确认的系统性问题，不是单个接口的疏漏。
- **附件下载零鉴权**：见 7.3，可导致企业身份证件、诉求材料等敏感文件被匿名批量下载。
- **密钥管理**：`.env` 中的 `APP_SECRET_KEY` 当前仍是 `.env.example` 中的占位文本，未针对本环境定制；`app/core/config.py` 在环境变量完全缺失时还会静默回退到硬编码的 `"dev-secret-key"`。该密钥同时签发企业端和管理端 Token，一旦泄露等价于可伪造任意角色的管理员身份。
- **文件上传**：无扩展名/内容类型白名单，信任客户端 `Content-Type`；大小限制在读取全部内容之后才校验，存在内存膨胀型 DoS 风险。
- **SQL注入**：全仓库检索确认所有数据访问都通过 SQLAlchemy ORM 查询构造器完成，未发现任何原生 SQL 拼接，**未发现SQL注入风险**。
- **CORS**：当前配置为开发环境白名单（localhost 各端口 + 内网 `10.x.x.x` 正则），`allow_credentials=False`，**配置本身安全**，但需要在生产部署时替换为实际域名（属于部署事项非漏洞）；`docs/ADMIN_WEB_DEBUG.md` 中描述的"`allow_origins=["*"]`"与当前代码不符，属于文档滞后。
- **CSRF**：两端 Token 均通过 `localStorage` 存储 + `Authorization: Bearer` 头传输，不依赖 Cookie 自动携带，经典 CSRF 攻击面很小；代价是 Token 面临 XSS 窃取风险（与上传接口的文件类型缺口存在潜在叠加效应）。
- **默认账号/弱口令**：系统没有传统意义上的"默认管理员账号+密码"，因为压根没有密码机制——这既是"没有弱口令"，也是"没有任何口令"，需要辩证看待（详见 P0-1）。
- **Swagger暴露**：`/docs`、`/openapi.json`、`/redoc` 均无鉴权网关，生产环境应关闭或加访问控制。
- **信息泄露**：全局异常处理器（`generic_exception_handler`）返回固定的"系统异常，请稍后重试"，**不泄露堆栈信息**，这一点做得规范。

---

## 10. 前后端接口一致性检查

对 admin-web、enterprise-h5 的全部 API 调用文件逐一与后端路由做了路径、方法、字段名比对，结论：

- **admin-web**：全部接口调用均能在后端找到路径、方法一致的路由，**没有发现前端调用不存在的接口，也没有发现后端路由完全无人调用的孤儿接口**（除了本身就是后续对接用的 `/api/enterprise/*` 相关接口不适用比对）。仅有的差异是语义性的：会议室新建接口发送 `imageAttachmentIds` 字段在导出的 TS 请求类型中未声明（但因未走字面量对象类型检查，不影响运行时和构建）。
- **enterprise-h5**：同样整体一致，唯二的"孤儿后端路由"是 `PUT /api/enterprise/appeals/{id}`（修改诉求）和 `PUT /api/enterprise/gov-meetings/{id}`（修改约见）——后端已实现但前端未调用；诉求补充材料接口 `POST /api/enterprise/appeals/{id}/supplement` 同样是孤儿路由（对应第6.2节的功能缺失）。
- 两个前端都在早期迭代中出现过"诉求评价用 `/evaluation`、约见评价用 `/evaluate`"这种不对称路径命名，但**当前代码已经正确处理并在注释中标注**，不构成实际缺陷。
- enterprise-h5 的 `meetingRoom.ts`/`govMeeting.ts` 中存在大量 camelCase/snake_case 双字段兼容读取代码（`s()`/`rn()`/`bn()` 等辅助函数），这是历史上前后端字段命名不一致遗留的技术债，当前用兼容层掩盖而非根治。

**结论：接口契约层面的一致性总体良好，唯二实质性缺口是诉求模块的"补充材料"和"修改诉求"两个接口在企业端前端完全没有入口**，其余问题均为已被开发者自行发现并注释说明的历史遗留问题，不影响当前功能可用性。

---

## 11. 运行/编译/测试验证结果

以下均为**实际执行**结果，非静态推断：

| 验证项 | 命令 | 结果 |
|---|---|---|
| MySQL 连通性 | socket connect 127.0.0.1:3306 | **成功**（返回0），后续DB相关验证均为真实验证，非"未验证" |
| 应用可导入性 | `python -c "from app.main import app"` | **成功**，`routes=87`，无异常 |
| Alembic 迁移状态 | `alembic current` / `alembic history` | **成功**，head=`009_booking_enterprise_type`，与9个迁移文件一一对应，无待迁移项 |
| 自动化测试 | `pytest tests/ -q` | **失败**——venv 中未安装 pytest，且 `tests/` 目录下只有空的 `__init__.py`，**没有任何测试用例文件**，即便安装 pytest 也是"0 测试可收集"状态 |
| 临时启动服务 | `uvicorn app.main:app` 后 curl `/docs`、`/openapi.json` | **成功**，`/docs`返回200，日志全程无 WARNING/ERROR，启动与关闭均干净 |
| Python/Node版本 | `--version` | Python 3.12.3、Node v24.18.1、npm 11.16.0（均满足或超过文档建议版本） |
| 依赖漂移 | `pip freeze` vs `requirements.txt` | 显式依赖版本齐全无缺失，多余包均为正常传递依赖，**无版本冲突** |
| admin-web构建 | `npm run build` | **成功**（14.57s），仅有第三方库无害警告和500KB chunk提示 |
| enterprise-h5构建 | `npm run build` | **成功**（7.38s），无警告无错误 |

**静态代码检查通过 + 运行验证通过**的项：应用启动、数据库连接、迁移状态、两个前端构建。
**运行验证发现问题**的项：项目事实上没有可运行的自动化测试套件——`FULL_FLOW_TEST_REPORT.md` 中提到的"测试"实际是 `scripts/test_api_flow.py` 与三个 `.sh` 脚本这类需要手动启动服务器、手动跑通的黑盒验证脚本，而不是可在 CI 中自动运行、可重复回归的单元/集成测试。

**文档滞后核查**：`docs/` 全部7份文档写于2026-06-03同一天，此后代码经历6次同步提交（06-18/07-09/07-15/07-16/07-27/08-13）。经比对：
- `API_TESTING.md`/`DEPLOY_KYLIN_V10.md` 的迁移版本表和路由清单**未收录 005~009 号迁移**及后续新增的"服务中心管理"接口组，属于文档滞后。
- `FULL_FLOW_TEST_REPORT.md` 声称的"全流程测试通过"覆盖的会议室材料规则相关代码在其之后又发生过改动（字段增加、参数语义变化），报告结论**不能代表当前代码已重新验证过**，只能作为历史记录看待。
- `DEPLOY_KYLIN_V10.md` 相对最诚实——开篇即声明"当前仓库未发现 Dockerfile/Nginx配置/systemd单元文件"，与实际仓库状态完全一致，不存在虚报。

---

## 12. Docker 化准备度检查

| 检查项 | 状态 | 依据 |
|---|---|---|
| 数据库配置外部化 | ✅ 完全通过 | `config.py` 全部字段通过 `pydantic-settings` 读环境变量，无硬编码生产地址 |
| 数据库字符集/连接串 | ✅ 通过 | `database_url` 固定拼接 `?charset=utf8mb4` |
| 上传目录可配置 | ✅ 通过（有健壮性设计） | `UPLOAD_DIR` 环境变量 + `upload_dir_resolved` 属性将相对路径解析为**基于项目根目录**的绝对路径，不依赖进程 cwd |
| 日志目录可配置 | ⚠️ 不通过 | 未发现任何日志文件/目录相关的环境变量或配置项，完全依赖 systemd journal（`DEPLOY_KYLIN_V10.md`自己也确认这点），不符合容器化"日志应可挂载卷或输出到stdout"的标准做法（Uvicorn 默认输出到 stdout 尚可，但没有结构化/可配置的落盘日志方案） |
| 前端API地址可配置 | ✅ 通过，但有缺口 | 两端均支持 `VITE_API_BASE_URL` 构建期注入；`admin-web` 有 `.env.production`（值为占位域名，需要部署时替换）；**`enterprise-h5` 缺少 `.env.production` 文件**，需部署时手动新建 |
| Windows路径/大小写依赖 | ✅ 未发现问题 | 全仓库无 Windows 风格路径，统一用 `pathlib.Path` |
| 时区处理 | ✅ 一致 | 全仓库统一使用 `datetime.utcnow()`，未发现与 `datetime.now()` 混用；但前端展示层是否做了时区换算未在本次范围内核实 |
| 字符编码 | ✅ 通过 | 数据库连接、迁移建表 SQL 均为 `utf8mb4` |
| 健康检查端点 | ✅ 存在且无需鉴权 | `/api/health` 与 `/api/common/health` 均可直接用于容器编排存活/就绪探针 |
| Dockerfile / docker-compose | ❌ 不存在 | 全仓库检索确认没有任何 Dockerfile/docker-compose 文件 |
| systemd unit / nginx 配置 | ❌ 不存在 | `DEPLOY_KYLIN_V10.md` 提供的是**文档内模板**，需部署时手动创建，仓库中没有对应文件落地 |
| 服务启动顺序/依赖等待 | ❌ 未设计 | 应用启动时不会等待 MySQL 就绪（无重试/健康检查等待逻辑），容器化后如果 DB 容器启动慢于 App 容器，首次启动会直接连接失败退出 |
| 数据持久化 | ⚠️ 需规划 | `uploads/` 目录和 MySQL 数据目录都需要显式声明为 Docker Volume，当前无任何 `.dockerignore`/卷声明相关文件 |

**结论**：应用代码本身的"可配置性"已经为容器化做好了基础准备（配置外部化、路径解析健壮、健康检查齐全），**真正缺失的是容器化的"最后一公里"工件**——Dockerfile、compose 编排、启动顺序控制、日志落盘方案，这些目前完全不存在，需要从零编写。

---

## 13. 麒麟 V10 部署兼容性风险

1. **无 Windows 路径依赖，无大小写敏感问题** —— 代码层面对 Linux（含国产化发行版）友好，未发现需要专门适配麒麟 V10 的路径/编码问题。
2. **Python/Node 版本依赖需要在麒麟 V10 上确认可用源**：麒麟 V10 默认软件源的 Python3/Node 版本可能低于开发环境实测的 3.12/Node24，需要确认目标机可以通过 `pyenv`/`nvm` 或容器方式获得 Python 3.11+ 和 Node 18+（这是环境问题，非代码问题）。
3. **MySQL 8 在国产化环境的兼容性**需要单独验证——麒麟 V10 官方仓库对 MySQL 8 的支持程度、或是否需要改用达梦/人大金仓等国产数据库，这是一个业务决策问题，当前代码通过 SQLAlchemy + pymysql 访问，**理论上迁移适配层工作量可控**，但需要提前规划测试窗口。
4. **日志方案在国产化 Docker 场景下的短板**（见12节）会被放大：如果麒麟 V10 上使用的容器运行时（如 iSulad）对 journal 日志的采集方式与标准 Docker 不同，当前"完全依赖 systemd journal"的日志方案可能需要额外适配。
5. **无服务启动顺序控制**在国产化环境下（虚拟化/容器化性能与标准 x86 环境可能有差异）更容易暴露——建议提前加入数据库连接重试逻辑。
6. **无 CI/CD、无自动化测试**意味着"迁移到麒麟 V10 环境是否引入回归"目前只能靠人工回归测试来保证，风险高于有自动化测试覆盖的项目。

---

## 14. 问题清单（P0/P1/P2/P3）

### P0（阻断性问题）

**P0-1｜模块：登录认证（企业端+管理端）**
- 问题：`enterprise_mock_login`/`admin_mock_login` 接受客户端自报的任意身份信息（管理端甚至包括 `roleCodes`、`dataScope`）签发正式 JWT，全程零验证，且代码中**没有任何环境网关**能阻止其在生产环境被访问。
- 证据：`app/api/auth/router.py:16-120`；`app/core/deps.py:23-45`（`get_current_admin` 只验证签名和 `token_type`，不回查角色）。
- 涉及文件/函数：`app/api/auth/router.py::enterprise_mock_login/admin_mock_login`、`app/core/deps.py::get_current_admin`。
- 影响：任何具备网络访问权限的人可自签发 `dataScope=ALL`、`roleCodes=["SUPER_ADMIN"]` 的管理员 Token，完全接管系统；对已存在的 `platformUserId` 重复登录还会**覆盖写入**该账号存储的角色/区域/部门信息，造成持久化的权限篡改。
- 建议：短期在 `settings.app_env == "production"` 时硬性关闭两个 mock-login 路由（返回404或直接不注册路由）；中长期按需求文档要求接入省级统一身份认证 / 政务服务平台统一用户体系。
- 是否影响Docker/麒麟V10部署：**是**——必须在生产镜像的配置/构建阶段就确保该网关生效，不能依赖运维手工记得关闭。

**P0-2｜模块：附件体系（共用）**
- 问题：附件下载接口 `download_attachment` 没有任何鉴权依赖，附件主键为可枚举的自增整数。
- 证据：`app/api/common/router.py:134-150`（对比同文件 `upload_attachment` 在66行有 `Depends(_get_uploader)`，下载接口完全没有等价依赖）。
- 涉及文件/函数：`app/api/common/router.py::download_attachment`。
- 影响：任何未登录的第三方可以枚举 `attachment_id` 批量下载系统内全部附件，包括企业法人身份证扫描件、会议室申请表盖章件、诉求佐证材料等敏感个人信息与商业信息，构成规模化个人信息泄露风险。
- 建议：为该路由增加 `CurrentEnterprise | CurrentAdmin` 依赖，并在业务层校验调用方是否为该附件 `business_type`/`business_id` 的所有者或有权限的管理端角色。
- 是否影响Docker/麒麟V10部署：**是**——该漏洞与部署环境无关，只要接口对外可达即可被利用，必须在任何环境上线前修复。

### P1（高优先级）

**P1-1｜模块：企业诉求/共享会议室/政企约见-管理端（系统性）**
- 问题：三大模块管理端的"详情查看"和全部"操作类"接口（受理/退回/不予受理/分派/办理/反馈/审核/批准/驳回/安排/确认/办结/爽约等）均直接按主键取记录，不做 `data_scope`/`region_code`/`department_id` 校验，仅"列表"接口做了过滤。
- 证据：`app/repositories/appeal_repo.py:22-26`（`get_by_id` 无scope参数，被 `assign_dept` 等方法使用）；`app/services/meeting_room_service.py` 的 `approve_booking`(958)/`reject_booking`(978)/`complete_booking`(1004)/`no_show_booking`(1024) 及 `app/services/gov_meeting_service.py` 的 `audit_apply`(383)/`arrange_apply`(458)/`confirm_apply`(544)/`finish_apply`(633) 均调用无 scope 参数的 `get_by_id`/`get_apply_by_id`。
- 影响：区县级管理员理论上可以直接对其他区县的诉求/预约/约见执行受理、驳回、办结等操作（越权访问/IDOR），只要能猜到或获取到对方的数字ID（自增主键，可枚举）。
- 建议：在上述所有 Service 方法中增加 `data_scope`/`current_region_code`/`current_dept_id` 参数并在取记录后立即校验，越权则抛 `ForbiddenException`；建议抽取为统一的 `assert_in_scope(record, operator)` 工具函数供三个模块共用，避免再次出现遗漏。
- 是否影响Docker/麒麟V10部署：否（纯逻辑问题，与部署环境无关，但应在上线前修复）。

**P1-2｜模块：权限体系（全栈系统性）**
- 问题：`role_codes` 字段在登录时被收集、写入数据库、写入JWT，但从后端 `deps.py` 到 admin-web 前端路由/菜单/按钮，**全链路没有任何一处代码读取并校验它**。
- 证据：`app/core/deps.py` 全文搜索 `role_codes` 无匹配；`admin-web/src/router/index.ts:93-101` 仅判断 `getToken()`；`admin-web/src/layouts/AdminLayout.vue:8-48` 无条件渲染全部菜单。
- 影响：任何通过 mock-login 获得有效 Token 的身份，无论自报角色是什么（哪怕自称"只读查询员"），都能在前端UI上直接执行受理、驳回、字典增删、会议室启停等任意管理端操作。
- 建议：至少实现基于 `role_codes` 的功能级权限校验中间件（后端）+ 路由/按钮级 `v-if` 权限指令（前端），二者缺一不可（只做前端会被绕过接口直接调用，只做后端会导致UI体验与实际权限不符）。
- 是否影响Docker/麒麟V10部署：否。

**P1-3｜模块：企业诉求**
- 问题：诉求状态机缺少"办结"（COMPLETED）动作的 Service 方法和 API 路由，`EVALUATED` 是事实上的终态，与需求文档 5.1.4 的状态图（…已评价 → 已办结）不符；对照会议室的 `complete_booking`、政企约见的 `finish_apply`，诉求模块是唯一缺失终态收尾动作的模块。
- 证据：`app/services/appeal_service.py` 全文搜索无 `COMPLETED` 赋值语句；`app/constants/appeal.py` 中 `AppealAction.COMPLETE` 常量已定义但 `ALLOWED_STATUS_FOR_ACTION` 字典中没有对应条目，`app/api/admin/appeals.py` 无 `/complete` 路由。
- 影响：所有已评价的诉求在统计报表中会一直计入"待办结"或需要靠 `EVALUATED` 状态强行代表"已结束"，无法真正归档，管理端无法准确统计"当期已办结数量"。
- 建议：新增 `AppealAction.COMPLETE` 对应的 `ALLOWED_STATUS_FOR_ACTION` 条目（`[EVALUATED]` 或 `[REPLIED, PENDING_EVALUATION, EVALUATED]`）、`AppealService.complete_appeal()` 方法与 `POST /api/admin/appeals/{id}/complete` 路由，比照 `finish_apply` 实现。
- 是否影响Docker/麒麟V10部署：否。

**P1-4｜模块：企业诉求-企业端H5**
- 问题：诉求"补充材料"功能在企业端H5完全没有实现，后端接口存在但前端无调用入口。
- 证据：`app/api/enterprise/appeals.py:72`（`POST /{appeal_id}/supplement` 路由存在）；`enterprise-h5/src/api/appeal.ts` 无对应函数；`enterprise-h5/src/views/appeal/AppealDetail.vue` 无补充材料入口按钮。
- 影响：诉求被管理端"退回补充"后，企业用户在移动端**无法响应**，该诉求实质上被卡死，只能等管理端线下沟通后强行推进流程或代为处理。
- 建议：在 `AppealDetail.vue` 增加补充材料表单（复用 `MeetingRoomBooking` 补充材料页面的实现模式），对接已有后端接口。
- 是否影响Docker/麒麟V10部署：否。

**P1-5｜模块：安全/密钥管理**
- 问题：`.env` 中 `APP_SECRET_KEY` 的值仍是 `.env.example` 中的占位文本，未针对当前环境定制；`app/core/config.py` 在环境变量缺失时还会静默回退到硬编码字符串。
- 证据：`.env:3` 与 `.env.example:3` 值一致（不在报告中复述具体值）；`app/core/config.py:11` `Field("dev-secret-key", env="APP_SECRET_KEY")`。
- 影响：该密钥同时签发企业端和管理端全部 JWT，一旦以任何方式泄露（如误将 `.env` 打入镜像、误提交等），攻击者可伪造任意角色的管理员 Token，且无需依赖 P0-1 的 mock-login 接口是否开放。
- 建议：生产环境使用长随机字符串并通过 K8s Secret / 环境变量注入；在 `Settings` 中增加校验，当 `app_env == "production"` 且 `app_secret_key` 等于默认值时启动阶段直接 `raise`，防止误上线。
- 是否影响Docker/麒麟V10部署：**是**——必须在容器化部署方案中通过 Secret 管理机制解决，不能依赖 `.env` 文件被正确替换的"人工纪律"。

**P1-6｜模块：附件体系**
- 问题：文件上传接口对扩展名/内容类型没有任何白名单校验，`file.content_type` 直接来自客户端且被信任存入数据库、下载时原样作为 `media_type` 返回。
- 证据：`app/api/common/router.py:88-90`（`ext = os.path.splitext(original_name)[1].lower()`，无校验）。
- 影响：结合 P0-2（下载零鉴权），攻击者可上传任意类型文件并让受害者通过链接直接访问；虽然当前 Starlette `FileResponse` 默认走 `attachment` 方式下载（缓解了直接渲染风险），但仍建议加固。
- 建议：增加允许的扩展名/MIME类型白名单（pdf/doc/docx/jpg/png等业务相关类型），并对内容做真实类型嗅探而非只信任声明的 `Content-Type`。
- 是否影响Docker/麒麟V10部署：否。

**P1-7｜模块：admin-web登录/数据权限**
- 问题：登录页 `dataScope` 下拉选项（`NATIONAL`/`PROVINCE`/`REGION`/`DISTRICT`/`CENTER`）与后端实际识别的值（`REGION`/`DEPARTMENT`/`SELF`，其余一律退化为不限权限）不一致。
- 证据：`admin-web/src/views/login/Login.vue:41-47`；后端分支判断见 `app/services/dashboard_service.py:20-40`、`app/repositories/appeal_repo.py:89-91` 等，均只识别 `"REGION"`/`"DEPARTMENT"`/`"SELF"`。
- 影响：操作员选择"区县"以外任意选项（如误以为"DISTRICT"更精细），实际获得的是**不受限的全量数据访问权限**，与UI呈现的"更小范围"语义完全相反，属于严重的权限认知错配。
- 建议：登录表单下拉选项与后端 `data_scope` 枚举值严格对齐，并在后端对未识别的 `data_scope` 值做默认拒绝（而非默认放行）处理。
- 是否影响Docker/麒麟V10部署：否。

**P1-8｜模块：预约/流水号生成（并发）**
- 问题：`generate_daily_serial` 采用"查最大值+1"非原子模式生成业务编号。
- 证据：`app/utils/serial_no.py:6-23`。
- 影响：高并发提交场景下（例如活动通知后大量企业同时提交诉求/预约），存在生成重复编号导致数据库唯一约束冲突、请求失败的可能性，且失败后无重试机制，用户只能重新点击提交。
- 建议：改为数据库自增序列表 + `SELECT ... FOR UPDATE`，或使用带时间戳+随机数的编号方案规避序列竞争。
- 是否影响Docker/麒麟V10部署：否（但高并发场景在生产更容易触发，建议上线前修复）。

**P1-9｜模块：消息记录（共用能力）**
- 问题：`SysMessageRecord` 表已建模，但全仓库检索确认**没有任何 Service/Repository 代码创建过该表的记录**。
- 证据：`grep -rn "SysMessageRecord" app/` 仅命中 `models/__init__.py` 和 `models/system.py` 的定义处，服务层零引用。
- 影响：需求文档明确要求的"提交成功/退回补正/不予受理/受理通过/约见安排/约见完成/待评价提醒"等站内消息通知场景**完全没有实现**，企业和管理端工作人员无法通过系统获知状态变化，只能靠主动刷新列表页面。
- 建议：在三大模块状态流转的关键节点（如 `accept_appeal`/`reject_booking`/`arrange_apply` 等）补充调用一个统一的 `MessageService.notify(...)`，写入 `SysMessageRecord`，管理端/企业端各自增加"消息中心"页面展示未读消息。
- 是否影响Docker/麒麟V10部署：否。

### P2（中优先级）

| 编号 | 模块 | 问题 | 涉及文件 | 建议 |
|---|---|---|---|---|
| P2-1 | 共享会议室 | 预约审批冲突校验存在TOCTOU竞态窗口（SELECT无行锁） | `app/services/meeting_room_service.py::approve_booking`(958) | 加 `SELECT...FOR UPDATE` 或数据库层唯一约束辅助 |
| P2-2 | 附件体系 | 上传文件大小限制在读取全部内容到内存后才校验，存在内存膨胀DoS风险 | `app/api/common/router.py:72-76` | 用 `Content-Length` 预检或分块读取+提前中止 |
| P2-3 | 附件体系 | 扩展名从客户端文件名截取未做字符集限制，极端构造文件名有理论路径拼接风险 | `app/api/common/router.py:89-93` | 白名单校验 `ext` 为 `\.[A-Za-z0-9]{1,10}` |
| P2-4 | 全局 | 无任何接口限流/防暴力机制 | 全局 | 网关层或应用层加限流中间件 |
| P2-5 | 全局 | `/docs`/`/openapi.json` 生产环境无网关 | `app/main.py` | `app_env==production` 时置空 `docs_url`等 |
| P2-6 | 共享会议室-管理端 | 台账导出为JSON非真实Excel/CSV文件 | `app/api/admin/meeting_bookings.py:80`；`admin-web/.../BookingList.vue:264-271` | 用 `openpyxl`/`pandas` 生成真实文件流 |
| P2-7 | 企业诉求-管理端 | 附件下载/上传在诉求详情页显式TODO禁用 | `admin-web/.../AppealDetail.vue:104,263,302` | 补齐 `el-upload`/下载链接，复用会议室模块已有实现 |
| P2-8 | 共享会议室-管理端 | 无日/周/月日历可视化视图 | `admin-web/.../RoomList.vue` | 引入日历组件展示时段占用 |
| P2-9 | 统计分析 | 工作台无图表可视化，仅数字卡片 | `admin-web/.../Dashboard.vue` | 引入 echarts 等图表库 |
| P2-10 | 附件体系 | 无独立附件管理页面，无用户/角色/权限管理页面 | 前后端均无对应模块 | 视业务优先级排期，权限管理页面建议提前 |
| P2-11 | 企业端H5 | 须知/规则页面错误要求登录；无"常见问题"页面 | `enterprise-h5/src/router/index.ts:58-61,87-91` | 去掉这两个路由的 `requiresAuth`；新增FAQ页面 |
| P2-12 | 企业端H5 | `MockLogin.vue` console输出未加开发环境判断，生产构建泄露PII与token | `enterprise-h5/src/views/login/MockLogin.vue:84-125` | 用 `import.meta.env.DEV` 判断包裹或移除 |
| P2-13 | 测试基础设施 | `tests/`目录为空，pytest未安装，无可重复运行的自动化测试 | `tests/`、`requirements.txt` | 补充最小单元测试覆盖状态机分支+集成测试跑通三条主流程 |
| P2-14 | 部署 | 无Dockerfile/compose/systemd/nginx文件；应用无DB连接重试逻辑 | 全仓库 | 见第17/18节任务清单 |
| P2-15 | 部署 | enterprise-h5缺少`.env.production` | `enterprise-h5/` | 补充该文件，与admin-web对齐 |
| P2-16 | 部署 | 无日志落盘/可配置日志目录方案 | 全局 | 增加基于环境变量的日志目录配置或落地到stdout供容器采集 |

### P3（低优先级）

| 编号 | 问题 | 涉及文件 |
|---|---|---|
| P3-1 | `passlib[bcrypt]`为死依赖，全仓库零引用 | `requirements.txt` |
| P3-2 | `AppealStatus.DEPT_REPLIED`常量定义但从未被代码设置（死枚举值） | `app/constants/appeal.py`、`app/services/appeal_service.py::dept_reply` |
| P3-3 | `SysOperationLog.ip_address`/`user_agent`字段定义但从未写入 | `app/models/system.py`、各处 `add_operation_log` 调用 |
| P3-4 | admin-web全量引入Element Plus，构建产物1.19MB超过建议阈值，无代码分割 | `admin-web/src/main.ts` |
| P3-5 | 三大模块的列表筛选/分页样板代码在admin-web中重复实现，未抽取公共组件/composable | `admin-web/.../AppealList.vue`、`BookingList.vue`、`GovMeetingList.vue` |
| P3-6 | enterprise-h5存在大量camelCase/snake_case双字段兼容读取函数，掩盖历史命名不一致问题 | `enterprise-h5/src/api/meetingRoom.ts`、`govMeeting.ts` |
| P3-7 | `docs/ADMIN_WEB_DEBUG.md`关于CORS配置的描述与当前代码不符（滞后） | `docs/ADMIN_WEB_DEBUG.md` |
| P3-8 | `docs/API_TESTING.md`/`DEPLOY_KYLIN_V10.md`迁移版本表和路由清单未收录005~009号迁移及服务中心管理接口组 | `docs/API_TESTING.md`、`docs/DEPLOY_KYLIN_V10.md` |
| P3-9 | `HelloWorld.vue`脚手架默认组件全项目无引用，属死代码 | `enterprise-h5/src/components/HelloWorld.vue` |
| P3-10 | `govMeeting.ts`中"后端暂无此接口"注释与实际代码不符（接口已实现） | `enterprise-h5/src/api/govMeeting.ts:231` |
| P3-11 | 附件表存在孤儿数据风险：`TEMP`类型的未绑定上传记录和物理文件无清理机制 | `app/api/common/router.py::upload_attachment` |

---

## 15. 尚未完成的功能清单

1. **企业诉求"办结"闭环动作**（Service方法+API路由完全缺失，P1-3）。
2. **企业端H5诉求补充材料功能**（无UI入口，P1-4）。
3. **企业端H5"常见问题"页面**（完全未实现）。
4. **消息通知体系**（表存在，零实现，P1-9）。
5. **用户/角色/权限管理界面**（前后端均无，仅有数据字段无管理能力）。
6. **会议室日历可视化（日/周/月视图）**（管理端仅有表单，无时间轴视图）。
7. **统计分析图表可视化**（当前仅数字卡片，无趋势/占比图表）。
8. **会议室预约台账真实文件导出**（当前为JSON回显，非Excel/CSV）。
9. **诉求附件上传/下载UI**（管理端两处显式TODO禁用）。
10. **独立附件管理页面**（当前附件只能嵌套在各业务详情页查看）。
11. **自动化测试套件**（`tests/`目录事实为空）。
12. **Docker化部署工件**（Dockerfile/compose/启动脚本/日志方案）。
13. **真实身份认证对接**（省级统一身份认证 / 政务服务平台统一用户体系，当前均为mock-login，需求文档允许一期占位，但属于"未完成"而非"已完成"）。

---

## 16. 技术债务清单

1. mock-login无环境网关（P0-1）——需要在真实SSO接入前作为最低限度加固。
2. 系统性IDOR模式（P1-1）——建议抽取统一的权限校验工具函数，一次性修复三个模块，避免后续新增模块重蹈覆辙。
3. 角色权限从未被强制执行（P1-2）——是当前系统最大的架构缺口，建议作为独立的"权限中间件"项目立项，而不是逐接口打补丁。
4. 序列号生成竞态（P1-8）。
5. 附件孤儿数据无清理机制（P3-11）。
6. `DEPT_REPLIED`死枚举、`ip_address`/`user_agent`死字段（P3-2、P3-3）——反映"设计比实现快一步"的模式，建议在补齐权限体系时一并清理或补齐实现。
7. 前端camelCase/snake_case兼容层（P3-6）、admin-web重复样板代码（P3-5）——不影响功能，但会拖慢后续维护速度。
8. 文档滞后（P3-7、P3-8）——建议将文档更新纳入合并请求（PR）检查清单，避免继续累积漂移。
9. 无自动化测试（P2-13）——是长期维护成本最高的一项技术债，建议尽早补齐，否则后续每次修复本报告中的问题都存在引入新回归的风险却无法被自动发现。

---

## 17. 推荐的后续开发顺序

综合"影响面 × 修复成本"排序，建议按以下顺序推进：

**第一阶段：安全阻断项收口（预计1个批次内完成）**
1. P0-1（mock-login环境网关）
2. P0-2（附件下载鉴权）
3. P1-5（密钥管理加固）
4. P1-6（上传文件类型白名单）

**第二阶段：权限体系补齐（这是决定系统能否真正投入多角色使用的关键）**
5. P1-1（系统性IDOR修复，三模块统一抽取权限校验工具）
6. P1-2（角色权限强制执行，前后端同步）
7. P1-7（dataScope下拉选项与后端对齐）

**第三阶段：业务闭环补全**
8. P1-3（诉求办结动作）
9. P1-4（企业端H5补充材料功能）
10. P1-9（消息通知最小实现）
11. 企业端H5常见问题页面 + 须知/规则登录门禁修正（P2-11）

**第四阶段：体验与运营能力补齐**
12. P2-6（台账真实导出）
13. P2-7（诉求附件上传/下载补齐）
14. P2-8/P2-9（会议室日历、统计图表）
15. 用户/角色/权限管理界面

**第五阶段：质量与部署基建**
16. P2-13（自动化测试套件从0到1）
17. P1-8（序列号并发修复）、P2-1（预约审批竞态修复）
18. P2-14/P2-15/P2-16（Dockerfile、compose、启动顺序、日志方案）
19. 麒麟V10实机联调验证

**理由**：安全阻断项必须最先处理，因为它们不需要新功能开发即可被利用；权限体系是第二优先，因为后续所有业务功能的补全都应该"自带权限校验"而不是先做完功能再回头补权限；业务闭环补全解决的是"已经投入使用会立刻被用户发现"的缺口；体验/运营能力和质量/部署基建虽然重要，但短期不影响已上线部分的正确性和安全性，可以放在功能闭环之后统筹处理。

---

## 18. 下一阶段 Claude Code 开发任务

> 以下任务按第17节顺序编排，可逐项交给 Claude Code 执行。每项任务给出目标、涉及模块/文件、需要完成的工作和验收标准。**本次审计未修改任何业务代码，以下均为待执行任务。**

---

**TASK-001**
目标：为企业端/管理端 mock-login 增加生产环境网关，防止一期占位登录方式被误用于生产环境。
涉及模块：登录认证
涉及文件：`app/api/auth/router.py`、`app/core/config.py`
需要完成：
- 在 `Settings` 增加读取当前环境的能力（已有 `app_env`）；
- 在两个 mock-login 路由函数入口处，当 `settings.app_env == "production"` 时抛出 403/404；
- 在 `README.md`/部署文档中明确标注该网关及其绕过条件（如未来真实SSO接入后应移除mock-login路由本身而非仅加网关）。
验收标准：在 `APP_ENV=production` 下调用两个 mock-login 接口返回非200且不签发Token；在 `APP_ENV=development` 下行为不变。
优先级：P0

---

**TASK-002**
目标：修复附件下载接口零鉴权问题。
涉及模块：附件体系
涉及文件：`app/api/common/router.py`
需要完成：
- 为 `download_attachment` 增加鉴权依赖（复用 `_get_uploader` 或新增一个同时接受企业端/管理端Token的依赖）；
- 增加业务归属校验：企业端Token只能下载 `business_type`对应记录且`business_id`归属本企业的附件；管理端Token需满足与该附件所属业务记录一致的数据权限（复用TASK-005产出的权限校验工具）。
验收标准：未携带Token请求下载接口返回401；企业A的Token请求企业B的附件返回403或404；管理端跨区域下载被正确拦截或放行（视TASK-005完成情况）。
优先级：P0

---

**TASK-003**
目标：加固JWT密钥管理，防止生产环境使用默认/占位密钥。
涉及模块：核心配置
涉及文件：`app/core/config.py`、`.env.example`、部署文档
需要完成：
- 移除或标记 `app_secret_key` 的硬编码默认值 `"dev-secret-key"` 为仅限开发使用；
- 增加启动期校验：当 `app_env == "production"` 且 `app_secret_key` 为空、等于默认值、或等于`.env.example`中的占位文本时，直接抛出异常阻止启动；
- 更新部署文档，说明生产环境密钥的生成与注入方式（环境变量/K8s Secret）。
验收标准：使用占位密钥+`APP_ENV=production`启动应用会失败并给出明确错误信息；使用自定义密钥可正常启动。
优先级：P1

---

**TASK-004**
目标：为文件上传增加扩展名/内容类型白名单校验。
涉及模块：附件体系
涉及文件：`app/api/common/router.py`
需要完成：
- 定义允许的扩展名集合（pdf/doc/docx/jpg/jpeg/png/xls/xlsx等，与业务附件场景对齐）；
- 在 `upload_attachment` 中校验 `ext` 是否在白名单内，不在则抛 `FileUploadException`；
- 将文件大小校验前移到读取内容之前（基于 `Content-Length` 或流式读取+提前中止），修复P2-2。
验收标准：上传白名单外扩展名文件返回业务错误码；超大文件在未完全读入内存前即被拒绝。
优先级：P1（含P2-2）

---

**TASK-005**
目标：修复三大模块管理端"详情/操作"接口的系统性数据权限（IDOR）缺口。
涉及模块：企业诉求、共享会议室、政企约见（管理端）
涉及文件：`app/repositories/appeal_repo.py`、`app/repositories/meeting_room_repo.py`、`app/repositories/gov_meeting_repo.py`、对应三个 `*_service.py`、对应三个 `api/admin/*.py`
需要完成：
- 新增一个共用的权限校验工具函数（建议放在 `app/core/permission.py`），输入记录的 `region_code`/`responsible_dept_id`（或`assigned_dept_id`）与操作者的 `data_scope`/`region_code`/`department_id`，越权则抛 `ForbiddenException`；
- 在三个模块所有"按ID取记录后执行操作"的Service方法中调用该工具函数（受理/退回/不予受理/分派/办理/反馈/审核/批准/驳回/安排/确认/办结/爽约等，见P1-1列出的具体方法名）；
- 详情查看接口同样增加校验（不仅是操作接口）。
验收标准：使用 `dataScope=REGION`、`regionCode=A`的Token访问区域B的诉求/预约/约见详情或执行任意操作，返回403；使用`dataScope=ALL`的Token行为不变。
优先级：P1

---

**TASK-006**
目标：实现基于`role_codes`的功能级权限校验（前后端同步）。
涉及模块：全局权限体系
涉及文件：`app/core/deps.py`（新增角色校验依赖）、各`api/admin/*.py`（按接口标注所需角色）、`admin-web/src/router/index.ts`、`admin-web/src/layouts/AdminLayout.vue`、`admin-web/src/stores`
需要完成：
- 后端：设计最小可行的角色-操作映射表（可先用字典/常量硬编码角色码与允许操作的对应关系，不必做完整RBAC管理界面），为管理端的写操作类接口增加角色依赖；
- 前端：登录后将 `roleCodes` 存入 Pinia store，路由meta增加所需角色声明，路由守卫和菜单渲染增加角色过滤，操作按钮增加权限指令/`v-if`。
验收标准：使用不含所需角色码的Token调用受限接口返回403；前端对应菜单/按钮不渲染。
优先级：P1

---

**TASK-007**
目标：修正admin-web登录页`dataScope`下拉选项与后端枚举值不一致的问题。
涉及模块：admin-web登录
涉及文件：`admin-web/src/views/login/Login.vue`
需要完成：
- 将下拉选项改为与后端实际识别值一致：`ALL`（全量）/`REGION`（区县）/`DEPARTMENT`（部门）/`SELF`（个人，如适用）；
- 同步核对后端对未识别`data_scope`值的默认行为，改为默认拒绝而非默认放行（防御性加固，与TASK-005一并处理）。
验收标准：下拉选项与后端行为完全对应，不存在"选择更小范围实际获得更大范围"的情况。
优先级：P1

---

**TASK-008**
目标：补齐企业诉求模块的"办结"闭环动作。
涉及模块：企业诉求-管理端
涉及文件：`app/constants/appeal.py`、`app/services/appeal_service.py`、`app/api/admin/appeals.py`、`app/schemas/appeal.py`、admin-web对应详情页
需要完成：
- 在 `ALLOWED_STATUS_FOR_ACTION` 中为 `AppealAction.COMPLETE` 增加允许的前置状态（如`EVALUATED`）；
- 新增 `AppealService.complete_appeal()` 方法（比照 `GovMeetingService.finish_apply` 实现，写状态、写审核轨迹、写操作日志）；
- 新增 `POST /api/admin/appeals/{appeal_id}/complete` 路由；
- admin-web诉求详情页增加"办结"操作按钮。
验收标准：诉求处于`EVALUATED`状态时管理端可点击"办结"，状态变为`COMPLETED`，审核轨迹和操作日志均正确记录；仪表盘统计中"已办结"数量正确反映。
优先级：P1

---

**TASK-009**
目标：实现企业端H5诉求补充材料功能。
涉及模块：企业诉求-企业端H5
涉及文件：`enterprise-h5/src/api/appeal.ts`、`enterprise-h5/src/views/appeal/AppealDetail.vue`（或新增`AppealSupplement.vue`）
需要完成：
- 在`api/appeal.ts`中增加调用`POST /api/enterprise/appeals/{id}/supplement`的函数；
- 在诉求详情页为`NEED_SUPPLEMENT`状态的诉求增加"补充材料"入口，表单包含说明文字和附件上传（复用会议室补充材料页面模式）。
验收标准：诉求处于"退回补充"状态时，企业用户可在H5端提交补充说明和附件，提交后状态变回"待受理"，管理端可见补充内容。
优先级：P1

---

**TASK-010**
目标：实现消息通知的最小可行版本（站内记录）。
涉及模块：消息记录（共用）
涉及文件：新增`app/services/message_service.py`，三大模块的`*_service.py`在关键状态转移点调用，管理端/企业端各新增"消息中心"页面
需要完成：
- 实现`MessageService.notify(business_type, business_id, receiver_type, receiver_id, receiver_name, title, content)`方法，写入`SysMessageRecord`；
- 在诉求受理/退回/不予受理/回复、会议室审核通过/驳回、约见受理/安排/完成/待评价等关键节点调用该方法（对照需求文档6.4节场景列表）；
- 管理端和企业端分别增加消息列表页面（分页查询+已读/未读标记）。
验收标准：完成一次诉求受理操作后，能在企业端消息列表看到对应通知记录；管理端能查询到系统内全部消息记录。
优先级：P1

---

**TASK-011**
目标：补齐企业端H5"常见问题"页面，修正须知/规则页面的登录门禁。
涉及模块：企业端H5
涉及文件：`enterprise-h5/src/router/index.ts`、新增`enterprise-h5/src/views/faq/FAQ.vue`
需要完成：
- 将`MeetingRoomRules`、`GovMeetingNotice`路由的`meta.requiresAuth`改为`false`；
- 新增常见问题页面及路由，内容来源可先用字典表配置（如后台无对应字典类型则先新增一个`FAQ`字典类型，前端渲染问答列表）。
验收标准：未登录状态下可直接访问须知、规则、常见问题三个页面；提交类操作仍强制登录。
优先级：P2

---

**TASK-012**
目标：实现会议室预约台账真实文件导出（Excel）。
涉及模块：共享会议室-管理端
涉及文件：`app/api/admin/meeting_bookings.py`、`app/services/meeting_room_service.py`、`admin-web/src/views/meeting-room/BookingList.vue`
需要完成：
- 后端引入`openpyxl`（或等价库），实现真实Excel文件流生成并通过`StreamingResponse`返回；
- 前端改为触发浏览器文件下载而非展示提示信息。
验收标准：点击"导出台账"后浏览器下载一个包含当前筛选条件下全部预约记录的`.xlsx`文件，字段与需求文档5.2.4第9节列出的维度一致。
优先级：P2

---

**TASK-013**
目标：补齐诉求详情页的附件上传/下载功能（去除现有TODO占位）。
涉及模块：企业诉求-管理端
涉及文件：`admin-web/src/views/appeal/AppealDetail.vue`
需要完成：
- 移除硬编码`disabled`的下载按钮限制，接入已可用的`GET /api/common/attachments/{id}/download`；
- 企服中心办理/部门反馈弹窗增加`el-upload`组件（复用`RoomList.vue`中已有的上传组件模式），提交时将返回的`attachmentIds`传给对应接口。
验收标准：诉求详情页可正常下载已上传附件；办理/反馈时可上传新附件并在提交后于详情页可见。
优先级：P2

---

**TASK-014**
目标：从0搭建自动化测试套件。
涉及模块：全局
涉及文件：`requirements.txt`（新增`pytest`/`httpx`/`pytest-asyncio`等）、`tests/`目录下新增测试文件
需要完成：
- 引入`pytest` + FastAPI `TestClient`，为三大模块的状态机核心分支（含TASK-005/008修复后的新分支）编写单元/集成测试；
- 至少覆盖：诉求提交→受理→分派→部门反馈→审核→评价→办结全流程；会议室提交→审核→完成/爽约；约见提交→审核→安排→确认→完成→纪要→评价→办结；
- 覆盖TASK-005的越权校验用例（应返回403）。
验收标准：`pytest tests/ -q`可在CI环境下无需手动启动服务器即运行通过（使用测试数据库或SQLite内存库+事务回滚）。
优先级：P2（但建议尽早启动，作为后续所有任务的回归保障）

---

**TASK-015**
目标：编写Dockerfile与docker-compose，实现容器化部署最小可行方案。
涉及模块：部署
涉及文件：新增根目录`Dockerfile`（后端）、`admin-web/Dockerfile`、`enterprise-h5/Dockerfile`（或统一Nginx镜像）、`docker-compose.yml`、`.dockerignore`
需要完成：
- 后端镜像：多阶段构建（安装依赖→拷贝代码），启动命令增加数据库连接重试逻辑（修复12节"无服务启动顺序控制"问题）；
- 前端：构建产物由Nginx镜像托管，Nginx配置反向代理`/api`到后端容器；
- compose编排：MySQL、后端、Nginx（含两个前端静态资源）三个服务，声明`uploads`和MySQL数据目录为具名Volume；
- 补充`enterprise-h5/.env.production`（修复P2-15）。
验收标准：`docker-compose up`后可通过Nginx访问两个前端，前端可正常调用后端接口，重启MySQL容器后后端能自动重连而不崩溃退出。
优先级：P2，建议在麒麟V10实机联调前完成

---

**TASK-016**
目标：修复会议室预约审批的并发竞态与流水号生成竞态。
涉及模块：共享会议室、序列号生成
涉及文件：`app/services/meeting_room_service.py::approve_booking`、`app/utils/serial_no.py`
需要完成：
- `approve_booking`中的冲突校验查询增加行锁（`with_for_update()`）或改为数据库唯一约束辅助校验；
- `generate_daily_serial`改为基于数据库自增序列或`SELECT...FOR UPDATE`的原子方案。
验收标准：并发压测两个冲突时间段的预约审批，只有一个能成功；并发压测同日大量提交，不出现编号重复导致的提交失败。
优先级：P2

---

*报告完*
