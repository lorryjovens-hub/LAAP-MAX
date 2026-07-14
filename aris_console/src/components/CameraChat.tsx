'use client';

import { useEffect, useRef, useState } from 'react';
import TerminalCard from './TerminalCard';

export default function CameraChat() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [status, setStatus] = useState<'idle' | 'capturing' | 'thinking' | 'speaking'>('idle');
  const [vlmResponse, setVlmResponse] = useState<string>('');
  const [log, setLog] = useState<string[]>(['[SYS] 摄像头对话初始化...']);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: 640, height: 480, facingMode: 'user' } 
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        addLog('[CAM] 摄像头已连接');
        setStatus('capturing');

        // Start capture loop
        intervalRef.current = setInterval(captureAndAnalyze, 5000);
      } catch (err) {
        addLog(`[ERR] 摄像头失败: ${err}`);
        setStatus('idle');
      }
    }

    startCamera();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  function addLog(msg: string) {
    const now = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    setLog(prev => [...prev.slice(-20), `[${now}] ${msg}`]);
  }

  async function captureAndAnalyze() {
    if (!videoRef.current || !canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = 640;
    canvas.height = 480;
    ctx.drawImage(videoRef.current, 0, 0);
    
    const imageData = canvas.toDataURL('image/jpeg', 0.7);
    setStatus('thinking');
    addLog('[VLM] 发送帧到视觉模型...');

    try {
      const resp = await fetch('/api/vision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setVlmResponse(data.description);
        addLog(`[VLM] ${data.description.slice(0, 50)}...`);
        setStatus('speaking');
        setTimeout(() => setStatus('capturing'), 2000);
      } else {
        // Fallback: show mock response
        const mockResponses = [
          '看到你在屏幕前，光线柔和',
          '摄像头捕捉到房间一角，有家具的轮廓',
          '你在盯着屏幕看，专注的样子',
          '房间里暗着，只有屏幕的光',
        ];
        const mock = mockResponses[Math.floor(Math.random() * mockResponses.length)];
        setVlmResponse(mock);
        addLog(`[VLM:mock] ${mock}`);
        setStatus('speaking');
        setTimeout(() => setStatus('capturing'), 2000);
      }
    } catch {
      addLog('[VLM] 后端未连接，使用模拟模式');
      setStatus('capturing');
    }
  }

  const statusText = {
    idle: '等待中...',
    capturing: '实时监控中',
    thinking: '视觉识别中...',
    speaking: 'Aris 回应中...',
  };

  return (
    <TerminalCard title="CAMERA CHAT" status={status === 'capturing' ? 'green' : 'yellow'}>
      <div className="grid grid-cols-2 gap-4">
        {/* Camera feed */}
        <div className="camera-feed relative">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full rounded"
            style={{ transform: 'scaleX(-1)' }}
          />
          <canvas ref={canvasRef} className="hidden" />
          {/* Corners */}
          <div className="camera-corner" style={{ top: 8, left: 8, borderTop: '2px solid var(--matrix-green-dim)', borderLeft: '2px solid var(--matrix-green-dim)' }} />
          <div className="camera-corner" style={{ top: 8, right: 8, borderTop: '2px solid var(--matrix-green-dim)', borderRight: '2px solid var(--matrix-green-dim)' }} />
          <div className="camera-corner" style={{ bottom: 8, left: 8, borderBottom: '2px solid var(--matrix-green-dim)', borderLeft: '2px solid var(--matrix-green-dim)' }} />
          <div className="camera-corner" style={{ bottom: 8, right: 8, borderBottom: '2px solid var(--matrix-green-dim)', borderRight: '2px solid var(--matrix-green-dim)' }} />
          {/* Status overlay */}
          <div className="absolute top-3 right-3 badge-online bg-[var(--bg-darkest)]">
            {statusText[status]}
          </div>
        </div>

        {/* VLM Response */}
        <div>
          <div className="text-[10px] text-[var(--text-muted)] mb-1 uppercase tracking-wider">
            Aris 的回应
          </div>
          <div className="terminal-card" style={{ minHeight: 200, padding: 12 }}>
            {vlmResponse ? (
              <p className="text-sm text-[var(--matrix-cyan)] cursor-blink leading-relaxed">
                {vlmResponse}
              </p>
            ) : (
              <p className="text-xs text-[var(--text-muted)] italic">
                {'>'} 等待首次视觉识别...
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Log */}
      <div className="mt-3">
        <div className="text-[10px] text-[var(--text-muted)] mb-1 uppercase tracking-wider">
          System Log
        </div>
        <div className="data-stream">
          {log.slice(-8).map((line, i) => (
            <div key={i} className="text-[10px] text-[var(--text-muted)] leading-relaxed">
              {line}
            </div>
          ))}
        </div>
      </div>
    </TerminalCard>
  );
}
