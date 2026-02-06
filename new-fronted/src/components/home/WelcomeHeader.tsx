import { useEffect, useState } from 'react';
import { useAppStore } from '@/hooks/useStore';

export function WelcomeHeader() {
  const { user } = useAppStore();
  const [greeting, setGreeting] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const hour = currentTime.getHours();
    let greetingText = '';
    
    if (hour >= 5 && hour < 12) {
      greetingText = '早上好';
    } else if (hour >= 12 && hour < 18) {
      greetingText = '下午好';
    } else {
      greetingText = '晚上好';
    }
    
    setGreeting(`${greetingText}, ${user?.name || 'admin'}.`);
  }, [currentTime, user]);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="text-center mb-6 sm:mb-8 px-2">
      <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-1 sm:mb-2 text-text-primary">
        {greeting}
      </h1>
      <p className="text-sm sm:text-base md:text-lg text-text-secondary">
        灵感稍纵即逝，抓住它。
      </p>
    </div>
  );
}
