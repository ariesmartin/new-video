import { useState } from 'react';
import { X, Music, Mic, Volume2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface MaterialWorkshopModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MaterialWorkshopModal({ isOpen, onClose }: MaterialWorkshopModalProps) {
  const [activeTab, setActiveTab] = useState('tts');
  
  // TTS状态
  const [voice, setVoice] = useState('Alloy');
  const [ttsText, setTtsText] = useState('');
  
  // 音乐生成状态
  const [musicMode, setMusicMode] = useState<'instrumental' | 'lyrics'>('instrumental');
  const [songTitle, setSongTitle] = useState('');
  const [lyrics, setLyrics] = useState('');
  const [style, setStyle] = useState('Cinematic');

  const voices = ['Alloy', 'Echo', 'Fable', 'Onyx', 'Nova', 'Shimmer'];
  const styles = ['Cinematic', 'Epic', 'Emotional', 'Mysterious', 'Action', 'Romantic'];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent 
        className="max-w-2xl max-h-[90vh] overflow-y-auto"
        style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }}
      >
        <DialogHeader>
          <DialogTitle 
            className="flex items-center justify-between"
            style={{ color: 'var(--text-primary)' }}
          >
            素材工坊
            <button 
              onClick={onClose}
              className="p-1 rounded hover:bg-white/10 transition-colors"
            >
              <X size={20} style={{ color: 'var(--text-secondary)' }} />
            </button>
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList 
            className="w-full grid grid-cols-2 mb-4"
            style={{ backgroundColor: 'var(--bg-night)' }}
          >
            <TabsTrigger 
              value="tts"
              className="flex items-center justify-center gap-2 data-[state=active]:bg-primary data-[state=active]:text-black"
            >
              <Mic size={16} />
              配音室 (TTS)
            </TabsTrigger>
            <TabsTrigger 
              value="music"
              className="flex items-center justify-center gap-2 data-[state=active]:bg-primary data-[state=active]:text-black"
            >
              <Music size={16} />
              音乐生成
            </TabsTrigger>
          </TabsList>

          {/* 配音室 */}
          <TabsContent value="tts" className="flex flex-col m-0 space-y-4">
            <div>
              <label 
                className="text-xs block mb-2"
                style={{ color: 'var(--text-tertiary)' }}
              >
                选择音色(Voice):
              </label>
              <select 
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
                className="w-full input"
              >
                {voices.map((v) => (
                  <option key={v} value={v}>
                    {v} {v === 'Alloy' ? '(中性/通用)' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label 
                className="text-xs block mb-2"
                style={{ color: 'var(--text-tertiary)' }}
              >
                输入要朗读的台词...
              </label>
              <textarea
                value={ttsText}
                onChange={(e) => setTtsText(e.target.value)}
                placeholder="输入台词..."
                className="w-full input resize-none"
                rows={6}
              />
            </div>

            <Button className="w-full btn-primary flex items-center justify-center gap-2">
              <Volume2 size={16} />
              生成语音
            </Button>
          </TabsContent>

          {/* 音乐生成 */}
          <TabsContent value="music" className="flex flex-col m-0 space-y-4">
            {/* 模式选择 */}
            <div>
              <label 
                className="text-xs block mb-2"
                style={{ color: 'var(--text-tertiary)' }}
              >
                模式选择:
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setMusicMode('instrumental')}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm transition-colors ${
                    musicMode === 'instrumental' 
                      ? 'bg-primary text-black' 
                      : 'bg-transparent border'
                  }`}
                  style={{ 
                    borderColor: musicMode === 'instrumental' ? 'transparent' : 'var(--border)',
                    color: musicMode === 'instrumental' ? '#000' : 'var(--text-secondary)'
                  }}
                >
                  纯音乐(Instrumental)
                </button>
                <button
                  onClick={() => setMusicMode('lyrics')}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm transition-colors ${
                    musicMode === 'lyrics' 
                      ? 'bg-primary text-black' 
                      : 'bg-transparent border'
                  }`}
                  style={{ 
                    borderColor: musicMode === 'lyrics' ? 'transparent' : 'var(--border)',
                    color: musicMode === 'lyrics' ? '#000' : 'var(--text-secondary)'
                  }}
                >
                  带歌词
                </button>
              </div>
            </div>

            {/* 歌曲标题 */}
            <div>
              <label 
                className="text-xs block mb-2"
                style={{ color: 'var(--text-tertiary)' }}
              >
                歌曲标题:
              </label>
              <input
                type="text"
                value={songTitle}
                onChange={(e) => setSongTitle(e.target.value)}
                placeholder="无标题"
                className="w-full input"
              />
            </div>

            {/* 歌词 */}
            {musicMode === 'lyrics' && (
              <div>
                <label 
                  className="text-xs block mb-2"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  歌词(Lyrics):
                </label>
                <textarea
                  value={lyrics}
                  onChange={(e) => setLyrics(e.target.value)}
                  placeholder="[Intro]&#10;此处输入歌词...&#10;&#10;[Chorus]&#10;此处输入副歌..."
                  className="w-full input resize-none"
                  rows={6}
                />
              </div>
            )}

            {/* 风格流派 */}
            <div>
              <label 
                className="text-xs block mb-2"
                style={{ color: 'var(--text-tertiary)' }}
              >
                风格流派(Style Tags):
              </label>
              <select 
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="w-full input"
              >
                {styles.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <Button className="w-full btn-primary flex items-center justify-center gap-2">
              <Music size={16} />
              生成音乐 (Suno V3)
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
