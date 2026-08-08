/**
 * CodePanel：代码 / 差异 surface 渲染组件
 *
 * - 展示文件路径与内容
 * - 支持简单的语法高亮（无外部高亮库依赖）
 * - 支持 diff 视图：高亮 before / after 差异
 * - 支持保存修改（调用 window.fs.writeFile）
 * - 支持复制内容
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Copy, Save } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'
import type { CodeSurface, DiffSurface } from '../../laap/types'

export interface CodePanelProps {
  surface: CodeSurface | DiffSurface
}

type DiffEntry =
  | { type: 'same'; before: string; after: string }
  | { type: 'del'; before: string }
  | { type: 'add'; after: string }
  | { type: 'change'; before: string; after: string }

const KEYWORDS = new Set([
  'function',
  'const',
  'let',
  'var',
  'return',
  'if',
  'else',
  'for',
  'while',
  'do',
  'switch',
  'case',
  'break',
  'continue',
  'default',
  'try',
  'catch',
  'finally',
  'throw',
  'new',
  'typeof',
  'instanceof',
  'in',
  'of',
  'async',
  'await',
  'import',
  'export',
  'from',
  'as',
  'class',
  'interface',
  'type',
  'extends',
  'implements',
  'enum',
  'namespace',
  'module',
  'declare',
  'abstract',
  'public',
  'private',
  'protected',
  'readonly',
  'static',
  'get',
  'set',
  'yield',
  'void',
  'never',
  'any',
  'unknown',
  'string',
  'number',
  'boolean',
  'undefined',
  'null',
  'true',
  'false',
  'this',
  'super',
])

const TOKEN_PATTERN =
  /\/\/.*$|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\b(function|const|let|var|return|if|else|for|while|switch|case|break|continue|default|try|catch|finally|throw|new|typeof|instanceof|in|of|async|await|import|export|from|as|class|interface|type|extends|implements|enum|namespace|module|declare|abstract|public|private|protected|readonly|static|get|set|yield|void|never|any|unknown|string|number|boolean|undefined|null|true|false|this|super)\b|\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b|\b[a-zA-Z_$][\w$]*\b(?=\s*\()/g

function tokenizeLine(line: string): Array<{ text: string; className?: string }> {
  const tokens: Array<{ text: string; className?: string }> = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = TOKEN_PATTERN.exec(line)) !== null) {
    if (match.index > lastIndex) {
      tokens.push({ text: line.slice(lastIndex, match.index) })
    }

    const text = match[0]
    let className: string | undefined

    if (text.startsWith('//') || text.startsWith('/*')) {
      className = 'text-white/40 italic'
    } else if (text.startsWith('"') || text.startsWith("'") || text.startsWith('`')) {
      className = 'text-emerald-300/90'
    } else if (/^\d/.test(text)) {
      className = 'text-amber-300/90'
    } else if (KEYWORDS.has(text)) {
      className = 'text-sky-300/90 font-medium'
    } else {
      // function call
      className = 'text-yellow-200/90'
    }

    tokens.push({ text, className })
    lastIndex = TOKEN_PATTERN.lastIndex
  }

  if (lastIndex < line.length) {
    tokens.push({ text: line.slice(lastIndex) })
  }

  return tokens
}

function HighlightedLine({ line }: { line: string }) {
  return (
    <>
      {tokenizeLine(line).map((token, idx) =>
        token.className ? (
          <span key={idx} className={token.className}>
            {token.text}
          </span>
        ) : (
          <span key={idx}>{token.text}</span>
        ),
      )}
    </>
  )
}

function computeLineDiff(before: string, after: string): DiffEntry[] {
  const beforeLines = before.split(/\r?\n/)
  const afterLines = after.split(/\r?\n/)
  const result: DiffEntry[] = []

  let i = 0
  let j = 0

  while (i < beforeLines.length && j < afterLines.length) {
    if (beforeLines[i] === afterLines[j]) {
      result.push({ type: 'same', before: beforeLines[i], after: afterLines[j] })
      i++
      j++
      continue
    }

    let nextInAfter = -1
    for (let k = j + 1; k < afterLines.length; k++) {
      if (afterLines[k] === beforeLines[i]) {
        nextInAfter = k
        break
      }
    }

    let nextInBefore = -1
    for (let k = i + 1; k < beforeLines.length; k++) {
      if (beforeLines[k] === afterLines[j]) {
        nextInBefore = k
        break
      }
    }

    if (nextInAfter === -1 && nextInBefore === -1) {
      result.push({ type: 'change', before: beforeLines[i], after: afterLines[j] })
      i++
      j++
    } else if (nextInAfter !== -1 && (nextInBefore === -1 || nextInAfter - j <= nextInBefore - i)) {
      for (let k = j; k < nextInAfter; k++) {
        result.push({ type: 'add', after: afterLines[k] })
      }
      j = nextInAfter
    } else {
      for (let k = i; k < nextInBefore; k++) {
        result.push({ type: 'del', before: beforeLines[k] })
      }
      i = nextInBefore
    }
  }

  while (i < beforeLines.length) {
    result.push({ type: 'del', before: beforeLines[i++] })
  }
  while (j < afterLines.length) {
    result.push({ type: 'add', after: afterLines[j++] })
  }

  return result
}

export function CodePanel({ surface }: CodePanelProps) {
  const isDiff = surface.kind === 'diff'
  const editable = !isDiff && surface.editable !== false

  const initialContent = isDiff ? surface.after : surface.content
  const [value, setValue] = useState(initialContent)
  const [saving, setSaving] = useState(false)
  const [hint, setHint] = useState('')

  useEffect(() => {
    setValue(isDiff ? surface.after : surface.content)
  }, [isDiff, isDiff ? surface.after : surface.content, surface])

  const diffEntries = useMemo(() => {
    if (!isDiff) return null
    return computeLineDiff(surface.before, surface.after)
  }, [isDiff, surface])

  const showHint = useCallback((message: string) => {
    setHint(message)
    setTimeout(() => setHint(''), 2000)
  }, [])

  const copyContent = useCallback(async () => {
    const text = isDiff ? surface.after : value
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(text)
      } else {
        const textarea = document.createElement('textarea')
        textarea.value = text
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
      }
      showHint('已复制')
    } catch {
      showHint('复制失败')
    }
  }, [isDiff, surface, value, showHint])

  const saveContent = useCallback(async () => {
    if (isDiff) return
    if (!window.fs?.writeFile) {
      showHint('文件 API 不可用')
      return
    }
    setSaving(true)
    try {
      const result = await window.fs.writeFile(surface.filePath, value)
      showHint(result.success ? '已保存' : result.error || '保存失败')
    } finally {
      setSaving(false)
    }
  }, [isDiff, surface.filePath, value, showHint])

  return (
    <GlassPanel
      className="flex flex-col h-full max-h-[420px]"
      intensity="sm"
      radius="var(--laap-radius-md)"
    >
      <div className="flex items-center justify-between gap-3 px-3 py-2 border-b border-white/[0.08]">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.08] text-white/50 font-mono uppercase">
            {isDiff ? 'diff' : 'code'}
          </span>
          <span
            className="text-xs text-white/70 truncate font-mono"
            title={surface.filePath}
          >
            {surface.filePath}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {hint && <span className="text-[10px] text-white/50">{hint}</span>}
          <button
            type="button"
            onClick={copyContent}
            title="复制内容"
            className="p-1 rounded text-white/50 hover:text-white/90 hover:bg-white/10 transition-colors"
          >
            <Copy size={14} />
          </button>
          {!isDiff && (
            <button
              type="button"
              onClick={saveContent}
              disabled={saving}
              title="保存修改"
              className="p-1 rounded text-white/50 hover:text-white/90 hover:bg-white/10 transition-colors disabled:opacity-40"
            >
              <Save size={14} />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-auto p-3 font-mono text-xs leading-5">
        {isDiff ? (
          <table className="w-full table-fixed border-collapse">
            <tbody>
              {(() => {
                let oldLine = 0
                let newLine = 0
                return diffEntries?.map((entry, idx) => {
                  let oldNum: React.ReactNode = null
                  let newNum: React.ReactNode = null
                  let content: React.ReactNode
                  let rowClass = ''

                  if (entry.type === 'same') {
                    oldLine++
                    newLine++
                    oldNum = oldLine
                    newNum = newLine
                    content = <HighlightedLine line={entry.before} />
                  } else if (entry.type === 'del') {
                    oldLine++
                    oldNum = oldLine
                    rowClass = 'bg-red-500/10'
                    content = <HighlightedLine line={entry.before} />
                  } else if (entry.type === 'add') {
                    newLine++
                    newNum = newLine
                    rowClass = 'bg-emerald-500/10'
                    content = <HighlightedLine line={entry.after} />
                  } else {
                    oldLine++
                    newLine++
                    oldNum = oldLine
                    newNum = newLine
                    rowClass = 'bg-amber-500/10'
                    content = <HighlightedLine line={entry.after} />
                  }

                  return (
                    <tr key={idx} className={rowClass}>
                      <td className="w-10 text-right text-white/30 select-none px-2 py-0.5 border-r border-white/[0.06]">
                        {oldNum}
                      </td>
                      <td className="px-2 py-0.5 text-white/80 whitespace-pre overflow-hidden">
                        {entry.type === 'change' ? (
                          <>
                            <span className="line-through decoration-red-400 text-white/50">
                              <HighlightedLine line={entry.before} />
                            </span>
                            <span className="mx-1 text-white/30">→</span>
                            <HighlightedLine line={entry.after} />
                          </>
                        ) : (
                          content
                        )}
                      </td>
                      <td className="w-10 text-right text-white/30 select-none px-2 py-0.5 border-l border-r border-white/[0.06]">
                        {newNum}
                      </td>
                    </tr>
                  )
                })
              })()}
            </tbody>
          </table>
        ) : editable ? (
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-full h-full min-h-[240px] bg-transparent text-white/85 resize-none focus:outline-none whitespace-pre font-mono text-xs leading-5"
            spellCheck={false}
          />
        ) : (
          <pre className="whitespace-pre-wrap text-white/85">
            {value.split(/\r?\n/).map((line, idx) => (
              <div key={idx} className="px-2">
                <HighlightedLine line={line} />
              </div>
            ))}
          </pre>
        )}
      </div>
    </GlassPanel>
  )
}
