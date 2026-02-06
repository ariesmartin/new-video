import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Edit2,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Key,
  Globe,
  TestTube,
  Plus,
  X,
  ChevronUp,
} from 'lucide-react';
import type {
  ModelProvider,
  ModelProviderCreate,
  ModelProviderUpdate,
  ProviderType,
  ProtocolType,
  TestResult,
} from '@/types';

interface ProviderCardProps {
  provider?: ModelProvider;
  isNew?: boolean;
  type: ProviderType;
  protocols: { value: ProtocolType; label: string }[];
  onSave: (data: ModelProviderCreate | ModelProviderUpdate) => Promise<void>;
  onCancel: () => void;
  onDelete?: () => Promise<void>;
  onTest: (providerId: string, modelName: string) => Promise<TestResult>;
  onEdit?: () => void;
  isCollapsed?: boolean;
}

export function ProviderCard({
  provider,
  isNew = false,
  type,
  protocols,
  onSave,
  onCancel,
  onDelete,
  onTest,
  onEdit,
  isCollapsed = false,
}: ProviderCardProps) {
  const [isExpanded] = useState(isNew || !isCollapsed);
  const [form, setForm] = useState<ModelProviderCreate>({
    name: provider?.name || '',
    provider_type: type,
    protocol: (provider?.protocol as ProtocolType) || protocols[0]?.value || 'openai',
    base_url: provider?.base_url || '',
    api_key: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [newModelName, setNewModelName] = useState('');
  const [availableModels, setAvailableModels] = useState<string[]>(
    provider?.available_models || []
  );

  const isEditing = !isNew && !!provider;

  const handleSubmit = async () => {
    if (!form.name) return;
    if (isNew && !form.api_key) return;

    setIsSubmitting(true);
    try {
      if (isEditing && provider) {
        const updateData: ModelProviderUpdate = {
          name: form.name,
          base_url: form.base_url,
        };
        if (form.api_key) updateData.api_key = form.api_key;
        await onSave(updateData);
      } else {
        await onSave(form);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTest = async () => {
    if (isNew || !provider) {
      setTestResult({ success: false, error: '请先保存服务商后再测试' });
      return;
    }

    setIsTesting(true);
    setTestResult(null);
    try {
      const testModel = availableModels[0] || 'default';
      const result = await onTest(provider.id, testModel);
      setTestResult(result);
    } finally {
      setIsTesting(false);
    }
  };

  const handleAddModel = () => {
    if (!newModelName.trim()) return;
    if (availableModels.includes(newModelName.trim())) return;
    setAvailableModels([...availableModels, newModelName.trim()]);
    setNewModelName('');
  };

  const handleRemoveModel = (modelName: string) => {
    setAvailableModels(availableModels.filter((m) => m !== modelName));
  };

  if (!isExpanded && provider) {
    return (
      <div
        className="p-4 rounded-lg border border-border bg-elevated cursor-pointer hover:border-primary/50 transition-colors"
        onClick={() => onEdit?.()}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-3 h-3 rounded-full ${
                provider.is_active ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <h3 className="font-medium text-text-primary">{provider.name}</h3>
            <Badge variant="secondary" className="text-xs">
              {provider.protocol}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-secondary">
              {availableModels.length} 个模型
            </span>
            <Button variant="ghost" size="sm" onClick={() => onEdit?.()}>
              <Edit2 size={16} />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-lg border border-border bg-elevated">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-text-primary">
          {isNew ? `添加新${type === 'video' ? '视频' : 'LLM'}服务商` : `编辑 ${provider?.name}`}
        </h3>
        {!isNew && (
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <ChevronUp size={16} />
          </Button>
        )}
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-sm text-text-secondary block mb-1.5">
            名称 *
          </label>
          <Input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="例如：OpenAI GPT-4"
            className="bg-surface"
          />
        </div>

        <div>
          <label className="text-sm text-text-secondary block mb-1.5">
            协议类型 *
          </label>
          <select
            value={form.protocol}
            onChange={(e) =>
              setForm({ ...form, protocol: e.target.value as ProtocolType })
            }
            className="w-full px-3 py-2 rounded-md bg-surface border border-border text-sm text-text-primary"
          >
            {protocols.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm text-text-secondary block mb-1.5">
            Base URL
          </label>
          <div className="flex items-center gap-2">
            <Globe size={16} className="text-text-tertiary" />
            <Input
              value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              placeholder="https://api.openai.com/v1"
              className="flex-1 bg-surface"
            />
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
        >
          {/* 隐藏的 username 字段用于无障碍访问 */}
          <input
            type="text"
            autoComplete="username"
            value={form.name}
            readOnly
            className="sr-only"
            aria-hidden="true"
            tabIndex={-1}
          />
          <label className="text-sm text-text-secondary block mb-1.5">
            API 密钥 {isNew && '*'}
          </label>
          <div className="flex items-center gap-2">
            <Key size={16} className="text-text-tertiary" />
            <Input
              type="password"
              autoComplete={isNew ? "new-password" : "current-password"}
              value={form.api_key}
              onChange={(e) => setForm({ ...form, api_key: e.target.value })}
              placeholder={isNew ? '输入 API 密钥' : '留空表示不修改'}
              className="flex-1 bg-surface"
            />
          </div>
        </form>

        {isEditing && (
          <div>
            <label className="text-sm text-text-secondary block mb-1.5">
              可用模型
            </label>
            <div className="flex gap-2 mb-2">
              <Input
                value={newModelName}
                onChange={(e) => setNewModelName(e.target.value)}
                placeholder="添加模型名称"
                className="flex-1 bg-surface"
                onKeyDown={(e) => e.key === 'Enter' && handleAddModel()}
              />
              <Button onClick={handleAddModel} size="sm" variant="outline">
                <Plus size={16} />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto p-1">
              {availableModels.map((model) => (
                <Badge
                  key={model}
                  variant="secondary"
                  className="flex items-center gap-1"
                >
                  <span className="font-mono text-xs">{model}</span>
                  <button
                    onClick={() => handleRemoveModel(model)}
                    className="hover:text-red-400"
                  >
                    <X size={12} />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        )}

        {testResult && (
          <div
            className={`p-3 rounded-lg flex items-start gap-2 ${
              testResult.success
                ? 'bg-green-500/10 border border-green-500/20'
                : 'bg-red-500/10 border border-red-500/20'
            }`}
          >
            {testResult.success ? (
              <CheckCircle size={18} className="text-green-500 mt-0.5" />
            ) : (
              <AlertTriangle size={18} className="text-red-500 mt-0.5" />
            )}
            <div className="flex-1">
              <p
                className={`text-sm ${
                  testResult.success ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {testResult.success ? '连接测试成功' : '连接测试失败'}
              </p>
              {testResult.response && (
                <p className="text-xs text-text-secondary mt-1">
                  响应: {testResult.response}
                </p>
              )}
              {testResult.error && (
                <p className="text-xs text-red-400/80 mt-1">
                  错误: {testResult.error}
                </p>
              )}
              {testResult.latency_ms && (
                <p className="text-xs text-text-secondary mt-1">
                  延迟: {testResult.latency_ms}ms
                </p>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-4 border-t border-border">
          <div className="flex items-center gap-2">
            {isEditing && onDelete && (
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowDeleteConfirm(true)}
              >
                <Trash2 size={16} className="mr-1" />
                删除
              </Button>
            )}
            {isEditing && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleTest}
                disabled={isTesting}
              >
                {isTesting ? (
                  <Loader2 size={16} className="animate-spin mr-1" />
                ) : (
                  <TestTube size={16} className="mr-1" />
                )}
                测试连接
              </Button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onCancel}>
              取消
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={
                isSubmitting || !form.name || (isNew && !form.api_key)
              }
              size="sm"
            >
              {isSubmitting ? (
                <Loader2 size={16} className="animate-spin mr-1" />
              ) : (
                <CheckCircle size={16} className="mr-1" />
              )}
              {isNew ? '添加' : '保存'}
            </Button>
          </div>
        </div>
      </div>

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface p-6 rounded-lg border border-border max-w-sm">
            <h4 className="font-medium text-text-primary mb-2">确认删除</h4>
            <p className="text-sm text-text-secondary mb-4">
              确定要删除服务商 "{provider?.name}" 吗？此操作不可恢复。
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDeleteConfirm(false)}
              >
                取消
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={async () => {
                  await onDelete?.();
                  setShowDeleteConfirm(false);
                }}
              >
                确认删除
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
