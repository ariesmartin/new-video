# ALPN 协商失败问题 - 完整诊断与解决方案

## 问题描述

浏览器访问前端应用时出现 `ERR_ALPN_NEGOTIATION_FAILED` 错误，导致 API 请求失败。

## 根本原因

**浏览器尝试使用 HTTPS 连接到 `localhost:5174`，但 Vite dev server 只提供 HTTP 服务**

### 问题发生流程

```
浏览器尝试: https://localhost:5174/api/...
    ↓
发起 TLS handshake
    ↓
ALPN 协商 (浏览器提供: h2, http/1.1)
    ↓
服务器响应: 非 TLS 数据 (HTTP 响应或拒绝连接)
    ↓
❌ ERR_ALPN_NEGOTIATION_FAILED
```

### 为什么浏览器会尝试 HTTPS？

1. **浏览器扩展自动升级 HTTPS**（最常见）
   - HTTPS Everywhere
   - 其他安全增强扩展

2. **浏览器设置**
   - "始终使用安全连接" 功能
   - HSTS (HTTP Strict Transport Security) 缓存

3. **用户操作**
   - 手动输入 `https://localhost:5174`
   - 书签保存的是 HTTPS URL

## 解决方案

### ✅ 方案 1：使用 Vite 代理（推荐）

**优点**：
- ✅ 无需修改浏览器配置
- ✅ 符合开发环境最佳实践
- ✅ 避免 CORS 问题
- ✅ 更容易调试

**已实施配置**：

#### 1. 修改 `src/api/client.ts`

```typescript
import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from '../types/api';

// 获取环境变量或使用代理路径
const baseUrl = import.meta.env.VITE_API_URL || '/api';

export const client = createClient<paths>({
  baseUrl,
});
```

#### 2. 修改 `.env.development`

```env
# 开发环境使用 Vite 代理（推荐）
# 如果直连后端有问题，取消下面的注释：
# VITE_API_URL=http://127.0.0.1:8000
```

#### 3. Vite 代理配置（已存在）

```typescript
// vite.config.ts
server: {
  port: 5174,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
      secure: false,
      ws: true,
    },
  },
}
```

#### 4. 使用说明

访问应用时使用 HTTP：
```
✅ http://localhost:5174
❌ https://localhost:5174
```

---

### 🔧 方案 2：清理浏览器 HTTPS 缓存

如果方案 1 仍然遇到问题，执行以下步骤：

#### Chrome

1. **清除 HSTS 设置**
   - 地址栏输入：`chrome://net-internals/#hsts`
   - 在 "Delete domain security policies" 中输入：`localhost`
   - 点击 "Delete"

2. **清除缓存**
   - `Ctrl + Shift + Delete` (Windows) / `Cmd + Shift + Delete` (Mac)
   - 选择 "缓存的图片和文件"
   - 点击 "清除数据"

3. **禁用 HTTPS 扩展**
   - 打开扩展管理：`chrome://extensions/`
   - 临时禁用 HTTPS Everywhere 等扩展
   - 刷新页面测试

#### Firefox

1. **清除 HSTS 设置**
   - 地址栏输入：`about:config`
   - 搜索 `security.enterprise_roots.enabled`
   - 右键 → 修改 → 设为 `false`

2. **清除缓存**
   - `Ctrl + Shift + Delete` (Windows) / `Cmd + Shift + Delete` (Mac)
   - 选择 "缓存"
   - 点击 "立即清除"

3. **禁用 HTTPS-Only 模式**
   - 地址栏左侧点击 🔒 图标
   - 关闭 "仅 HTTPS 模式"

---

### 🚀 方案 3：为 Vite 配置 HTTPS（可选）

如果确实需要使用 HTTPS（如测试 PWA、混合内容等），可以为 Vite 配置 HTTPS：

```bash
# 安装 mkcert（创建本地证书）
choco install mkcert  # Windows
brew install mkcert   # macOS
sudo apt install mkcert  # Linux

# 生成证书
mkcert -install
mkcert localhost 127.0.0.1 ::1
```

修改 `vite.config.ts`：

```typescript
import fs from 'fs'
import path from 'path'

export default defineConfig({
  server: {
    port: 5174,
    https: {
      key: fs.readFileSync(path.resolve(__dirname, 'localhost-key.pem')),
      cert: fs.readFileSync(path.resolve(__dirname, 'localhost.pem')),
    },
    proxy: {
      // ... proxy config
    },
  },
})
```

---

### 🔍 方案 4：诊断工具

如果问题仍然存在，使用以下工具诊断：

#### 1. 浏览器开发者工具

**Network 标签**：
- 查看请求的 URL 是 HTTP 还是 HTTPS
- 检查请求头中是否有 `Upgrade-Insecure-Requests: 1`

**Console 标签**：
- 查找具体的错误信息
- 检查是否有 HSTS 相关警告

#### 2. 浏览器状态检查

**Chrome**：
- 访问 `chrome://net-internals/#hsts` - 查看 localhost 的 HSTS 状态
- 访问 `chrome://net-internals/#sockets` - 查看当前连接状态

**Firefox**：
- 访问 `about:networking#dns` - 查看 DNS 缓存
- 访问 `about:preferences#privacy` - 检查隐私设置

#### 3. 命令行诊断

```bash
# 测试后端连接
curl -v http://127.0.0.1:8000/

# 测试前端 HTTP 连接
curl -v http://localhost:5174/

# 测试前端 HTTPS 连接（会失败）
curl -v https://localhost:5174/

# 检查端口监听
netstat -tlnp | grep -E ":(5174|8000)"
```

---

## 预防措施

1. **在 README 中说明**
   ```markdown
   ## 开发环境启动

   ⚠️ 重要：请使用 HTTP 而不是 HTTPS 访问开发服务器

   ✅ 正确：http://localhost:5174
   ❌ 错误：https://localhost:5174

   如果遇到 ALPN 错误，请参考 [ALPN-ERROR-SOLUTIONS.md](./ALPN-ERROR-SOLUTIONS.md)
   ```

2. **添加 package.json 脚本**
   ```json
   {
     "scripts": {
       "dev": "npm run check-protocol && vite",
       "check-protocol": "echo '⚠️ 请使用 http://localhost:5174 访问应用（不要使用 HTTPS）'"
     }
   }
   ```

3. **团队沟通**
   - 在团队会议中说明此问题
   - 在文档中添加常见问题章节
   - 建议团队成员关闭自动 HTTPS 扩展

---

## FAQ

### Q1: 为什么之前没有这个问题？

A: 可能的原因：
- 最近安装了 HTTPS 相关的浏览器扩展
- 浏览器更新后改变了默认行为
- 某个网站设置了 HSTS 策略影响到 localhost
- 系统更新改变了网络配置

### Q2: openapi-fetch 是否强制使用 HTTP/2？

A: **不强制**。openapi-fetch 只是对原生 Fetch API 的封装，不控制协议协商。协议由浏览器自动处理。

### Q3: 为什么 curl 正常但浏览器不行？

A: curl 明确指定了 HTTP 协议：
```bash
curl http://localhost:8000  # 明确使用 HTTP
```

浏览器可能根据扩展或设置自动升级到 HTTPS。

### Q4: 生产环境也会有这个问题吗？

A: 不会。生产环境应该配置 HTTPS 证书，浏览器可以正常协商协议。这个问题只存在于开发环境。

---

## 技术背景

### ALPN (Application-Layer Protocol Negotiation)

ALPN 是 TLS 协议扩展，用于在 TLS handshake 期间协商应用层协议（如 HTTP/2, HTTP/1.1）。

**协商流程**：
```
ClientHello
  ├── 支持的协议列表: [h2, http/1.1]
  ├── TLS 版本
  └── 其他 TLS 参数

ServerHello
  ├── 选择协议: http/1.1  (如果支持)
  ├── TLS 版本
  └── 其他 TLS 参数

❌ 如果服务器不是 HTTPS，则无法响应 ServerHello
```

### 为什么会显示 "ALPN_NEGOTIATION_FAILED"

当浏览器尝试建立 HTTPS 连接但服务器不支持时：
1. 浏览器发送 TLS ClientHello
2. 服务器返回非 TLS 响应（如 HTTP 400、连接拒绝等）
3. 浏览器无法完成 ALPN 协商
4. 报错：`ERR_ALPN_NEGOTIATION_FAILED`

---

## 更新日志

- **2026-02-03**: 初始版本，添加完整诊断和解决方案
- 配置 client.ts 使用环境变量或代理路径
- 更新 .env.development 默认使用代理

---

## 参考

- [MDN: HTTP](https://developer.mozilla.org/zh-CN/docs/Web/HTTP)
- [MDN: HSTS](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/Strict-Transport-Security)
- [Vite: Server Proxy](https://vite.dev/config/server-options.html#server-proxy)
- [Chrome HSTS 清理](https://support.google.com/chrome/answer/7061588)
