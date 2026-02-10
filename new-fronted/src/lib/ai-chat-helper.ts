export interface InteractionPayload {
    genre?: string;
    [key: string]: any;
}

/**
 * 清理和解析 AI 响应内容
 * 处理多种格式：纯文本、JSON数组、字符串化的JSON数组、Master Router JSON
 * 移除不应显示给用户的结构化数据
 */
export function cleanJsonFromContent(content: string): string {
    if (!content) return '';

    let cleaned = content;

    // 情况0: 提取 Master Router JSON 中的 ui_feedback 字段
    // 支持格式：
    // 1. 单步骤模式: {"thought_process": "...", "target_agent": "...", "ui_feedback": "..."}
    // 2. 多步骤模式: {"intent_analysis": "...", "workflow_plan": [...], "ui_feedback": "..."}
    if (typeof cleaned === 'string' && cleaned.trim().startsWith('{') && cleaned.trim().endsWith('}')) {
        try {
            // 先移除可能的 markdown 代码块标记
            let jsonStr = cleaned.trim();
            if (jsonStr.startsWith('```json')) {
                jsonStr = jsonStr.replace(/^```json\n?/, '').replace(/\n?```$/, '').trim();
            } else if (jsonStr.startsWith('```')) {
                jsonStr = jsonStr.replace(/^```\n?/, '').replace(/\n?```$/, '').trim();
            }

            const parsed = JSON.parse(jsonStr);
            if (parsed && typeof parsed === 'object') {
                // 如果是 Master Router JSON，提取 ui_feedback（优先显示给用户）
                if (parsed.ui_feedback && typeof parsed.ui_feedback === 'string' && parsed.ui_feedback.trim()) {
                    return parsed.ui_feedback.trim();
                }

                // 如果 ui_feedback 为空，但有 thought_process/intent_analysis，显示它
                const analysis = parsed.thought_process || parsed.intent_analysis;
                if (analysis && typeof analysis === 'string' && analysis.trim()) {
                    return analysis.trim();
                }

                // 检查是否有 workflow_plan（多步骤模式），显示步骤信息
                if (parsed.workflow_plan && Array.isArray(parsed.workflow_plan) && parsed.workflow_plan.length > 0) {
                    const steps = parsed.workflow_plan.map((step: any, idx: number) =>
                        `${idx + 1}. ${step.task || step.agent || '执行任务'}`
                    ).join('\n');
                    return `正在执行多步骤任务（共 ${parsed.workflow_plan.length} 步）：\n${steps}`;
                }

                // 如果是包含 content/text 的 JSON，提取内容
                if (parsed.content) {
                    return typeof parsed.content === 'string' ? parsed.content.trim() : String(parsed.content).trim();
                }
                if (parsed.text) {
                    return typeof parsed.text === 'string' ? parsed.text.trim() : String(parsed.text).trim();
                }

                const possibleFields = ['response', 'answer', 'result', 'output', 'message', 'data', 'skeleton', 'outline', 'content_text'];
                for (const field of possibleFields) {
                    if (parsed[field] && typeof parsed[field] === 'string') {
                        return parsed[field].trim();
                    }
                }

                if (parsed.toString && typeof parsed.toString === 'function') {
                    const str = parsed.toString();
                    if (str !== '[object Object]') {
                        return str.trim();
                    }
                }

                return '';
            }
        } catch {
        }
    }

    // 情况1: 内容是一个字符串化的JSON数组，如 "[{'type': 'text', 'text': '...'}]"
    if (typeof cleaned === 'string' && cleaned.trim().startsWith('[') && cleaned.trim().endsWith(']')) {
        try {
            let parsed = cleaned;
            if (cleaned.includes("'") && !cleaned.includes('"type"')) {
                parsed = cleaned.replace(/'/g, '"');
            }
            const arr = JSON.parse(parsed);
            if (Array.isArray(arr)) {
                const textParts = arr.map((item: any) => {
                    if (typeof item === 'string') return item;
                    if (item && typeof item === 'object') {
                        return item.text || item.content || '';
                    }
                    return '';
                });
                cleaned = textParts.join('');
            }
        } catch {
            const textMatches = cleaned.match(/"text"\s*:\s*"([^"]+)"/g);
            if (textMatches) {
                const extracted = textMatches.map(match => {
                    const textMatch = match.match(/"text"\s*:\s*"([^"]+)"/);
                    return textMatch ? textMatch[1] : '';
                });
                cleaned = extracted.join('');
            }
        }
    }

    // 情况2: 移除暴露的 JSON 对象块（市场分析数据、赛道推荐等）
    cleaned = cleaned.replace(/\{\s*"(compatibility_score|trend_index|recommended_tracks|swot|strengths|weaknesses)"[\s\S]*?\n\s*\}/g, '');

    // 情况3: 移除赛道推荐数组
    cleaned = cleaned.replace(/\[\s*\{\s*"(label|genre|style|track|description|potential_roi)"[\s\S]*?\}\s*\]/g, '');



    // 情况5: 移除 <thinking> ... </thinking> 块 (如果前端不想显示)
    // 如果需要显示思考过程，可以在这里通过标志位控制
    // cleaned = cleaned.replace(/<thinking>[\s\S]*?<\/thinking>/g, '');

    // 情况6: 清理连续的空行
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

    // 情况7: 清理开头/结尾的空白
    cleaned = cleaned.trim();

    return cleaned;
}


