/**
 * video_pipeline/animations/entrance.tsx — GSAP 风格入场动效 (Remotion 原生)
 * ======================================================================
 * 用 Remotion 的 spring/interpolate 实现 GSAP 级别的动效:
 *   - stagger-fade-up: 级联上浮
 *   - fade-slide-up:  平滑淡入上移
 *   - scale-stagger:  缩放级联
 *   - split-reveal:   逐字揭示
 *   - glow-in:        光晕淡入
 *
 * 用法:
 *   import { useEntrance, EntranceStyle } from "./animations/entrance";
 *   const { opacity, translateY, scale } = useEntrance("stagger-fade-up", props);
 */

import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export type EntranceStyle =
  | "stagger-fade-up"
  | "fade-slide-up"
  | "scale-stagger"
  | "split-reveal"
  | "glow-in"
  | "none";

export interface EntranceProps {
  enableAnimations: boolean;
  animDuration?: number;
}

/**
 * 通用入场动画 hook — 根据风格返回 { opacity, translateY, translateX, scale, rotation }
 * 用法: const { opacity, translateY } = useEntrance("stagger-fade-up", props, delay);
 */
export function useEntrance(
  style: EntranceStyle,
  props: { enableAnimations: boolean },
  delay: number = 0,
  durationOverride?: number,
) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = durationOverride ?? 30; // 默认 1 秒 @ 30fps

  if (!props.enableAnimations || style === "none") {
    return { opacity: 1, translateY: 0, translateX: 0, scale: 1, rotation: 0 };
  }

  const progress = spring({
    frame: frame - delay,
    fps,
    config: { damping: style === "scale-stagger" ? 200 : 120, stiffness: 80 },
    durationInFrames: dur,
  });

  switch (style) {
    case "stagger-fade-up":
      return {
        opacity: interpolate(progress, [0, 1], [0, 1]),
        translateY: interpolate(progress, [0, 1], [60, 0]),
        translateX: 0,
        scale: interpolate(progress, [0, 1], [0.95, 1]),
        rotation: 0,
      };
    case "fade-slide-up":
      return {
        opacity: interpolate(progress, [0, 1], [0, 1]),
        translateY: interpolate(progress, [0, 1], [40, 0]),
        translateX: 0,
        scale: 1,
        rotation: 0,
      };
    case "scale-stagger":
      return {
        opacity: interpolate(progress, [0, 1], [0, 1]),
        translateY: 0,
        translateX: 0,
        scale: interpolate(progress, [0, 1], [0.8, 1]),
        rotation: 0,
      };
    case "split-reveal":
      return {
        opacity: interpolate(progress, [0, 1], [0, 1]),
        translateY: interpolate(progress, [0, 1], [30, 0]),
        translateX: 0,
        scale: 1,
        rotation: 0,
      };
    case "glow-in":
      return {
        opacity: interpolate(progress, [0, 1], [0, 1]),
        translateY: 0,
        translateX: 0,
        scale: interpolate(progress, [0, 1], [0.95, 1]),
        rotation: 0,
      };
    default:
      return { opacity: 1, translateY: 0, translateX: 0, scale: 1, rotation: 0 };
  }
}

// ── 文字拆解动画 (SplitText 等效) ──

export const SplitText: React.FC<{
  text: string;
  style?: React.CSSProperties;
  delay?: number;
  staggerFrames?: number;
}> = ({ text, style, delay = 0, staggerFrames = 3 }) => {
  const frame = useCurrentFrame();
  const chars = [...text];

  return (
    <span style={{ display: "inline-block", ...style }}>
      {chars.map((ch, i) => {
        const charFrame = frame - delay - i * staggerFrames;
        const opacity = Math.min(1, Math.max(0, charFrame / 15));
        const y = Math.max(0, 30 - charFrame * 2);
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              opacity,
              transform: `translateY(${y}px)`,
              transition: "none",
              whiteSpace: ch === " " ? "pre" : undefined,
            }}
          >
            {ch === " " ? "\u00A0" : ch}
          </span>
        );
      })}
    </span>
  );
};

// ── 逐步揭示动画 (Stagger children) ──

export const StaggerContainer: React.FC<{
  children: React.ReactNode[];
  containerStyle?: React.CSSProperties;
  itemStyle?: React.CSSProperties;
  delay?: number;
  staggerFrames?: number;
  entrance?: EntranceStyle;
  enabled?: boolean;
}> = ({
  children,
  containerStyle,
  itemStyle,
  delay = 0,
  staggerFrames = 6,
  entrance = "fade-slide-up",
  enabled = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, ...containerStyle }}>
      {React.Children.map(children, (child, i) => {
        const itemFrame = frame - delay - i * staggerFrames;
        const progress = spring({
          frame: itemFrame,
          fps,
          config: { damping: 120 },
          durationInFrames: 25,
        });
        const show = enabled ? Math.min(1, Math.max(0, progress)) : 1;
        return (
          <div
            key={i}
            style={{
              opacity: show,
              transform: `translateY(${enabled ? interpolate(show, [0, 1], [30, 0]) : 0}px)`,
              ...itemStyle,
            }}
          >
            {child}
          </div>
        );
      })}
    </div>
  );
};

// ── 数字滚动动画 (计数器) ──

export function useCounter(
  target: number,
  delay: number = 0,
  durationFrames: number = 40,
  easing: "bouncy" | "smooth" = "bouncy",
) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (target <= 0) return 0;

  const progress = spring({
    frame: frame - delay,
    fps,
    config: { damping: easing === "bouncy" ? 200 : 300 },
    durationInFrames: durationFrames,
  });

  return Math.round(interpolate(progress, [0, 1], [0, target]));
}

// ── 粒子背景 (Three.js 静态渲染等效) ──

export const ParticleBackground: React.FC<{
  color?: string;
  count?: number;
  opacity?: number;
}> = ({ color = "#7c7cff", count = 60, opacity = 0.15 }) => {
  const frame = useCurrentFrame();
  const particles = React.useMemo(() => {
    const p = [];
    for (let i = 0; i < count; i++) {
      p.push({
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: 1 + Math.random() * 3,
        speed: 0.2 + Math.random() * 0.5,
        delay: Math.random() * 100,
      });
    }
    return p;
  }, [count]);

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>
      {particles.map((p, i) => {
        const yOffset = Math.sin((frame + p.delay) * 0.02 * p.speed) * 8;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${p.x}%`,
              top: `${p.y + yOffset}%`,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: color,
              opacity,
            }}
          />
        );
      })}
    </div>
  );
};