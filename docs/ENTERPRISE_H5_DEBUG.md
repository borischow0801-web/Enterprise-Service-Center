# 企业端 H5 调试指南

## 1. 启动 enterprise-h5

```bash
cd /app/Enterprise-Service-Center/enterprise-h5

# 安装依赖（首次）
npm install

# 启动开发服务器（监听所有网卡，端口 5174）
npm run dev
```

启动成功后控制台输出：
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5174/
➜  Network: http://10.217.19.22:5174/
```

其他 PC 通过 `http://10.217.19.22:5174` 访问。

---

## 2. 配置接口地址

接口配置采用 **Vite 代理**方案，无需在浏览器端暴露后端地址。

**`.env.development`**（当前配置）：
```
VITE_API_BASE_URL=
```

**`vite.config.ts`** 代理配置：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
}
```

浏览器发出相对路径请求 → Vite 服务端转发到后端，任意客户端 PC 都可使用，**不需要修改任何代码**。

如需切换后端地址，修改 `vite.config.ts` 中 `target` 值即可。

---

## 3. 企业端 Mock 登录默认参数

访问 `http://10.217.19.22:5174/login`，页面预填以下默认值：

| 字段 | 默认值 |
|------|--------|
| 企业名称 | 威海测试科技有限公司 |
| 统一社会信用代码 | 91371000TEST000001 |
| 法人姓名 | 张三 |
| 法人手机 | 13800138000 |
| 所属区划 | 环翠区 |

> **说明**：企业端使用 Mock 登录，直接写入本地 Token，不验证企业是否真实存在于数据库。

登录成功后跳转首页（`/home`），Token 存储在 `localStorage.enterprise_token`，与管理端的 `esc_admin_token` 完全隔离。

---

## 4. 企业提交诉求流程

1. **首页** → 点击「提交新诉求」
2. **提交诉求页** (`/appeals/create`)：
   - 填写诉求标题、诉求内容
   - 选择紧急程度（从字典 API 加载：`GET /api/common/dictionaries/URGENCY_LEVEL`）
   - 选择所属行业（可选，字典类型 `INDUSTRY_TYPE`）
   - 选择所属区划（必填，字典类型 `REGION`）
   - 联系人/联系电话自动从 Mock 登录信息填充
3. 点击「提交诉求」→ 调用 `POST /api/enterprise/appeals`
4. 成功后跳转诉求列表（`/appeals`）

**请求示例**：
```json
POST /api/enterprise/appeals
{
  "title": "厂房租金减免申请",
  "content": "受疫情影响，希望获得租金减免政策支持",
  "contactName": "张三",
  "contactPhone": "13800138000",
  "urgencyLevel": "NORMAL",
  "industryCode": "MANUFACTURING",
  "industryName": "制造业",
  "regionCode": "HUANCUI",
  "regionName": "环翠区"
}
```

---

## 5. 管理端办理诉求流程

访问 `http://10.217.19.22:5173`（admin-web）。

### 完整办理路径（中心直接办理）

```
企业提交 → PENDING_ACCEPT
    ↓ 受理（accept）
ACCEPTED
    ↓ 中心办理（centerHandle）
PENDING_EVALUATION ← 企业可评价
```

### 完整办理路径（转办部门）

```
ACCEPTED
    ↓ 转办（assign）
DEPT_HANDLING
    ↓ 部门答复（deptReply）
DEPT_REPLIED / CENTER_REVIEWING
    ↓ 审核通过（reviewReply）
PENDING_EVALUATION ← 企业可评价
```

### 各状态可用操作

| 状态 | 可用操作 |
|------|---------|
| PENDING_ACCEPT（待受理） | 受理、退回补充、驳回 |
| ACCEPTED（已受理） | 中心办理、转办、退回补充、驳回 |
| CENTER_HANDLING（中心办理中） | 中心办理 |
| DEPT_HANDLING（部门办理中） | 部门答复 |
| CENTER_REVIEWING（中心审核中） | 审核答复 |
| REVIEW_REJECTED（审核退回） | 转办、部门答复 |
| PENDING_EVALUATION / EVALUATED | 跟进 |

---

## 6. 企业评价流程

1. **诉求列表** → 切换到「待评价」Tab → 点击诉求卡片
2. **诉求详情页** → 状态横幅显示「待评价」→ 点击「去评价」按钮
3. **评价页** (`/appeals/:id/evaluate`)：
   - 选择满意度（满意 / 基本满意 / 不满意）
   - 星级评分（1-5 星）
   - 是否解决主要诉求（已解决 / 未解决）
   - 评价意见（可选）
4. 点击「提交评价」→ 调用 `POST /api/enterprise/appeals/:id/evaluate`
5. 成功后跳回诉求详情，显示「我的评价」区块

> 评价入口仅在状态为 `REPLIED` 或 `PENDING_EVALUATION` 且未评价时显示。

---

## 7. 常见错误排查

### 401 未授权

**现象**：请求返回 `{"code": 40101, "message": "未登录或登录已过期"}`

**原因与处理**：
- Token 未生成或已过期 → 重新 Mock 登录
- `localStorage.enterprise_token` 被清除 → 清空后自动跳转 `/login`
- 访问管理端接口（`/api/admin/...`）→ 企业端应只调用 `/api/enterprise/...` 接口

```bash
# 检查 Token 是否存在（浏览器控制台）
localStorage.getItem('enterprise_token')
```

---

### 404 Not Found

**现象**：接口返回 404 或 Vite 代理报错

**排查步骤**：
1. 确认后端正在运行：`curl http://127.0.0.1:8000/api/health`
2. 确认路由已注册（后端日志应显示路由）
3. 检查请求路径，企业端接口前缀：`/api/enterprise/`，公共接口：`/api/common/`

---

### 422 Unprocessable Entity

**现象**：后端返回 `{"detail": [...]}`，提示字段校验失败

**原因**：请求体缺少必填字段或字段类型不匹配

**排查步骤**：
1. 打开浏览器 DevTools → Network → 查看请求 Payload
2. 对照后端 API 文档或 `http://127.0.0.1:8000/docs` 的 Swagger UI
3. 常见问题：`regionCode` 必填未选择、`resolvedFlag` 需为整数（0/1）

---

### 500 Internal Server Error

**现象**：后端返回 500 或接口超时

**排查步骤**：
1. 查看后端控制台日志（uvicorn 输出）
2. 检查数据库连接：`app/database.py` 中 SQLite 文件路径
3. 检查字典数据是否初始化：

```bash
cd /app/Enterprise-Service-Center
python scripts/init_dict.py
```

---

### 页面空白 / 组件不渲染

**现象**：页面加载但内容为空

**排查步骤**：
1. 浏览器 DevTools → Console，查看 JS 错误
2. 确认 Vant 组件正确导入（`main.ts` 已全局引入 Vant CSS）
3. Vite HMR 热更新失效时，强制刷新：`Ctrl+Shift+R`

---

### 字典选项为空

**现象**：诉求提交页的区划/行业/紧急程度 Picker 无选项

**排查步骤**：
1. 确认字典已初始化：`python scripts/init_dict.py`
2. 确认接口可访问：`curl http://127.0.0.1:8000/api/common/dictionaries/REGION`
3. 查看 Network 请求是否成功（200 且 `data` 非空数组）

---

## 附：快速启动命令

```bash
# 1. 启动后端
cd /app/Enterprise-Service-Center
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. 启动管理端（新终端）
cd /app/Enterprise-Service-Center/admin-web
npm run dev

# 3. 启动企业端 H5（新终端）
cd /app/Enterprise-Service-Center/enterprise-h5
npm run dev

# 4. 初始化字典数据（首次）
cd /app/Enterprise-Service-Center
python scripts/init_dict.py
```

| 服务 | 地址 |
|------|------|
| 后端 API | http://10.217.19.22:8000 |
| API 文档 | http://10.217.19.22:8000/docs |
| 管理端 | http://10.217.19.22:5173 |
| 企业端 H5 | http://10.217.19.22:5174 |
