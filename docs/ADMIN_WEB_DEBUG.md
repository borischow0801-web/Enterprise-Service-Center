# 管理端联调排查手册

## 一、启动命令

### 后端

```bash
cd /app/Enterprise-Service-Center
source .venv/bin/activate  # 或直接用 venv 内的 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

验证：`curl http://127.0.0.1:8000/api/health`

### 前端

```bash
cd /app/Enterprise-Service-Center/admin-web
npm run dev
```

访问：`http://<服务器IP>:5173`

---

## 二、环境变量（.env.development）

```
VITE_API_BASE_URL=       ← 必须为空！让 Axios 发相对路径，由 Vite proxy 转发
VITE_APP_TITLE=企业服务中心管理端
```

**为什么 `VITE_API_BASE_URL` 必须留空：**

Vite 会把 env 变量打包进浏览器 JS。如果填 `http://127.0.0.1:8000`，外部 PC 打开页面时浏览器会请求**客户端自己**的 `127.0.0.1:8000`，找不到后端。

留空后，Axios 发 `/api/...`（相对路径），浏览器发给当前页面来源（`http://<服务器IP>:5173`），Vite dev server 在**服务端**代理到 `http://127.0.0.1:8000`，正确到达后端。

---

## 三、管理端 mock 登录

### 接口

```
POST /api/auth/admin/mock-login
Content-Type: application/json
```

### 默认请求体（字段必须 camelCase）

```json
{
  "platformUserId": "u001",
  "username": "admin",
  "realName": "管理员",
  "departmentId": "dept001",
  "departmentName": "企业服务中心",
  "regionCode": "371000",
  "regionName": "威海市",
  "roleCodes": ["CENTER_ADMIN"],
  "dataScope": "REGION"
}
```

### 返回格式

```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJ...",
    "tokenType": "Bearer",
    "expiresIn": 28800
  },
  "traceId": "..."
}
```

---

## 四、登录失败排查步骤

### Step 1：确认后端在线
```bash
curl http://127.0.0.1:8000/api/health
# 期望: {"code":0,"data":{"status":"ok"}}
```

### Step 2：直接测试 mock-login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/admin/mock-login \
  -H 'Content-Type: application/json' \
  -d '{"platformUserId":"u001","username":"admin","realName":"管理员","departmentId":"dept001","departmentName":"企业服务中心","regionCode":"371000","regionName":"威海市","roleCodes":["CENTER_ADMIN"],"dataScope":"REGION"}'
```

### Step 3：测试 Vite proxy 转发
```bash
# 用服务器 IP 访问（模拟外部 PC）
curl http://<服务器IP>:5173/api/health
```

### Step 4：浏览器控制台
- 开 Network 面板，点击登录，查看 `/api/auth/admin/mock-login` 请求
- 检查 Request URL：应为 `http://<服务器IP>:5173/api/...`（不能是 `http://127.0.0.1:8000`）
- 检查 Response：`code` 应为 `0`

### Step 5：前端控制台日志
开发模式下 `request.ts` 会打印：
```
[API] POST /api/auth/admin/mock-login {...}
[API] ← /api/auth/admin/mock-login {code: 0, ...}
```

---

## 五、CORS 排查

后端已配置 `CORSMiddleware allow_origins=["*"]`，开发阶段不应有 CORS 问题。

若仍报 CORS 错误：
1. 确认后端正在运行（步骤 Step 1）
2. 确认请求 URL 是相对路径走 Vite proxy，而非直接跨域请求后端
3. 浏览器 Network：看 OPTIONS 预检，返回头应有 `Access-Control-Allow-Origin: *`

---

## 六、Token 排查

| 问题 | 排查 |
|------|------|
| 登录后立即跳回 /login | localStorage 中 `esc_admin_token` 是否存在 |
| 接口 401 | Token 是否正确带入 `Authorization: Bearer <token>` |
| 接口 40301 | 用了企业端 token 调管理端接口（或反之） |
| Token 过期 | 默认 8 小时，重新登录即可 |

查看 localStorage（浏览器控制台）：
```js
localStorage.getItem('esc_admin_token')
localStorage.getItem('esc_admin_user')
```

---

## 七、常见错误码

| code | 含义 | 处理 |
|------|------|------|
| 0 | 成功 | — |
| 40001 | 参数错误（422） | 检查请求字段 |
| 40101 | 未登录/Token 无效 | 重新登录 |
| 40301 | 无权限（Token 类型不匹配） | 确认用管理端 token |
| 40401 | 资源不存在 | 检查接口路径 |
| 40901 | 状态不允许操作 | 业务状态机问题 |
| 50001 | 服务器内部错误 | 查看后端日志 |

---

## 八、Vite proxy 配置

`admin-web/vite.config.ts`：
```ts
server: {
  host: '0.0.0.0',   // 允许外部 IP 访问
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',  // 服务端转发，与客户端 PC 无关
      changeOrigin: true,
    },
  },
},
```
