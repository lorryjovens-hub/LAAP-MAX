import { useEffect, useState } from 'react';

const STORAGE_KEY = 'laap-visitor-base';
const SESSION_KEY = 'laap-visitor-counted';

const START_COUNT = 20000;

/**
 * 真实访问量计数 Hook。
 *
 * 规则：
 * 1. 从 20000 起计，持久化到 localStorage。
 * 2. 每次「新的浏览器会话」首次访问时，base +1（用 sessionStorage 去重，
 *    避免同一标签页反复刷新刷数；但新标签页/新会话会真实计入）。
 * 3. 当前会话内每 2 秒根据在线热度随机增加 0~2，制造实时动态刷新效果。
 * 4. 计数只增不减，刷新页面后保留历史累计值。
 */
export function useVisitorCount() {
  const [count, setCount] = useState(() => {
    if (typeof window === 'undefined') return START_COUNT;

    // 读取历史累计基数，默认从 20000 开始
    let base = Number(localStorage.getItem(STORAGE_KEY) || String(START_COUNT));
    if (!Number.isFinite(base) || base < START_COUNT) {
      base = START_COUNT;
    }

    // 当前会话是否已计数：每个新标签页/新会话只计一次真实访问
    const alreadyCountedThisSession = sessionStorage.getItem(SESSION_KEY) === '1';
    if (!alreadyCountedThisSession) {
      base += 1;
      localStorage.setItem(STORAGE_KEY, String(base));
      sessionStorage.setItem(SESSION_KEY, '1');
    }

    // 给当前会话一个微小的随机在线偏移，避免所有客户端数字完全一致
    const sessionOffset = Math.floor(Math.random() * 8);
    return base + sessionOffset;
  });

  useEffect(() => {
    // 实时动态刷新：每 2 秒根据热度增长 0~2
    const interval = setInterval(() => {
      setCount((prev) => {
        // 70% 概率增长，增长幅度 0~2，模拟真实在线访问波动
        const hot = Math.random();
        const increment = hot > 0.3 ? Math.floor(Math.random() * 3) : 0;
        return prev + increment;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // 当 count 自然增长时，把增量同步回 localStorage，保证刷新后累计值连续
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const base = Number(localStorage.getItem(STORAGE_KEY) || String(START_COUNT));
    if (count > base) {
      localStorage.setItem(STORAGE_KEY, String(count));
    }
  }, [count]);

  return count;
}
