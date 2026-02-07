import {
    Dialog,
    DialogContent,
    DialogTitle,
} from "@/components/ui/dialog";
import { Copy, X, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ScriptRenderer } from './ScriptRenderer';
import { cleanJsonFromContent } from '@/lib/ai-chat-helper';
import { useUIStore } from '@/hooks/useStore';

interface AIReaderDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    content: string;
    title?: string;
}

export function AIReaderDialog({
    open,
    onOpenChange,
    content,
    title = "AI 创作内容"
}: AIReaderDialogProps) {
    const addToast = useUIStore((state) => state.addToast);

    const handleCopy = () => {
        navigator.clipboard.writeText(content).then(() => {
            addToast({ type: 'success', message: '内容已复制到剪贴板' });
        });
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-5xl h-[90vh] flex flex-col p-0 gap-0 bg-background/95 backdrop-blur-xl border-border/50 shadow-2xl rounded-xl overflow-hidden focus:outline-none">

                {/* Header - Minimalist & Functional */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border/40 bg-background/50 backdrop-blur-md shrink-0 z-10">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                            <Sparkles size={16} />
                        </div>
                        <DialogTitle className="text-base font-medium text-text-primary/90">
                            {title}
                        </DialogTitle>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleCopy}
                            className="h-8 px-3 text-text-secondary hover:text-text-primary hover:bg-surface/80 rounded-lg gap-2 transition-all"
                        >
                            <Copy size={14} />
                            <span className="text-xs font-medium">复制全文</span>
                        </Button>
                        <div className="w-px h-4 bg-border/50 mx-1" />
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onOpenChange(false)}
                            className="h-8 w-8 text-text-tertiary hover:text-text-primary hover:bg-surface/80 rounded-full transition-all"
                        >
                            <X size={16} />
                        </Button>
                    </div>
                </div>

                {/* Content - Reader Mode (Native Scroll) */}
                <div className="flex-1 w-full overflow-y-auto bg-background/50 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
                    <div className="max-w-3xl mx-auto px-8 py-12 min-h-full">
                        <div className="prose prose-slate dark:prose-invert max-w-none
              prose-headings:font-semibold prose-headings:tracking-tight prose-headings:text-text-primary
              prose-h1:text-3xl prose-h1:mb-8
              prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-6 prose-h2:pb-2 prose-h2:border-b prose-h2:border-border/40
              prose-h3:text-lg prose-h3:mt-8 prose-h3:mb-4
              prose-p:text-[15px] prose-p:leading-7 prose-p:text-text-secondary prose-p:mb-5
              prose-strong:text-text-primary prose-strong:font-semibold
              prose-ul:my-6 prose-ul:list-disc prose-ul:pl-6
              prose-ol:my-6 prose-ol:list-decimal prose-ol:pl-6
              prose-li:my-2 prose-li:text-text-secondary
              prose-blockquote:border-l-4 prose-blockquote:border-primary/40 prose-blockquote:bg-muted/50 prose-blockquote:py-2 prose-blockquote:px-4 prose-blockquote:my-6 prose-blockquote:rounded-r-lg prose-blockquote:not-italic
              prose-code:text-primary prose-code:bg-primary/5 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:font-mono prose-code:text-sm
              prose-pre:bg-muted/50 prose-pre:border prose-pre:border-border/50 prose-pre:rounded-xl prose-pre:p-4
              hr:my-8 hr:border-border/40
            ">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    p: ScriptRenderer
                                }}
                            >
                                {cleanJsonFromContent(content)}
                            </ReactMarkdown>
                        </div>

                        {/* End of content indicator */}
                        <div className="mt-16 flex justify-center pb-8">
                            <div className="w-1.5 h-1.5 rounded-full bg-border/60" />
                        </div>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
