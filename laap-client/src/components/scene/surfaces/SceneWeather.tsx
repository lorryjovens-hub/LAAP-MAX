/**
 * SceneWeather：weather 类型 surface
 *
 * 根据天气描述显示图标、温度与描述。
 */

import { Sun, Cloud, CloudRain, CloudSnow, CloudLightning } from 'lucide-react'
import { GlassPanel } from '../../glass/GlassPanel'
import type { SceneSurface } from '../../../laap/types'

export interface SceneWeatherProps {
  surface: SceneSurface
}

function WeatherIcon({ condition }: { condition?: string }) {
  const text = condition || ''
  if (text.includes('雨')) return <CloudRain className="w-8 h-8 text-laap-status-info" />
  if (text.includes('雪')) return <CloudSnow className="w-8 h-8 text-white/80" />
  if (text.includes('雷')) return <CloudLightning className="w-8 h-8 text-laap-status-warn" />
  if (text.includes('云') || text.includes('阴')) return <Cloud className="w-8 h-8 text-white/70" />
  return <Sun className="w-8 h-8 text-laap-status-warn" />
}

export function SceneWeather({ surface }: SceneWeatherProps) {
  return (
    <GlassPanel className="p-4 flex items-center justify-between" intensity="sm" radius="var(--laap-radius-md)">
      <div>
        <span className="text-[10px] text-white/50">{surface.location || '天气'}</span>
        <div className="text-2xl font-mono text-white/90 mt-1">
          {surface.temperature ?? '--'}°
        </div>
      </div>
      <div className="flex flex-col items-end gap-1">
        <WeatherIcon condition={surface.condition} />
        <div className="text-sm text-white/80">{surface.condition || '未知'}</div>
      </div>
    </GlassPanel>
  )
}
