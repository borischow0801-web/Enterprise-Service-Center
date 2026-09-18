# 企业端自主注册 + 密码登录 实施说明

本次开发目标：在暂未接入省级统一身份认证的情况下，为企业端提供真实可用的注册/登录能力，同时保证未来接入省统一身份认证时**不需要修改三大业务模块**。对应 `PROJECT_AUDIT_REPORT.md` 中 P0-1（mock-login 生产风险）的企业端部分，以及尚未完成功能清单中的"真实身份认证对接"过渡方案。

---

## 1. 原认证机制

- 企业端 JWT 由 `create_enterprise_token()`（`app/core/security.py`）签发，payload 固定为：
  `{token_type: "enterprise", sub_type: "enterprise", sub, subject_type: "ENTERPRISE", enterprise_id, enterprise_name, credit_code}`。
- `get_current_enterprise`（`app/core/deps.py`）只校验 token 签名与 `token_type=="enterprise"`，之后所有业务代码统一读取 `current["enterprise_id"]`。
- 唯一的身份确认方式是 `POST /api/auth/enterprise/mock-login`：按 `creditCode` 查 `enterprise` 表，不存在则创建、存在则用请求体覆盖法人信息——**认证身份与企业业务档案完全耦合**，且零校验、无环境网关（`PROJECT_AUDIT_REPORT.md` P0-1）。
- `app/services/auth_adapter.py` 只有一个从未被调用的 `BaseAuthAdapter` 抽象骨架。
- `enterprise-h5/src/api/auth.ts::handleProvincialAuthCallback()` 是省认证回调的唯一预留点，直接抛异常，后端无对应路由。

## 2. 新认证架构

```
Enterprise (企业业务档案)
    1 : N
EnterpriseIdentity (登录身份)
    ├─ LOCAL           本地账号密码（本次实现）
    └─ PROVINCIAL_SSO  省统一身份认证（预留，未实现）
```

核心原则：**Enterprise 只承载业务数据，不知道自己有哪些登录方式；EnterpriseIdentity 只负责"确认你是谁"，确认完之后立刻把问题收敛成一个 `enterprise_id` 交给下游。** 三大业务模块（诉求/会议室/政企约见）以及 `get_current_enterprise` 全程不感知 `identity_type` 的存在，因此本次改动**没有修改 `app/core/deps.py`、`app/api/enterprise/appeals.py`、`app/services/appeal_service.py` 等任何业务代码**。

## 3. 数据库变化

新增迁移 `migrations/versions/010_enterprise_identity.py`（`down_revision=009_booking_enterprise_type`）：

- 新建表 `enterprise_identity`：`enterprise_id`（FK→`enterprise.id`）、`identity_type`、`identifier`（LOCAL 时为信用代码）、`credential_hash`（仅 LOCAL，bcrypt hash）、`contact_name`/`contact_mobile`、`status`、`last_login_time` + `TimestampMixin`；唯一约束 `uq_enterprise_identity_type_identifier (identity_type, identifier)`。
- `enterprise.legal_person_name` / `legal_person_id_no` / `legal_person_mobile` 由 `NOT NULL` 改为可空：本地注册阶段采集的是"联系人"而非经核实的"法人"，不应该把联系人信息硬塞进法人字段冒充权威数据；这三个字段将来由省统一身份认证或管理端核实登记后再补齐。
- **已在真实 MySQL 开发库上执行 `alembic upgrade head` 验证通过**，升级前 37 条企业数据、升级后仍为 37 条（后续本文档中的联调测试又产生了几条测试企业，属预期），无数据丢失，`alembic current` 显示 `010_enterprise_identity (head)`。

副带修复（详见第 12 节）：`app/models/enterprise.py` 中 `region_code`/`auth_account_id` 字段原先同时用了 `index=True` 和 `__table_args__` 里同名的显式 `Index()`，属于纯元数据重复声明，仅在使用 `Base.metadata.create_all()`（本次新增的 SQLite 测试基础设施需要）时才会报错；已去重，**不涉及、不产生任何新的 MySQL DDL**，线上索引结构不变。

## 4. 注册流程

`POST /api/auth/enterprise/register`（`EnterpriseAuthService.register_local`，`app/services/enterprise_auth_service.py`）：

1. Pydantic 校验（`EnterpriseRegisterRequest`）：企业名称非空、信用代码 18 位数字/大写字母、手机号 `1[3-9]\d{9}`、密码 8-64 位且同时含字母数字、两次密码一致。
2. 按 `creditCode` 查 `enterprise` 表：
   - **不存在** → 新建 `Enterprise`（`legal_person_*` 留空，`auth_source="LOCAL"`）+ 新建 `EnterpriseIdentity(LOCAL)`。
   - **存在但无 LOCAL 身份** → 不新建企业，直接为已有 `enterprise_id` 绑定新的 `EnterpriseIdentity(LOCAL)`；**不覆盖**已有企业的 `enterprise_name`/`auth_source` 等字段（避免抹掉其他来源已经确认过的数据）。
   - **已存在 LOCAL 身份** → 抛 `AlreadyRegisteredException`（code=40904，"该企业已注册，请直接登录"）。
3. 密码通过 `hash_password()`（bcrypt，12 rounds）后存入 `credential_hash`，全程不落明文、不写日志、不进 JWT、不在任何响应体中返回。
4. 整个流程包在 `try/except IntegrityError` 里：并发重复提交时，数据库唯一约束（`enterprise.credit_code` 或 `uq_enterprise_identity_type_identifier`）兜底拦截，捕获后统一转换为同样的"该企业已注册"错误，而不是让请求方看到 500。
5. 注册成功后**直接签发企业 JWT 并返回**（与现有 mock-login 完全相同的 `{accessToken, tokenType, expiresIn}` 结构），采用"注册即登录"而非"注册后跳回登录页"——原因见第 15 节。

## 5. 登录流程

`POST /api/auth/enterprise/login`（`EnterpriseAuthService.login_local`）：

1. 按 `(identity_type=LOCAL, identifier=creditCode)` 查 `EnterpriseIdentity`。
2. 找不到 / 密码校验失败（`verify_password`，bcrypt）/ 身份状态非 `ACTIVE`，**统一返回同一个错误**：code=40102，"账号或密码错误"，不区分"账号不存在"与"密码错误"，避免信用代码被枚举。
3. 校验通过后取出对应 `Enterprise`，更新 `EnterpriseIdentity.last_login_time` 和 `Enterprise.last_login_time`，用与 mock-login 完全相同的 payload 结构签发 JWT。
4. 前端保存 token 后，后续请求走**未经任何修改的** `CurrentEnterprise` 依赖和 `enterprise_id` 识别链路。

## 6. Enterprise 与 EnterpriseIdentity 关系

- 1 个 `Enterprise` 可以对应 0~N 个 `EnterpriseIdentity`。
- 同一企业未来可以同时拥有 `LOCAL` 和 `PROVINCIAL_SSO` 两条身份记录，互不覆盖、互不依赖对方存在。
- `EnterpriseIdentity.status` 预留 `ACTIVE`/`DISABLED`，为后续管理端"禁用某个登录方式但不影响企业档案"留出空间（本次未做对应管理界面，仅数据模型就绪）。

## 7. LOCAL 认证机制

- 唯一识别键：统一社会信用代码（`identifier` 列，`identity_type='LOCAL'`）。
- 密码存储：`bcrypt`（见第 11 节关于 passlib 兼容性问题的说明），12 rounds，`app/core/password.py`。
- 格式校验：`app/core/validators.py`（信用代码、手机号），密码强度校验在 `app/core/password.py::assert_password_strength`，均以 Pydantic `field_validator` 接入 `EnterpriseRegisterRequest`，复用项目现有的全局校验异常处理链路（`app/core/exceptions.py::validation_exception_handler`），未新增任何异常处理管道。

## 8. PROVINCIAL_SSO 后续接入点

真正接入省统一身份认证时，预计只需要：

1. 新增 `POST /api/auth/enterprise/sso-callback`（或类似路由），内部调用 `app/services/auth_adapter.py` 中实现一个真正的 `ProvincialSsoAdapter(BaseAuthAdapter)`（当前 `MockAuthAdapter` 保持不动）。
2. 拿到省认证返回的可信身份后，按信用代码查/建 `Enterprise`（复用 `EnterpriseRepository`），再调用 `EnterpriseIdentityRepository` 查/建一条 `identity_type=PROVINCIAL_SSO` 的记录（`identifier` 用省认证平台返回的账号唯一标识，而不是信用代码本身，避免和 LOCAL 的 `identifier` 唯一约束产生语义混淆）。
3. 用**与本次完全相同**的 `_issue_token()` 方式签发 JWT。
4. **不需要改动**：`app/core/deps.py`、三大业务模块、`app/api/enterprise/router.py` 的 `/me` 接口。

`EnterpriseIdentityType.PROVINCIAL_SSO` 常量已在 `app/models/enterprise.py` 中预留，`enterprise_identity` 表结构已支持任意数量的额外身份记录，无需再次迁移即可直接使用。

## 9. API 清单

| 方法 | 路径 | 说明 | 环境限制 |
|---|---|---|---|
| POST | `/api/auth/enterprise/register` | 企业自主注册（LOCAL），成功后自动登录 | 无（任何环境可用） |
| POST | `/api/auth/enterprise/login` | 企业密码登录（LOCAL） | 无 |
| POST | `/api/auth/enterprise/mock-login` | 原有开发调试登录 | **仅非 production**，production 下返回 `{code:40401, message:"接口不存在"}` |
| GET | `/api/enterprise/me` | 获取当前企业信息（未改动） | 无 |

`admin-web`/管理端 mock-login 未在本次任务范围内，仍保持原状（见第 16 节）。

## 10. 前端页面变化

| 文件 | 变化 |
|---|---|
| `enterprise-h5/src/views/login/Login.vue` | 新增，正式登录页：信用代码+密码、"还没有账号？立即注册"、禁用态的"省统一身份认证登录"入口，DEV 环境下额外显示"开发调试登录"入口 |
| `enterprise-h5/src/views/login/Register.vue` | 新增，注册页：企业名称/信用代码/联系人/手机号/密码/确认密码 + 服务条款勾选 |
| `enterprise-h5/src/views/login/DevMockLogin.vue` | 新增（原 `MockLogin.vue` 内容迁移），路由 `/dev-login` 仅在 `import.meta.env.DEV` 为真时注册，生产构建时被 Vite 静态裁剪（已通过构建产物验证：`dist/assets` 中不存在该 chunk） |
| `enterprise-h5/src/views/login/MockLogin.vue` | **删除**，功能拆分进 `Login.vue`（正式）与 `DevMockLogin.vue`（开发调试） |
| `enterprise-h5/src/api/auth.ts` | 新增 `registerEnterprise()`、`loginEnterprise()` 及对应类型；`enterpriseMockLogin` 保留并补充"仅限非生产环境"注释 |
| `enterprise-h5/src/router/index.ts` | `/login` 指向新页面；新增 `/register`；条件注册 `/dev-login`；登录守卫对 `/login`、`/register`、`/dev-login` 三者统一处理"已登录则跳转" |

## 11. Mock Login 环境隔离

- 后端：`enterprise_mock_login()`（`app/api/auth/router.py`）入口处判断 `settings.app_env == "production"`，是则直接 `raise NotFoundException("接口不存在")`（返回 `{code:40401}`），**不依赖运维记得关闭**，已通过启动真实 `APP_ENV=production` 的 uvicorn 进程实测验证。
- 前端：`/dev-login` 路由仅在 `import.meta.env.DEV` 为真时被加入路由表，生产构建（`npm run build`）产物中确认没有生成该页面对应的 chunk。
- 管理端 mock-login **未做**同样处理——不在本次任务范围内（见第 16 节"是否存在需要人工决策的问题"）。

## 12. 安全措施

对照任务书第十一节逐项说明：

1. **密码 Hash**：bcrypt，12 rounds，`app/core/password.py`。
2. **密码强度**：≥8 位、≤64 位、必须同时含字母和数字；额外做了 UTF-8 字节长度校验（≤72 字节，bcrypt 硬限制）防止多字节字符密码在服务端抛出未处理异常。
3. **重复注册**：应用层查重 + 数据库唯一约束兜底（`IntegrityError` → 统一转换为"该企业已注册"）。
4. **SQL 注入**：新增代码全部走 SQLAlchemy ORM，没有任何字符串拼接 SQL。
5. **暴力登录**：本次**未**新增限流（与现有系统一致，全局本来就没有限流机制，超出本次范围，已记录为遗留风险，见第 16 节）。
6. **登录错误信息枚举**：账号不存在与密码错误返回完全相同的 code/message，已有自动化测试覆盖（`test_login_nonexistent_account_fails_with_identical_message`）。
7. **JWT**：复用现有 `create_enterprise_token`，未改变签名算法、密钥来源或 payload 结构。
8. **Token 有效期**：沿用 `settings.jwt_enterprise_expire_minutes`（720 分钟），未改动。
9. **日志中是否泄露密码**：`hash_password`/`verify_password`/service 层均未对密码做任何 `print`/日志输出；FastAPI 默认访问日志只记录路径和状态码，不记录请求体。
10. **浏览器 console 泄露**：`DevMockLogin.vue`（原 `MockLogin.vue`）已删除全部 `console.log`/`console.error` 对表单内容、企业信息、token 的打印；`Login.vue`/`Register.vue` 全新编写，同样不打印任何敏感信息（仅在全局 `request.ts` 中已有的 `import.meta.env.DEV` 门控下打印请求/响应，且该文件本次未改动）。
11. **注册接口重复提交**：见第 3 点，`IntegrityError` 兜底；未额外加防抖/幂等 token（评估后认为数据库唯一约束已经是充分且更可靠的兜底，属于合理的最小实现）。
12. **数据库唯一约束**：`enterprise.credit_code`（已有）+ 新增 `uq_enterprise_identity_type_identifier`。
13. **mock-login 生产关闭**：见第 11 节，已实测验证。
14. **API 参数校验**：全部通过 Pydantic `field_validator`/`model_validator` 完成，复用现有全局异常处理。

## 13. 测试结果

新增 `tests/conftest.py`（SQLite 内存库 + `get_db` 依赖覆盖，不要求真实 MySQL 可用；额外提供 `as_production_env` fixture 用于环境隔离测试）与 `tests/test_enterprise_auth.py`，**14 个用例全部通过**：

```
14 passed, 68 warnings in 4.91s
```

覆盖任务书第十三节全部 15 项中除"迁移可 upgrade"和"enterprise-h5 build"外的 13 项（这两项按性质更适合作为独立运行验证，而非 pytest 用例，已在下方与第 3 节分别给出**真实**验证结果，而非用测试掩盖）：

| # | 用例 | 结果 |
|---|---|---|
| 1-4 | 新企业注册成功 / Enterprise 正确创建 / LOCAL Identity 正确创建 / 密码非明文 | `test_register_new_enterprise_success` ✅ |
| 5 | 已有 Enterprise 绑定 LOCAL Identity（不重复建企业、不覆盖原字段） | `test_register_binds_existing_enterprise_without_duplicating` ✅ |
| 6 | 已注册企业重复注册失败 | `test_register_duplicate_rejected` ✅ |
| 7 | 正确密码登录成功 | `test_login_success` ✅ |
| 8 | 错误密码登录失败 | `test_login_wrong_password_fails` ✅ |
| 9 | 不存在账号登录失败（且与密码错误消息一致） | `test_login_nonexistent_account_fails_with_identical_message` ✅ |
| 10-11 | JWT 通过 `get_current_enterprise`；能调用现有业务接口（`/api/enterprise/me`、`/api/enterprise/appeals`） | `test_login_token_can_access_existing_business_endpoint` ✅ |
| 12 | production 环境 mock-login 不可用（且 register/login 不受影响） | `test_mock_login_blocked_in_production` ✅ |
| 13 | development 环境 mock-login 正常 | `test_mock_login_allowed_in_development` ✅ |
| 附加 | 弱密码/信用代码格式/手机号格式/两次密码不一致 均被拒绝 | 4 个用例 ✅ |
| 附加 | migration revision 链路正确指向 `009_booking_enterprise_type` | `test_migration_chain_links_to_head` ✅ |

**14 Alembic migration 可正常 upgrade**：已在真实 MySQL 开发库执行 `alembic upgrade head`，`alembic current` 确认落在 `010_enterprise_identity (head)`，见第 3 节。

**15 enterprise-h5 可以正常 build**：`npm run build`（含 `vue-tsc -b` 类型检查）成功，无错误无警告；产物中确认不包含 `DevMockLogin` chunk。

此外还额外做了一轮**真实服务端联调**（非 pytest，直接起 uvicorn + curl，针对真实 MySQL 开发库）：注册新企业 → 查库确认 `Enterprise`/`EnterpriseIdentity` 数据正确 → 用签发的 token 调用 `/api/enterprise/me` 和 `/api/enterprise/appeals` 成功 → 重复注册返回 40904 → 正确/错误密码登录行为符合预期 → 已有 mock-login 产生的企业注册后未被重复创建、`auth_source` 保持原值不变 → `APP_ENV=production` 下 mock-login 返回 40401、`login` 接口正常。

## 14. Alembic Migration

- 文件：`migrations/versions/010_enterprise_identity.py`
- `revision = '010_enterprise_identity'`，`down_revision = '009_booking_enterprise_type'`
- 未修改任何历史迁移文件，未手工改动数据库结构。
- `downgrade()` 已实现；注意其中把 `legal_person_*` 三字段改回 `NOT NULL` 的部分，如果届时已存在 LOCAL 注册产生的 NULL 数据，会因约束校验失败而报错——这是刻意保留的安全阀，迁移脚本不会做隐式数据清理/回填。

## 15. 后续省统一身份认证接入指南

1. 在 `app/services/auth_adapter.py` 新增 `ProvincialSsoAdapter(BaseAuthAdapter)`，实现 `authenticate()`/`get_user_info()` 对接真实省平台接口。
2. 新增 schema（如 `ProvincialSsoCallbackRequest`）和路由（如 `POST /api/auth/enterprise/sso-callback`），内部：查/建 `Enterprise` → 查/建 `EnterpriseIdentity(identity_type=PROVINCIAL_SSO)` → 复用 `_issue_token()` 逻辑签发 JWT。建议把 `_issue_token()` 从 `enterprise_auth_service.py` 提炼成一个更通用的位置（如 `app/services/enterprise_token_issuer.py`），供 LOCAL 和 PROVINCIAL_SSO 两条路径共用，避免以后出现两份 payload 拼装逻辑。
3. 前端 `enterprise-h5/src/api/auth.ts::handleProvincialAuthCallback()` 替换为真正调用后端 callback 接口；`Login.vue` 中"省统一身份认证登录"按钮去掉 `disabled`，接入真实跳转/回调流程；路由守卫中 `redirect` 相关逻辑（`utils/redirect.ts`）已经是为这个场景设计的，无需改动。
4. 是否允许同一 `Enterprise` 同时保留 LOCAL 和 PROVINCIAL_SSO 两条身份、绑定后 LOCAL 是否要禁用等，属于业务规则决策，当前数据模型（1:N + `status` 字段）已经具备支持任意选择的能力，不会成为技术障碍。

---

## 16. 遗留事项 / 需人工决策

- **管理端 mock-login 未做生产环境网关**：`PROJECT_AUDIT_REPORT.md` P0-1 同时覆盖企业端和管理端，本次任务书明确限定"企业端"，故只处理了企业端。管理端 `admin_mock_login` 目前仍然在任何环境下都可用，建议尽快作为独立任务处理。
- **未加登录限流/防暴力破解**：本次登录接口和原有其它接口一样没有限流，任务书未将其列为强制项，但由于新增了真正的密码校验（存在被暴力破解的现实意义，不同于此前"零验证"的 mock-login），建议后续尽快补充。
- **`Enterprise.legal_person_*` 字段长期为空的运营影响**：本地注册产生的企业在法人信息补齐之前，`legalPersonName`/`legalPersonIdNo`/`legalPersonMobile` 会一直是 `null`；管理端诉求/会议室/政企约见列表页如果有展示或依赖这些字段做业务判断的地方，需要人工确认是否需要做兼容处理（本次审查未发现三大业务模块读取这些字段做逻辑判断，仅用于展示，风险较低，但建议由业务方最终确认）。
- **旧的 mock-login 产生的历史企业数据**（`auth_source="MOCK"`）与本次新注册企业（`auth_source="LOCAL"`）并存，两者数据完整性和字段完备程度不同，若后续要做企业名录相关的统计报表，建议按 `auth_source` 区分口径。
