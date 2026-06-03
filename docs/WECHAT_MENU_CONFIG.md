# 微信公众号自定义菜单配置说明

本文档说明「企业服务中心」企业端 H5 与微信公众号底部菜单「企业服务」的对接方式。

---

## 1. 菜单结构

| 层级 | 名称 |
|------|------|
| 主菜单 | 企业服务 |
| 子菜单 1 | 企业诉求 |
| 子菜单 2 | 共享会议室 |
| 子菜单 3 | 政企约见 |

---

## 2. 菜单类型

微信公众平台配置时使用：

- **类型**：`view`（跳转网页）
- **说明**：用户点击后直接在微信内置浏览器打开 H5 地址，不经过公众号首页。

---

## 3. 跳转地址（与路由对应）

| 子菜单 | 前端路由 | 页面说明 |
|--------|----------|----------|
| 企业诉求 | `/appeals` | 诉求列表 + 底部「提交诉求」 |
| 共享会议室 | `/meeting-rooms` | 会议室列表 |
| 政企约见 | `/gov-meetings/notice` | 约见须知 +「我已知晓，发起约见」 |

备用首页（非菜单必填）：`/home` — 企业服务中心调试/汇总入口。

---

## 4. 开发环境地址示例

> **注意**：本项目 `enterprise-h5` 的 Vite 默认端口为 **5174**（`vite.config.ts`）。若 5174 被占用会自动递增（如 5175）。请以终端 `npm run dev` 输出为准。

| 子菜单 | 开发环境 URL（默认 5174） |
|--------|---------------------------|
| 企业诉求 | `http://127.0.0.1:5174/appeals` |
| 共享会议室 | `http://127.0.0.1:5174/meeting-rooms` |
| 政企约见 | `http://127.0.0.1:5174/gov-meetings/notice` |

若你本地将端口改为 5173，则对应：

- `http://127.0.0.1:5173/appeals`
- `http://127.0.0.1:5173/meeting-rooms`
- `http://127.0.0.1:5173/gov-meetings/notice`

外网/手机调试请使用局域网 IP，例如：`http://10.x.x.x:5174/appeals`。

---

## 5. 正式环境地址示例

将 `正式域名` 替换为已备案、已配置 HTTPS 的企业端域名：

| 子菜单 | 正式环境 URL |
|--------|--------------|
| 企业诉求 | `https://正式域名/appeals` |
| 共享会议室 | `https://正式域名/meeting-rooms` |
| 政企约见 | `https://正式域名/gov-meetings/notice` |

---

## 6. 登录与 redirect 逻辑

### 当前（开发环境）

- 使用 **Mock 登录页** `/login`（模拟企业信息，非真实省认证）。
- 用户从菜单直链进入业务页时：
  1. 若未登录（无 `enterprise_token`），跳转  
     `/login?redirect=<原始路径>`  
     例如：`/login?redirect=%2Fappeals`
  2. Mock 登录成功后，使用 `redirect` **回到菜单目标页**（`decodeURIComponent`）。
  3. 无 `redirect` 时进入 `/home`。

### 正式环境（规划）

- 对接 **省级统一身份认证**，不使用账号密码。
- 流程与开发环境 redirect 约定一致：
  1. 菜单访问 `/appeals` 等 → 记录 `redirect`
  2. 跳转省认证
  3. 回调 `/auth/callback`（或约定页）→ 后端换 `enterprise_token`
  4. 保存 token 后 **跳回 redirect**，不强制 `/home`

实现参考代码：

- `enterprise-h5/src/router/index.ts` — 路由守卫
- `enterprise-h5/src/utils/redirect.ts` — `resolveRedirectPath` / `buildLoginRedirect`
- `enterprise-h5/src/api/auth.ts` — 省认证回调说明

---

## 7. 微信公众平台配置步骤（简要）

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 进入 **自定义菜单** → 编辑「企业服务」
3. 添加三个子菜单，类型选 **跳转网页**
4. 填入上表正式环境 HTTPS 地址（须在微信后台配置 JS 安全域名、业务域名）
5. 保存并发布菜单

---

## 8. 验证清单

| 场景 | 预期 |
|------|------|
| 未登录访问 `/appeals` | → `/login?redirect=/appeals` → 登录后回到 `/appeals` |
| 未登录访问 `/meeting-rooms` | → `/login?redirect=/meeting-rooms` → 登录后回到列表 |
| 未登录访问 `/gov-meetings/notice` | → `/login?redirect=/gov-meetings/notice` → 登录后回到须知页 |
| 已登录直链上述三地址 | 直接展示对应业务页 |
| 已登录访问 `/login` | 进入 `/home`（无 redirect 时） |

---

## 9. 相关页面标题（H5 内 NavBar）

| 路径 | 标题 |
|------|------|
| `/home` | 企业服务中心（页内头部） |
| `/appeals` | 企业诉求 |
| `/appeals/create` | 提交诉求 |
| `/meeting-rooms` | 共享会议室 |
| `/meeting-bookings` | 我的预约 |
| `/gov-meetings/notice` | 政企约见 |
| `/gov-meetings/create` | 发起约见 |
| `/gov-meetings` | 我的约见 |
| `/mine` | 我的 |

---

## 10. 本轮不做

- 真实微信公众号 OAuth 网页授权
- 省级统一身份认证接口对接
- 管理端改动
