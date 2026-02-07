import { useEffect, useRef } from 'react';

interface UseChatScrollProps {
    messages: any[];
    isStreaming: boolean;
    enabled?: boolean;
}

export function useChatScroll({
    messages,
    isStreaming,
    enabled = true
}: UseChatScrollProps) {
    const scrollRef = useRef<HTMLDivElement>(null);


    // 监听滚动事件，判断用户是否手动向上滚动了
    // 注意：这需要绑定到滚动容器上，但简化起见，我们先假设只做基本的"有新内容就滚到底"
    // 如果要更完美，可以结合 IntersectionObserver 监听底部锚点是否可见

    useEffect(() => {
        if (!enabled || !scrollRef.current) return;

        // 对于流式输出，使用 auto (即刻) 滚动以避免抖动
        // 对于新消息添加，使用 smooth 滚动以提供更好的视觉提示
        const behavior = isStreaming ? 'auto' : 'smooth';

        // 使用 requestAnimationFrame 确保在渲染后执行
        requestAnimationFrame(() => {
            scrollRef.current?.scrollIntoView({
                behavior,
                block: 'end'
            });
        });

    }, [messages, isStreaming, enabled]);

    return scrollRef;
}
