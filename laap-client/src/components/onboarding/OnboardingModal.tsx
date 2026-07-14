/**
 * OnboardingModal：首次启动引导
 *
 * 通过 localStorage 标志位控制是否显示，包含欢迎页、后端连接检查、
 * 说明视频播放以及生命体征介绍四个步骤。
 */

import { useState } from 'react'
import { ChevronRight, ChevronLeft, Activity, Zap, Heart } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import { GlassButton } from '../glass/GlassButton'
import { VideoPlayer } from '../media/VideoPlayer'
import { useLaap } from '../../hooks/useLaap'
import { useSettingsStore } from '../../store/settingsStore'

const TOTAL_STEPS = 4

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center justify-center gap-2">
      {Array.from({ length: TOTAL_STEPS }).map((_, index) => (
        <div
          key={index}
          className={`h-1.5 rounded-full transition-all duration-300 ${
            index === current ? 'w-6 bg-laap-accent' : 'w-1.5 bg-white/20'
          }`}
        />
      ))}
    </div>
  )
}

function WelcomeStep() {
  return (
    <div className="flex flex-col items-center text-center gap-5 py-6">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-laap-accent to-laap-secondary flex items-center justify-center shadow-[0_0_40px_rgba(124,124,255,0.25)]">
        <svg
          className="w-11 h-11"
          viewBox="0 0 256 256"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M80 208 V96 C80 72 96 56 128 56 C160 56 176 72 176 96 V208"
            stroke="#050608"
            strokeWidth="22"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path d="M104 132 H152" stroke="#050608" strokeWidth="22" strokeLinecap="round" />
          <path d="M128 132 L128 208" stroke="#050608" strokeWidth="22" strokeLinecap="round" />
          <circle cx="128" cy="132" r="13" fill="#050608" />
        </svg>
      </div>
      <div>
        <h1 className="text-xl font-medium text-white/90 mb-2">LAAP Client</h1>
        <p className="text-sm text-white/60">意识驱动桌面客户端</p>
      </div>
      <p className="text-xs text-white/40 max-w-[280px] leading-relaxed">
        LAAP 将 CognitiveBus、Colony 协作、PSI 循环与情感动力学整合到一个
        持续运行的桌面伴侣中。完成引导后即可开始交互。
      </p>
    </div>
  )
}

function ConnectionStep() {
  const { connectionStatus } = useLaap()
  const labels: Record<string, string> = {
    open: '已连接 CognitiveBus',
    connecting: '正在连接 CognitiveBus...',
    closed: '连接已关闭',
    error: '连接异常',
  }
  const dotClass =
    connectionStatus === 'open'
      ? 'bg-laap-secondary shadow-[0_0_10px_#00f5d4]'
      : connectionStatus === 'error'
        ? 'bg-red-400'
        : 'bg-laap-accent animate-pulse'

  return (
    <div className="flex flex-col items-center text-center gap-5 py-6">
      <div className="w-16 h-16 rounded-full bg-white/[0.05] border border-white/[0.08] flex items-center justify-center">
        <Zap className="w-7 h-7 text-laap-accent" />
      </div>
      <div>
        <h2 className="text-base font-medium text-white/90 mb-1">后端连接检查</h2>
        <p className="text-xs text-white/50">确认与 CognitiveBus 后端的 WebSocket 链路</p>
      </div>
      <div className="flex items-center gap-3 px-4 py-2 rounded-full bg-black/20 border border-white/[0.08]">
        <span className={`w-2 h-2 rounded-full ${dotClass}`} />
        <span className="text-xs text-white/70">{labels[connectionStatus] ?? '未知状态'}</span>
      </div>
      <p className="text-[10px] text-white/40 max-w-[280px]">
        如果状态异常，可在完成引导后通过右上角设置面板修改后端地址。
      </p>
    </div>
  )
}

function VideoStep() {
  return (
    <div className="flex flex-col gap-4 py-2">
      <div className="text-center">
        <h2 className="text-base font-medium text-white/90 mb-1">观看说明视频</h2>
        <p className="text-xs text-white/50">了解 LAAP 的核心交互方式</p>
      </div>
      <div className="rounded-xl overflow-hidden border border-white/[0.08]">
        <VideoPlayer />
      </div>
    </div>
  )
}

function VitalSignsStep() {
  const items = [
    {
      icon: Activity,
      title: '好奇心 / 信任 / 胜任',
      desc: '需求维度反映 LAAP 对信息、协作与能力的动态评估。',
    },
    {
      icon: Heart,
      title: '5D 情感状态',
      desc: '愉悦、唤醒、支配、社交与压力五个维度共同描绘情感动力学。',
    },
    {
      icon: Zap,
      title: 'PSI 循环',
      desc: '感知、选择、整合、学习四个阶段驱动认知节律。',
    },
  ]

  return (
    <div className="flex flex-col gap-4 py-2">
      <div className="text-center">
        <h2 className="text-base font-medium text-white/90 mb-1">生命体征</h2>
        <p className="text-xs text-white/50">左侧边栏实时展示 LAAP 的内部状态</p>
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <GlassPanel
            key={index}
            className="flex items-start gap-3 p-3"
            intensity="sm"
            radius="var(--laap-radius-md)"
          >
            <div className="w-8 h-8 rounded-lg bg-white/[0.05] flex items-center justify-center shrink-0">
              <item.icon className="w-4 h-4 text-laap-accent" />
            </div>
            <div>
              <h3 className="text-xs font-medium text-white/90">{item.title}</h3>
              <p className="text-[10px] text-white/50 mt-0.5 leading-relaxed">{item.desc}</p>
            </div>
          </GlassPanel>
        ))}
      </div>
    </div>
  )
}

export function OnboardingModal() {
  const [step, setStep] = useState(0)
  const completeOnboarding = useSettingsStore((state) => state.completeOnboarding)

  const handleNext = () => {
    if (step < TOTAL_STEPS - 1) {
      setStep((s) => s + 1)
    } else {
      completeOnboarding()
    }
  }

  const handleSkip = () => {
    completeOnboarding()
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <GlassPanel
        className="w-full max-w-lg flex flex-col overflow-hidden"
        radius="var(--laap-radius-lg)"
        intensity="lg"
        liquidGlass
      >
        <div className="px-6 pt-6 pb-2">
          <StepIndicator current={step} />
        </div>

        <div className="px-6 py-4 min-h-[360px]">
          {step === 0 && <WelcomeStep />}
          {step === 1 && <ConnectionStep />}
          {step === 2 && <VideoStep />}
          {step === 3 && <VitalSignsStep />}
        </div>

        <div className="px-6 py-5 border-t border-white/[0.08] flex items-center justify-between">
          <button
            type="button"
            onClick={handleSkip}
            className="text-xs text-white/50 hover:text-white/80 transition-colors"
          >
            跳过引导
          </button>
          <div className="flex items-center gap-2">
            {step > 0 && (
              <GlassButton
                type="button"
                onClick={() => setStep((s) => s - 1)}
                className="px-4 py-2 text-xs"
              >
                <ChevronLeft className="w-3.5 h-3.5 mr-1" />
                上一步
              </GlassButton>
            )}
            <GlassButton
              type="button"
              onClick={handleNext}
              className="px-4 py-2 text-xs bg-laap-accent/20"
            >
              {step === TOTAL_STEPS - 1 ? '完成' : '下一步'}
              {step < TOTAL_STEPS - 1 && <ChevronRight className="w-3.5 h-3.5 ml-1" />}
            </GlassButton>
          </div>
        </div>
      </GlassPanel>
    </div>
  )
}
