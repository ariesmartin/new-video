import express from "express";
import cors from "cors";
import puppeteer from "puppeteer";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { z } from "zod";
const app = express();
app.use(cors());
app.use(express.json());
// ===== Health Check Endpoint =====
app.get("/health", (_req, res) => {
    res.json({
        status: "ok",
        server: "puppet-browsing",
        version: "1.0.0",
        capabilities: ["navigate", "screenshot", "scrape_text", "extract_links"]
    });
});
// ===== Browser Pool (Reuse for performance) =====
let browserInstance = null;
async function getBrowser() {
    if (!browserInstance || !browserInstance.isConnected()) {
        console.log("Launching new browser instance...");
        browserInstance = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        });
    }
    return browserInstance;
}
async function withPage(action) {
    const browser = await getBrowser();
    const page = await browser.newPage();
    // Set reasonable defaults
    await page.setViewport({ width: 1280, height: 720 });
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");
    try {
        return await action(page);
    }
    finally {
        await page.close();
    }
}
// ===== Create MCP Server =====
const server = new McpServer({
    name: "puppet-browsing",
    version: "1.0.0",
});
// ===== Tool: Navigate =====
server.tool("navigate", { url: z.string().url() }, async ({ url }) => {
    console.log(`[navigate] ${url}`);
    try {
        const result = await withPage(async (page) => {
            const response = await page.goto(url, {
                waitUntil: "networkidle2",
                timeout: 30000
            });
            const title = await page.title();
            const status = response?.status() || 0;
            const finalUrl = page.url();
            return {
                title,
                status,
                url: finalUrl,
                success: status >= 200 && status < 400
            };
        });
        return {
            content: [{
                    type: "text",
                    text: `Navigated to: ${result.url}\nTitle: ${result.title}\nStatus: ${result.status}`
                }],
        };
    }
    catch (e) {
        const error = e instanceof Error ? e.message : String(e);
        return {
            content: [{ type: "text", text: `Navigation error: ${error}` }],
            isError: true,
        };
    }
});
// ===== Tool: Screenshot =====
server.tool("screenshot", { url: z.string().url() }, async ({ url }) => {
    console.log(`[screenshot] ${url}`);
    try {
        const result = await withPage(async (page) => {
            await page.goto(url, { waitUntil: "networkidle2", timeout: 30000 });
            const b64 = await page.screenshot({ encoding: "base64", fullPage: false });
            const title = await page.title();
            return { b64, title };
        });
        return {
            content: [
                { type: "text", text: `Screenshot captured for: ${url}\nTitle: ${result.title}` },
                { type: "image", data: result.b64, mimeType: "image/png" }
            ],
        };
    }
    catch (e) {
        const error = e instanceof Error ? e.message : String(e);
        return {
            content: [{ type: "text", text: `Screenshot error: ${error}` }],
            isError: true,
        };
    }
});
// ===== Tool: Scrape Text =====
server.tool("scrape_text", { url: z.string().url() }, async ({ url }) => {
    console.log(`[scrape_text] ${url}`);
    try {
        const text = await withPage(async (page) => {
            await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
            // Remove scripts and styles for clean text
            await page.evaluate(() => {
                const elements = document.querySelectorAll('script, style, noscript, iframe');
                elements.forEach(el => el.remove());
            });
            const bodyText = await page.evaluate(() => document.body.innerText);
            return bodyText.trim().slice(0, 10000); // Limit output
        });
        return {
            content: [{ type: "text", text: text || "No text content found" }],
        };
    }
    catch (e) {
        const error = e instanceof Error ? e.message : String(e);
        return {
            content: [{ type: "text", text: `Scrape error: ${error}` }],
            isError: true,
        };
    }
});
// ===== Tool: Extract Links =====
server.tool("extract_links", { url: z.string().url() }, async ({ url }) => {
    console.log(`[extract_links] ${url}`);
    try {
        const links = await withPage(async (page) => {
            await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
            return await page.evaluate(() => {
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                return anchors
                    .map(a => ({
                    text: a.textContent?.trim() || '',
                    href: a.getAttribute('href') || ''
                }))
                    .filter(link => link.href && !link.href.startsWith('#'))
                    .slice(0, 50); // Limit
            });
        });
        const formatted = links.map(l => `- [${l.text || 'No text'}](${l.href})`).join('\n');
        return {
            content: [{ type: "text", text: `Found ${links.length} links:\n${formatted}` }],
        };
    }
    catch (e) {
        const error = e instanceof Error ? e.message : String(e);
        return {
            content: [{ type: "text", text: `Extract error: ${error}` }],
            isError: true,
        };
    }
});
// ===== SSE Transport Setup =====
let transport = null;
app.get("/sse", async (req, res) => {
    console.log("[SSE] New connection");
    transport = new SSEServerTransport("/messages", res);
    await server.connect(transport);
});
app.post("/messages", async (req, res) => {
    if (transport) {
        await transport.handlePostMessage(req, res);
    }
    else {
        res.status(404).json({ error: "No active SSE connection. Connect to /sse first." });
    }
});
// ===== Graceful Shutdown =====
async function shutdown() {
    console.log("Shutting down...");
    if (browserInstance) {
        await browserInstance.close();
    }
    process.exit(0);
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
// ===== Start Server =====
const PORT = process.env.PORT || 8001;
app.listen(PORT, () => {
    console.log("=".repeat(60));
    console.log("Browser Automation MCP Server (Puppeteer)");
    console.log("=".repeat(60));
    console.log(`SSE Endpoint:    http://localhost:${PORT}/sse`);
    console.log(`Health Check:    http://localhost:${PORT}/health`);
    console.log(`Available Tools: navigate, screenshot, scrape_text, extract_links`);
    console.log("=".repeat(60));
});
//# sourceMappingURL=index.js.map