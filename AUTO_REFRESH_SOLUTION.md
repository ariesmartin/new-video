# 生成状态自动刷新方案

## 问题
用户刷新页面后，如果后端正在生成，前端需要**自动检测生成完成并更新消息**，而不是让用户手动刷新。

## 方案对比

### 方案1：轮询（已实现）
- 前端每隔几秒调用 initChat 检查状态
- 简单可靠，但有一定延迟

### 方案2：SSE 重连（推荐）
- 刷新后自动重新连接 SSE
- 后端继续推送生成进度和结果
- 实时性好，无需轮询

### 方案3：WebSocket
- 需要前后端都实现 WebSocket 连接管理
- 适合双向通信场景
- 对于这个场景略显复杂

## 推荐实现：方案2 SSE 重连

### 前端修改
```typescript
// AIAssistantPanel.tsx
useEffect(() => {
  // 如果检测到后端正在生成，自动重连 SSE
  if (isBackendGenerating && projectId) {
    console.log('[AIAssistantPanel] Backend is generating, auto-reconnecting SSE...');
    
    // 重新连接 SSE 接收生成结果
    const reconnectSSE = async () => {
      try {
        await chatService.streamMessage(
          '', // 空消息，只监听
          {
            onMessage: (msg) => {
              // 接收生成内容
              setStreamingContent(prev => prev + msg.content);
            },
            onComplete: () => {
              // 生成完成，刷新消息列表
              initChat(projectId);
            },
          },
          projectId
        );
      } catch (error) {
        console.error('[AIAssistantPanel] SSE reconnect failed:', error);
      }
    };
    
    reconnectSSE();
  }
}, [isBackendGenerating, projectId]);
```

### 后端修改
```python
# graph.py
# 在 chat_endpoint 中支持空消息监听模式
if not request.message:
    # 用户只是想监听当前生成状态
    # 返回当前 checkpoint 状态或建立 SSE 连接
    pass
```

## 快速修复（方案1 轮询）

如果希望快速实现，使用轮询方案：

```typescript
// useAIChatInit.ts
useEffect(() => {
  if (!isGenerating || !projectId) return;
  
  // 每隔3秒轮询检查生成状态
  const interval = setInterval(async () => {
    await initChat(projectId);
  }, 3000);
  
  return () => clearInterval(interval);
}, [isGenerating, projectId, initChat]);
```

## 建议

对于当前项目，建议：
1. **短期**：使用轮询方案（已实现基础，只需添加自动刷新）
2. **长期**：优化 SSE 支持重连，提供更好的实时体验
3. **WebSocket**：如果未来需要双向实时通信（如协同编辑），再考虑实现
