import { useState } from 'react';
import { 
  X, 
  Users, 
  Image as ImageIcon, 
  Database, 
  Settings, 
  CreditCard,
  BarChart3,
  FolderOpen
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAppStore } from '@/hooks/useStore';

interface BackstageModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'overview' | 'projects' | 'assets' | 'members' | 'billing' | 'settings';

export function BackstageModal({ isOpen, onClose }: BackstageModalProps) {
  const { user } = useAppStore();
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const tabs = [
    { id: 'overview' as TabType, label: '概览', icon: BarChart3 },
    { id: 'projects' as TabType, label: '项目管理', icon: FolderOpen },
    { id: 'assets' as TabType, label: '视觉资产', icon: ImageIcon },
    { id: 'members' as TabType, label: '成员管理', icon: Users },
    { id: 'billing' as TabType, label: '账单', icon: CreditCard },
    { id: 'settings' as TabType, label: '设置', icon: Settings },
  ];

  const stats = [
    { label: '项目总数', value: 12, icon: FolderOpen },
    { label: '分镜卡片', value: 156, icon: ImageIcon },
    { label: '视觉资产', value: 48, icon: Database },
    { label: '团队成员', value: 3, icon: Users },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* 统计卡片 */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {stats.map((stat) => {
                const Icon = stat.icon;
                return (
                  <div 
                    key={stat.label}
                    className="p-4 rounded-lg border"
                    style={{ 
                      backgroundColor: 'var(--bg-night)',
                      borderColor: 'var(--border)'
                    }}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div 
                        className="w-10 h-10 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: 'rgba(255, 215, 0, 0.1)' }}
                      >
                        <Icon size={20} style={{ color: 'var(--primary)' }} />
                      </div>
                      <span 
                        className="text-2xl font-bold"
                        style={{ color: 'var(--text-primary)' }}
                      >
                        {stat.value}
                      </span>
                    </div>
                    <span 
                      className="text-sm"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {stat.label}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* 最近活动 */}
            <div 
              className="p-4 rounded-lg border"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                borderColor: 'var(--border)'
              }}
            >
              <h3 
                className="text-sm font-medium mb-4"
                style={{ color: 'var(--text-primary)' }}
              >
                最近活动
              </h3>
              <div className="space-y-3">
                {[
                  { action: '创建了项目', target: '灰烬纪元：重生者之息', time: '2小时前' },
                  { action: '生成了分镜', target: 'Scene #12', time: '5小时前' },
                  { action: '更新了剧本', target: '第一集：深井的回响', time: '1天前' },
                  { action: '导出了项目', target: '尘埃尽头：新生代', time: '2天前' },
                ].map((activity, i) => (
                  <div 
                    key={i}
                    className="flex items-center justify-between py-2 border-b last:border-0"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    <div>
                      <span style={{ color: 'var(--text-primary)' }}>
                        {activity.action}
                      </span>
                      <span 
                        className="ml-2"
                        style={{ color: 'var(--primary)' }}
                      >
                        {activity.target}
                      </span>
                    </div>
                    <span 
                      className="text-xs"
                      style={{ color: 'var(--text-tertiary)' }}
                    >
                      {activity.time}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'projects':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 
                className="text-sm font-medium"
                style={{ color: 'var(--text-primary)' }}
              >
                所有项目
              </h3>
              <Button size="sm" className="btn-primary">
                + 新建项目
              </Button>
            </div>
            <div className="space-y-2">
              {[
                { name: '灰烬纪元：重生者之息', type: '电影', updated: '2小时前', cards: 45 },
                { name: '尘埃尽头：新生代', type: '短剧', updated: '1天前', cards: 32 },
                { name: '青竹小轩', type: '动画', updated: '3天前', cards: 28 },
                { name: '赛博朋克2077同人', type: '短片', updated: '1周前', cards: 15 },
              ].map((project, i) => (
                <div 
                  key={i}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-white/5 cursor-pointer transition-colors"
                  style={{ 
                    backgroundColor: 'var(--bg-night)',
                    borderColor: 'var(--border)'
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: 'var(--bg-card)' }}
                    >
                      <FolderOpen size={18} style={{ color: 'var(--primary)' }} />
                    </div>
                    <div>
                      <p style={{ color: 'var(--text-primary)' }}>{project.name}</p>
                      <p 
                        className="text-xs"
                        style={{ color: 'var(--text-tertiary)' }}
                      >
                        {project.type} · {project.cards} 张卡片
                      </p>
                    </div>
                  </div>
                  <span 
                    className="text-xs"
                    style={{ color: 'var(--text-tertiary)' }}
                  >
                    {project.updated}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'assets':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 
                className="text-sm font-medium"
                style={{ color: 'var(--text-primary)' }}
              >
                视觉资产库
              </h3>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" style={{ borderColor: 'var(--border)' }}>
                  导入
                </Button>
                <Button size="sm" className="btn-primary">
                  整理
                </Button>
              </div>
            </div>
            <div 
              className="p-8 rounded-lg border text-center"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                borderColor: 'var(--border)'
              }}
            >
              <ImageIcon size={48} style={{ color: 'var(--text-tertiary)', margin: '0 auto 16px' }} />
              <p style={{ color: 'var(--text-secondary)' }}>
                视觉资产库功能开发中
              </p>
              <p 
                className="text-sm mt-2"
                style={{ color: 'var(--text-tertiary)' }}
              >
                支持角色、场景、道具等资产的统一管理
              </p>
            </div>
          </div>
        );

      case 'members':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 
                className="text-sm font-medium"
                style={{ color: 'var(--text-primary)' }}
              >
                团队成员
              </h3>
              <Button size="sm" className="btn-primary">
                + 邀请成员
              </Button>
            </div>
            <div className="space-y-2">
              {[
                { name: 'admin', role: '所有者', email: 'admin@wuli.cool' },
                { name: '设计师小王', role: '编辑', email: 'designer@wuli.cool' },
                { name: '编剧小李', role: '编辑', email: 'writer@wuli.cool' },
              ].map((member, i) => (
                <div 
                  key={i}
                  className="flex items-center justify-between p-3 rounded-lg border"
                  style={{ 
                    backgroundColor: 'var(--bg-night)',
                    borderColor: 'var(--border)'
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-full flex items-center justify-center"
                      style={{ backgroundColor: 'var(--primary)' }}
                    >
                      <span className="text-sm font-medium text-black">
                        {member.name[0].toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p style={{ color: 'var(--text-primary)' }}>{member.name}</p>
                      <p 
                        className="text-xs"
                        style={{ color: 'var(--text-tertiary)' }}
                      >
                        {member.email}
                      </p>
                    </div>
                  </div>
                  <span 
                    className="text-xs px-2 py-1 rounded"
                    style={{ 
                      backgroundColor: 'var(--bg-card)',
                      color: 'var(--text-secondary)'
                    }}
                  >
                    {member.role}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'billing':
        return (
          <div className="space-y-4">
            <div 
              className="p-4 rounded-lg border"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                borderColor: 'var(--border)'
              }}
            >
              <h3 
                className="text-sm font-medium mb-4"
                style={{ color: 'var(--text-primary)' }}
              >
                账户余额
              </h3>
              <div className="flex items-baseline gap-2">
                <span 
                  className="text-4xl font-bold"
                  style={{ color: 'var(--primary)' }}
                >
                  {user?.balance.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
                </span>
                <span style={{ color: 'var(--text-secondary)' }}>积分</span>
              </div>
              <div className="flex gap-2 mt-4">
                <Button size="sm" className="btn-primary">
                  充值
                </Button>
                <Button size="sm" variant="outline" style={{ borderColor: 'var(--border)' }}>
                  查看账单
                </Button>
              </div>
            </div>

            <div 
              className="p-4 rounded-lg border"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                borderColor: 'var(--border)'
              }}
            >
              <h3 
                className="text-sm font-medium mb-4"
                style={{ color: 'var(--text-primary)' }}
              >
                消费记录
              </h3>
              <div className="space-y-2">
                {[
                  { action: '生图消费', amount: -50, time: '2小时前' },
                  { action: '充值', amount: 1000, time: '1天前' },
                  { action: '视频生成', amount: -200, time: '3天前' },
                ].map((record, i) => (
                  <div 
                    key={i}
                    className="flex items-center justify-between py-2 border-b last:border-0"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    <div>
                      <span style={{ color: 'var(--text-primary)' }}>
                        {record.action}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span 
                        style={{ 
                          color: record.amount > 0 ? 'var(--status-green)' : 'var(--text-primary)'
                        }}
                      >
                        {record.amount > 0 ? '+' : ''}{record.amount}
                      </span>
                      <span 
                        className="text-xs"
                        style={{ color: 'var(--text-tertiary)' }}
                      >
                        {record.time}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'settings':
        return (
          <div className="space-y-4">
            <div 
              className="p-4 rounded-lg border"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                borderColor: 'var(--border)'
              }}
            >
              <h3 
                className="text-sm font-medium mb-4"
                style={{ color: 'var(--text-primary)' }}
              >
                通用设置
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p style={{ color: 'var(--text-primary)' }}>自动保存</p>
                    <p 
                      className="text-xs"
                      style={{ color: 'var(--text-tertiary)' }}
                    >
                      每30秒自动保存项目
                    </p>
                  </div>
                  <button 
                    className="w-12 h-6 rounded-full relative transition-colors"
                    style={{ backgroundColor: 'var(--primary)' }}
                  >
                    <div 
                      className="w-5 h-5 rounded-full absolute right-0.5 top-0.5 transition-transform"
                      style={{ backgroundColor: '#fff' }}
                    />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p style={{ color: 'var(--text-primary)' }}>生成完成后播放提示音</p>
                    <p 
                      className="text-xs"
                      style={{ color: 'var(--text-tertiary)' }}
                    >
                      AI生成任务完成时播放声音
                    </p>
                  </div>
                  <button 
                    className="w-12 h-6 rounded-full relative transition-colors"
                    style={{ backgroundColor: 'var(--border)' }}
                  >
                    <div 
                      className="w-5 h-5 rounded-full absolute left-0.5 top-0.5 transition-transform"
                      style={{ backgroundColor: '#fff' }}
                    />
                  </button>
                </div>
              </div>
            </div>

            <div 
              className="p-4 rounded-lg border"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                borderColor: 'var(--border)'
              }}
            >
              <h3 
                className="text-sm font-medium mb-4"
                style={{ color: 'var(--text-primary)' }}
              >
                API 设置
              </h3>
              <div className="space-y-3">
                <div>
                  <label 
                    className="text-xs block mb-1"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    OpenAI API Key
                  </label>
                  <input 
                    type="password"
                    placeholder="sk-..."
                    className="w-full input text-sm"
                  />
                </div>
                <div>
                  <label 
                    className="text-xs block mb-1"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    Midjourney API Key
                  </label>
                  <input 
                    type="password"
                    placeholder="输入 API Key"
                    className="w-full input text-sm"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
      onClick={onClose}
    >
      <div 
        className="w-full max-w-5xl max-h-[85vh] rounded-xl overflow-hidden flex"
        style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 左侧导航 */}
        <div 
          className="w-56 flex-shrink-0 border-r overflow-y-auto"
          style={{ borderColor: 'var(--border)' }}
        >
          <div className="p-4">
            <div className="flex items-center gap-3 mb-6">
              <div 
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: 'var(--primary)' }}
              >
                <span className="text-sm font-medium text-black">
                  {user?.name?.[0]?.toUpperCase() || 'A'}
                </span>
              </div>
              <div>
                <p style={{ color: 'var(--text-primary)' }}>{user?.name || 'admin'}</p>
                <p 
                  className="text-xs"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  管理员
                </p>
              </div>
            </div>

            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors
                      ${isActive ? 'bg-yellow-500/10' : 'hover:bg-white/5'}
                    `}
                  >
                    <Icon 
                      size={18} 
                      style={{ color: isActive ? 'var(--primary)' : 'var(--text-secondary)' }}
                    />
                    <span 
                      style={{ 
                        color: isActive ? 'var(--primary)' : 'var(--text-primary)'
                      }}
                    >
                      {tab.label}
                    </span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* 右侧内容 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 头部 */}
          <div 
            className="flex items-center justify-between px-4 py-3 border-b flex-shrink-0"
            style={{ borderColor: 'var(--border)' }}
          >
            <span 
              className="font-semibold"
              style={{ color: 'var(--text-primary)' }}
            >
              {tabs.find(t => t.id === activeTab)?.label}
            </span>
            <button 
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              style={{ color: 'var(--text-secondary)' }}
            >
              <X size={20} />
            </button>
          </div>

          {/* 内容区 */}
          <div className="flex-1 overflow-y-auto p-6">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
}
