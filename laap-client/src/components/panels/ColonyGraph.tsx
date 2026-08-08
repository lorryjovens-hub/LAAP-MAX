/**
 * ColonyGraph：SVG 协作图。
 *
 * 使用固定网格布局摆放节点，消息流用带箭头的动画虚线边表示。
 * 边的 stroke-dashoffset 动画模拟流动效果。
 */

import { useMemo } from 'react'
import type { Agent, ColonyEdge, ColonyMessage } from '../../laap/types'

export interface ColonyGraphProps {
  agents: Agent[]
  edges: ColonyEdge[]
  messages: ColonyMessage[]
}

const statusFill: Record<Agent['status'], string> = {
  online: '#00f5d4',
  busy: '#f7b801',
  offline: '#9ca3af',
}

/**
 * 根据索引计算固定网格位置，避免每帧重算导致抖动
 */
function computeNodePosition(index: number, total: number): { x: number; y: number } {
  const cols = Math.ceil(Math.sqrt(total))
  const cellW = 100 / Math.max(1, cols)
  const cellH = 100 / Math.max(1, Math.ceil(total / cols))
  const row = Math.floor(index / cols)
  const col = index % cols
  return {
    x: cellW * col + cellW * 0.5,
    y: cellH * row + cellH * 0.5,
  }
}

/**
 * 计算箭头路径与角度
 */
function buildArrow(from: { x: number; y: number }, to: { x: number; y: number }): {
  d: string
  angle: number
} {
  const dx = to.x - from.x
  const dy = to.y - from.y
  const angle = Math.atan2(dy, dx) * (180 / Math.PI)
  const len = Math.sqrt(dx * dx + dy * dy)
  const r = 6 // 节点半径
  const ratio = len > r * 2 ? (len - r) / len : 0.85
  const endX = from.x + dx * ratio
  const endY = from.y + dy * ratio
  return {
    d: `M ${from.x} ${from.y} L ${endX} ${endY}`,
    angle,
  }
}

export function ColonyGraph({ agents, edges, messages }: ColonyGraphProps) {
  const nodes = useMemo(() => {
    return agents.map((agent, index) => ({
      ...agent,
      ...computeNodePosition(index, agents.length),
    }))
  }, [agents])

  const nodeMap = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>()
    nodes.forEach((n) => map.set(n.id, { x: n.x, y: n.y }))
    return map
  }, [nodes])

  const renderedEdges = useMemo(() => {
    return edges
      .map((edge) => {
        const from = nodeMap.get(edge.from)
        const to = nodeMap.get(edge.to)
        if (!from || !to) return null
        const { d, angle } = buildArrow(from, to)
        return { ...edge, d, angle, from, to }
      })
      .filter(Boolean) as Array<ColonyEdge & { d: string; angle: number; from: { x: number; y: number }; to: { x: number; y: number } }>
  }, [edges, nodeMap])

  const messageLookup = useMemo(() => {
    const map = new Map<string, ColonyMessage>()
    messages.forEach((m) => {
      const key = `${m.from}-${m.to}`
      map.set(key, m)
    })
    return map
  }, [messages])

  return (
    <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
      <defs>
        <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 L1.5,3 Z" fill="rgba(255,255,255,0.35)" />
        </marker>
      </defs>

      {/* 边 */}
      {renderedEdges.map((edge) => (
        <g key={edge.id}>
          <path
            d={edge.d}
            fill="none"
            stroke="rgba(255,255,255,0.12)"
            strokeWidth="0.6"
            markerEnd="url(#arrowhead)"
          />
          <path
            d={edge.d}
            fill="none"
            stroke="rgba(124,124,255,0.55)"
            strokeWidth="0.5"
            strokeDasharray="6 4"
            className="colony-edge-flow"
            style={{ animationDuration: `${3 + (edge.intensity ?? 0.5) * 2}s` }}
          />
          {messageLookup.get(`${edge.from}-${edge.to}`) && (
            <text
              x={(edge.from.x + edge.to.x) / 2}
              y={(edge.from.y + edge.to.y) / 2 - 2}
              fill="rgba(255,255,255,0.5)"
              fontSize="3"
              textAnchor="middle"
            >
              {messageLookup.get(`${edge.from}-${edge.to}`)?.summary.slice(0, 12)}
            </text>
          )}
        </g>
      ))}

      {/* 节点 */}
      {nodes.map((node) => (
        <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
          <circle r="5" fill="rgba(0,0,0,0.3)" stroke={statusFill[node.status]} strokeWidth="1" />
          <circle r="2.5" fill={statusFill[node.status]} opacity="0.6">
            <animate attributeName="r" values="2.5;4;2.5" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.6;0;0.6" dur="3s" repeatCount="indefinite" />
          </circle>
          <text y="8.5" fill="rgba(255,255,255,0.75)" fontSize="3" textAnchor="middle">
            {node.name}
          </text>
        </g>
      ))}
    </svg>
  )
}
