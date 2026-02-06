# 🚀 快速开始

## 开发环境启动

⚠️ **重要提示**：请使用 **HTTP** 而不是 **HTTPS** 访问开发服务器

✅ **正确**：http://localhost:5174
❌ **错误**：https://localhost:5174

---

## 启动步骤

### 1. 启动后端服务

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端服务

```bash
cd new-fronted
npm install  # 首次运行
npm run dev
```

### 3. 访问应用

在浏览器中打开：**http://localhost:5174**

---

## 🔧 常见问题

### ❌ ERR_ALPN_NEGOTIATION_FAILED 错误

**症状**：浏览器控制台显示 `ERR_ALPN_NEGOTIATION_FAILED` 错误，API 请求失败。

**原因**：浏览器尝试使用 HTTPS 连接到开发服务器，但 Vite dev server 只提供 HTTP 服务。

**快速修复**：

1. **确保使用 HTTP 访问**
   ```
   http://localhost:5174  ✅
   https://localhost:5174 ❌
   ```

2. **清除浏览器 HSTS 缓存**

   **Chrome**：
   - 访问 `chrome://net-internals/#hsts`
   - 在 "Delete domain security policies" 中输入 `localhost`
   - 点击 "Delete"

   **Firefox**：
   - 访问 `about:config`
   - 搜索 `security.enterprise_roots.enabled`
   - 右键 → 修改 → 设为 `false`

3. **禁用 HTTPS 扩展**
   - 关闭 "HTTPS Everywhere" 等扩展
   - 禁用浏览器 "始终使用安全连接" 功能

4. **运行诊断脚本**
   ```bash
   cd new-fronted
   ./diagnose-alpn-error.sh
   ```

**详细解决方案**：参见 [ALPN-ERROR-SOLUTIONS.md](./ALPN-ERROR-SOLUTIONS.md)

---

## 📦 项目结构

```
new-video/
├── backend/                 # FastAPI 后端
│   ├── main.py            # 主应用
│   └── ...
├── new-fronted/           # Vite + React 前端
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # React 组件
│   │   └── ...
│   ├── vite.config.ts    # Vite 配置（含代理设置）
│   ├── .env.development  # 开发环境配置
│   └── diagnose-alpn-error.sh  # 诊断脚本
└── ALPN-ERROR-SOLUTIONS.md  # ALPN 错误完整解决方案
```

---

## 🎯 开发环境配置

### API 请求配置

开发环境默认使用 **Vite 代理**：

```typescript
// src/api/client.ts
const baseUrl = import.meta.env.VITE_API_URL || '/api';
```

**工作原理**：
```
浏览器 → http://localhost:5174/api/...
         ↓
    Vite 代理
         ↓
    http://127.0.0.1:8000/api/...
```

**优点**：
- ✅ 避免 CORS 问题
- ✅ 避免 ALPN 协商问题
- ✅ 更容易调试
- ✅ 符合开发环境最佳实践

### 直连后端模式（可选）

如果需要直连后端，修改 `.env.development`：

```env
VITE_API_URL=http://127.0.0.1:8000
```

⚠️ **注意**：直连模式可能遇到 ALPN 协商问题，建议使用代理模式。

---

## 🔍 调试工具

### 诊断脚本

运行诊断脚本检查配置和连接状态：

```bash
cd new-fronted
./diagnose-alpn-error.sh
```

脚本会检查：
- ✅ 后端服务是否运行
- ✅ 前端服务是否运行
- ✅ 端口监听状态
- ✅ 配置文件是否正确
- ✅ HTTP/HTTPS 连接测试

### 浏览器开发者工具

**Network 标签**：
- 检查请求 URL 是 HTTP 还是 HTTPS
- 查看请求头 `Upgrade-Insecure-Requests: 1`

**Console 标签**：
- 查找 ALPN 相关错误
- 检查 HSTS 警告

---

## 📖 技术说明

### 为什么开发环境不支持 HTTPS？

Vite dev server 默认只提供 HTTP 服务，这是正常的设计：
- 开发环境不需要 HTTPS
- 配置 HTTPS 需要额外证书和配置
- HTTP 足够用于开发和测试

### 为什么会出现 ALPN 错误？

当浏览器尝试 HTTPS 连接时：
```
浏览器 → https://localhost:5174
  ↓
TLS handshake + ALPN 协商
  ↓
服务器不支持 TLS → 无法响应
  ↓
❌ ERR_ALPN_NEGOTIATION_FAILED
```

### 为什么 curl 正常？

```bash
curl http://localhost:8000  # 明确使用 HTTP
```

curl 明确指定协议，不会自动升级到 HTTPS。

---

## 🚨 故障排除

### 问题 1：API 请求失败

**检查清单**：
- [ ] 后端服务是否运行？(`http://127.0.0.1:8000/docs`)
- [ ] 前端服务是否运行？(`http://localhost:5174`)
- [ ] 使用 HTTP 还是 HTTPS 访问？
- [ ] 浏览器控制台有什么错误？
- [ ] Network 标签中请求状态是什么？

### 问题 2：CORS 错误

**解决**：使用 Vite 代理模式（默认配置）

### 问题 3：代理不工作

**检查**：
- `vite.config.ts` 中的 proxy 配置
- 后端服务是否监听 `127.0.0.1:8000`
- 浏览器控制台是否有代理错误

### 问题 4：清除 HSTS 后仍然不行

**尝试**：
1. 重启浏览器
2. 使用隐私/无痕模式
3. 尝试其他浏览器
4. 检查系统代理设置
5. 关闭 VPN 或代理软件

---

## 📚 相关文档

- [ALPN-ERROR-SOLUTIONS.md](./ALPN-ERROR-SOLUTIONS.md) - 完整诊断和解决方案
- [Vite 代理配置](https://vite.dev/config/server-options.html#server-proxy)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

## 💡 最佳实践

### 开发环境

✅ **推荐**：
- 使用 Vite 代理模式
- HTTP 访问开发服务器
- 清除浏览器 HSTS 缓存
- 禁用自动 HTTPS 扩展

❌ **避免**：
- HTTPS 访问开发服务器
- 直连后端（除非必要）
- 使用生产环境配置

### 团队协作

1. 在文档中说明 HTTP/HTTPS 访问规则
2. 代码审查时检查环境配置
3. 新成员入职时说明 ALPN 问题
4. 定期更新文档和解决方案

---

## 🤝 获取帮助

如果遇到问题：

1. 查看 [ALPN-ERROR-SOLUTIONS.md](./ALPN-ERROR-SOLUTIONS.md)
2. 运行诊断脚本：`./diagnose-alpn-error.sh`
3. 检查浏览器开发者工具
4. 搜索项目 Issues 或提交新 Issue

---

**最后更新**：2026-02-03
