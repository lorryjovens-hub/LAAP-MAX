import React, { useMemo } from 'react'
import { marked } from 'marked'

interface Props {
  content: string
  className?: string
}

const Markdown: React.FC<Props> = ({ content, className }) => {
  const html = useMemo(() => {
    try {
      const result = marked.parse(content, { breaks: true, gfm: true })
      return typeof result === 'string' ? result : ''
    } catch {
      return content
    }
  }, [content])

  const styles: Record<string, React.CSSProperties> = {
    container: {
      lineHeight: 1.6,
      fontSize: 14,
      wordBreak: 'break-word',
    },
    codeBlock: {
      backgroundColor: 'rgba(0,0,0,0.3)',
      borderRadius: 6,
      padding: '12px 16px',
      margin: '8px 0',
      overflowX: 'auto',
      fontFamily: "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
      fontSize: 13,
      border: '1px solid var(--border)',
    },
    inlineCode: {
      backgroundColor: 'rgba(0,212,170,0.1)',
      color: '#00d4aa',
      padding: '2px 6px',
      borderRadius: 4,
      fontFamily: "'Fira Code', 'Consolas', monospace",
      fontSize: 13,
    },
    table: {
      borderCollapse: 'collapse' as const,
      width: '100%',
      margin: '8px 0',
      fontSize: 13,
    },
    th: {
      border: '1px solid var(--border)',
      padding: '8px 12px',
      textAlign: 'left' as const,
      backgroundColor: 'var(--bg-elevated)',
      fontWeight: 600,
    },
    td: {
      border: '1px solid var(--border)',
      padding: '8px 12px',
    },
    blockquote: {
      borderLeft: '3px solid var(--accent)',
      padding: '8px 16px',
      margin: '8px 0',
      backgroundColor: 'var(--accent-dim)',
      borderRadius: '0 6px 6px 0',
      color: 'var(--text-secondary)',
    },
    link: {
      color: 'var(--accent)',
      textDecoration: 'none',
    },
  }

  return (
    <div
      className={className}
      style={styles.container}
      dangerouslySetInnerHTML={{ __html: html }}
      onMouseOver={(e) => {
        const target = e.target as HTMLElement
        // Add inline styles to rendered elements
        if (target.tagName === 'A') {
          target.style.color = styles.link.color as string
          target.style.textDecoration = 'none'
          target.addEventListener('mouseenter', () => {
            target.style.textDecoration = 'underline'
          })
          target.addEventListener('mouseleave', () => {
            target.style.textDecoration = 'none'
          })
        }
        if (target.tagName === 'CODE' && !target.closest('pre')) {
          Object.assign(target.style, styles.inlineCode)
        }
        if (target.tagName === 'PRE') {
          Object.assign(target.style, styles.codeBlock)
        }
        if (target.tagName === 'BLOCKQUOTE') {
          Object.assign(target.style, styles.blockquote)
        }
        if (target.tagName === 'TH') {
          Object.assign(target.style, styles.th)
        }
        if (target.tagName === 'TD') {
          Object.assign(target.style, styles.td)
        }
        if (target.tagName === 'TABLE') {
          Object.assign(target.style, styles.table)
        }
        if (target.tagName === 'IMG') {
          target.style.maxWidth = '100%'
          target.style.borderRadius = '8px'
          target.style.margin = '8px 0'
        }
      }}
    />
  )
}

export default Markdown
