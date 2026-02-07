import React, { type ReactNode, isValidElement } from 'react';

// 递归提取文本内容的辅助函数
const getTextContent = (node: ReactNode): string => {
    if (typeof node === 'string' || typeof node === 'number') {
        return String(node);
    }
    if (Array.isArray(node)) {
        return node.map(getTextContent).join('');
    }
    if (isValidElement(node) && node.props) {
        const props = node.props as { children?: ReactNode };
        return props.children ? getTextContent(props.children) : '';
    }
    return '';
};

const PATTERNS = {
    // 场景标题: INT. 或 EXT. 或 内景/外景 开头 (Script)
    SCENE: /^(?:INT\.|EXT\.|内景|外景|场景[ \t]).*$/i,
    // 角色对话: Name: Content (Script)
    DIALOGUE: /^([A-Z\u4e00-\u9fa5]{1,20})((?:\s*\(.*\))?)\s*[：:]\s*(.+)$/,
    // 动作指导: (bracketed text) (Script)
    DIRECTION: /^\(.*\)$/,

    // 方案标题: ### 方案 X (Story Plan) - Usually handled by H3, but distinct here if passed as P
    PLAN_TITLE: /^(?:###\s*)?方案\s*[A-Z0-9\u4e00-\u9fa5]+[：:].*$/,

    // 键值对强调: **Key**: Value (Story Plan)
    KEY_VALUE: /^\s*(.*?)[：:]\s*(.+)$/,
};

interface ScriptRendererProps {
    children?: ReactNode;
    className?: string;
    node?: any; // mdast node
}

/**
 * 智能文本渲染组件 (SmartTextRenderer)
 * 用于替代 ReactMarkdown 的 p 标签渲染，自动识别剧本格式、策划书格式并着色
 */
export const ScriptRenderer: React.FC<ScriptRendererProps> = ({ children, className }) => {
    // 1. 获取纯文本用于正则匹配
    const cleanText = getTextContent(children).trim();

    // --- 剧本模式 (Script Mode) ---

    // 1. 场景标题 (Scene Heading)
    // 如果 ReactMarkdown 将 "INT. SCENE" 渲染为 P (有时发生)，这里捕获它
    if (PATTERNS.SCENE.test(cleanText)) {
        return (
            <h3 className="text-amber-500 font-bold mt-6 mb-3 border-b border-amber-500/20 pb-1 text-base tracking-wide">
                {children}
            </h3>
        );
    }

    // 2. 角色对话 (Dialogue)
    const dialogueMatch = cleanText.match(PATTERNS.DIALOGUE);
    if (dialogueMatch) {
        const [_, name, action, content] = dialogueMatch;
        // 简单启发式：如果名字太长(>10字)或包含"方案"，可能不是角色名
        if (name.length < 10 && !name.includes('方案')) {
            return (
                <div className="flex gap-3 mb-3 leading-relaxed group">
                    <div className="shrink-0 min-w-[3rem] text-right">
                        <span className="text-sky-400 font-bold text-sm block">{name}</span>
                        {action && getTextContent(action).trim() && <span className="text-sky-400/60 text-xs text-right block italic">{getTextContent(action)}</span>}
                    </div>
                    <div className="text-sky-100/90 font-serif border-l-2 border-primary/20 pl-3">
                        {/* 对于对话内容，我们通常希望保留 Markdown 格式 (如 *强调*)。
                 但由于结构已经被拆分，简单起见我们这里渲染 children，
                 并在 CSS 上做一些处理让它看起来像是一体的。
                 或者我们可以尝试从 children 中移除 Name 部分? 
                 这比较复杂，作为 V1，我们直接显示 content (文本) 
                 或者简单地把整个 children 放这里? 
                 放整个 children 会导致 Name 重复显示。
                 
                 V1 方案：只显示解析出的 content 文本。
                 缺点：丢失了 content 里的 Markdown (如 bold/italic)。
                 改进：使用 cleanText 的 content 部分? 
                 
                 Better approach for V2: Just render cleanText content for now to ensure layout works.
              */}
                        {content}
                    </div>
                </div>
            );
        }
    }

    // 3. 动作指导 (Direction)
    if (PATTERNS.DIRECTION.test(cleanText)) {
        return (
            <p className="text-gray-400 italic text-sm pl-12 mb-2">
                {children}
            </p>
        );
    }

    // --- 策划书模式 (Plan Mode) ---

    // 4. 关键信息高亮 (Key-Value)
    // 检测格式: "**核心困境** : 内容..." 或 "核心困境 : 内容..."
    if (cleanText.includes('：') || cleanText.includes(':')) {
        // 排除掉短的（像对话）和长的（像普通句子）
        const kvMatch = cleanText.match(PATTERNS.KEY_VALUE);
        if (kvMatch) {
            const [_, key, val] = kvMatch;

            // 如果是策划书里的 Key (通常比较短)
            const isLikelyKey = key.length < 20 && !key.includes('http') && !key.includes('//');

            if (isLikelyKey) {
                // 尝试检测原 children 是否包含 strong 标签
                // 这是一个增强体验：如果 key 是 bold 的，我们给它特殊颜色

                return (
                    <p className={`mb-2 last:mb-0 ${className || ''}`}>
                        <span className="text-primary/90 font-semibold">{key}：</span>
                        <span className="text-text-secondary">{val}</span>
                    </p>
                );
            }
        }
    }

    // 6. 独立短标题 (Standalone Short Bold Lines)
    // 很多时候 Prompt 会输出 **标题** 然后换行。
    // 我们检测：纯文本较短 (<20字)，且 children 主要是 Strong/B 标签
    // 简易判断：如果 cleanText 很短，且没有标点符号结尾
    if (cleanText.length > 0 && cleanText.length < 20 && !/[。.,，!！]$/.test(cleanText)) {
        // 进一步检查 children 是否是 strong (需要遍历，稍微复杂)
        // 这里做一个宽松假设：只要是短文本且没标点，就当作小标题处理，给个颜色
        // 为了避免误伤普通短句，我们只对看起来像标题的（比如不含空格，或者全是中文）做处理
        // 也可以配合父级检测，但这里做不到。

        // 策略：如果它被 ** 包裹，ReactMarkdown 会传入 strong 标签。
        // 我们可以粗略判断：如果文本没标点，加粗一下颜色
        return (
            <p className={`mb-2 mt-4 font-bold text-primary/80 ${className || ''}`}>
                {children}
            </p>
        );
    }

    // 5. 默认渲染
    // 对普通段落，稍微调整行高和颜色，使其更易读
    return (
        <p className={`mb-3 last:mb-0 text-gray-300 leading-relaxed ${className || ''}`}>
            {children}
        </p>
    );
};
