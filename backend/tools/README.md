# Backend Tools 使用指南

## 概述

所有工具都**内置于 Backend**，无需启动额外服务！只需启动 Backend 即可使用全部功能。

```bash
cd backend && uvicorn main:app --reload
```

---

## 可用工具

| 工具 | 功能 | 支持平台 |
|-----|------|---------|
| `duckduckgo_search` | 网络搜索 | 全网 |
| `video_search` | 视频搜索 | YouTube, Bilibili |
| `video_info` | 视频详情 | YouTube, Bilibili, 抖音*, TikTok*, 小红书* |
| `browser_scrape` | 网页抓取 | 任意网页 |
| `browser_screenshot` | 网页截图 | 任意网页 |
| `browser_extract_links` | 链接提取 | 任意网页 |

> \* 标记的平台需要配置 cookies

---

## 配置抖音/小红书等平台

这些平台需要认证才能获取视频信息。

### 方法 1: 导出 Cookies (推荐)

1. 使用 Chrome 扩展 [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 
2. 登录抖音网页版 (https://www.douyin.com)
3. 点击扩展导出 cookies
4. 保存为 `backend/tools/cookies.txt`

### 方法 2: 手动获取

1. 打开浏览器开发者工具 (F12)
2. 登录抖音
3. 在 Network 标签中找到任意请求
4. 复制 Cookie 头
5. 创建 Netscape 格式的 cookies.txt 文件

### Cookies 文件格式

```
# Netscape HTTP Cookie File
.douyin.com	TRUE	/	FALSE	1700000000	sessionid	your_session_id
.douyin.com	TRUE	/	FALSE	1700000000	ttwid	your_ttwid
```

---

## 验证工具

运行测试脚本验证所有工具：

```bash
cd /media/martin/HDD2/new-video
source backend/.venv/bin/activate
PYTHONPATH=. python test_tools.py
```

---

## 技术架构

```
Backend (FastAPI)
    │
    ├── DuckDuckGo 搜索 (ddgs 库)
    │
    ├── 视频工具 (yt-dlp)
    │   ├── video_search → YouTube/Bilibili 搜索
    │   └── video_info → 多平台视频详情
    │
    └── 浏览器工具 (Playwright)
        ├── browser_scrape → 页面文本
        ├── browser_screenshot → 截图
        └── browser_extract_links → 链接提取
```

**优势**: 
- 无需启动额外服务
- 一键部署
- 自动 Fallback
