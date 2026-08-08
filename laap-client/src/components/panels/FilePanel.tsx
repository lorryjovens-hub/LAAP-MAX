/**
 * FilePanel — 文件浏览器
 *
 * 文件树 + 内容预览。支持目录展开、文件搜索、代码高亮预览。
 */

import { useEffect, useState, useCallback } from 'react'
import { GlassPanel } from '../glass/GlassPanel'
import {
  Folder, FolderOpen, File, FileCode, FileImage, FileText,
  Search, ChevronRight, RotateCw,
} from 'lucide-react'
import { useAetherSDK } from '../../hooks/useAetherSDK'
import type { FileEntry } from '../../laap/sdk/file'

export interface FilePanelProps {
  className?: string
  rootDir?: string
}

// 根据文件名推断图标
function getFileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase()
  if (!ext || ['md', 'txt', 'json', 'yaml', 'yml', 'toml'].includes(ext)) return <FileText className="w-3.5 h-3.5" />
  if (['ts', 'tsx', 'js', 'jsx', 'py', 'rs', 'go', 'java', 'c', 'cpp', 'h'].includes(ext)) return <FileCode className="w-3.5 h-3.5" />
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'webp'].includes(ext)) return <FileImage className="w-3.5 h-3.5" />
  return <File className="w-3.5 h-3.5" />
}

function FileTreeNode({
  entry,
  depth,
  onSelect,
  selectedPath,
}: {
  entry: FileEntry
  depth: number
  onSelect: (path: string) => void
  selectedPath: string | null
}) {
  const [expanded, setExpanded] = useState(depth < 1)

  const isDir = entry.type === 'dir'
  const isSelected = selectedPath === entry.path

  return (
    <div>
      <button
        type="button"
        onClick={() => {
          if (isDir) setExpanded(!expanded)
          else onSelect(entry.path)
        }}
        className={`w-full flex items-center gap-1.5 px-2 py-1 rounded-md text-xs transition-colors text-left
          ${isSelected ? 'bg-laap-accent/15 text-laap-accent' : 'text-white/70 hover:bg-white/[0.04] hover:text-white/90'}
        `}
        style={{ paddingLeft: `${8 + depth * 14}px` }}
      >
        {isDir ? (
          <>
            <ChevronRight className={`w-3 h-3 text-white/30 transition-transform ${expanded ? 'rotate-90' : ''}`} />
            {expanded ? <FolderOpen className="w-3.5 h-3.5 text-amber-400/70" /> : <Folder className="w-3.5 h-3.5 text-amber-400/50" />}
          </>
        ) : (
          <>
            <span className="w-3" />
            {getFileIcon(entry.name)}
          </>
        )}
        <span className="truncate">{entry.name}</span>
        {isDir && entry.children && (
          <span className="ml-auto text-[9px] text-white/30">{entry.children.length}</span>
        )}
      </button>
      {isDir && expanded && entry.children?.map((child) => (
        <FileTreeNode
          key={child.path}
          entry={child}
          depth={depth + 1}
          onSelect={onSelect}
          selectedPath={selectedPath}
        />
      ))}
    </div>
  )
}

export function FilePanel({ className = '', rootDir = '/home' }: FilePanelProps) {
  const { sdk } = useAetherSDK()
  const [tree, setTree] = useState<FileEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPath, setSelectedPath] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<FileEntry[]>([])

  const loadTree = useCallback(async () => {
    setLoading(true)
    try {
      const entries = await sdk.file.list(rootDir)
      setTree(entries)
    } catch {
      setTree([])
    } finally {
      setLoading(false)
    }
  }, [sdk, rootDir])

  useEffect(() => {
    loadTree()
  }, [loadTree])

  // 选中文件时预览
  useEffect(() => {
    if (!selectedPath) return
    setPreviewLoading(true)
    sdk.file.read(selectedPath).then((content) => {
      setPreview(content ?? '（空文件）')
    }).catch(() => {
      setPreview('（无法读取文件）')
    }).finally(() => setPreviewLoading(false))
  }, [sdk, selectedPath])

  // 搜索
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }
    const timer = setTimeout(async () => {
      try {
        const results = await sdk.file.search(searchQuery, rootDir)
        setSearchResults(results)
      } catch {
        setSearchResults([])
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [sdk, searchQuery, rootDir])

  return (
    <GlassPanel className={`flex flex-col overflow-hidden ${className}`} intensity="sm" radius="var(--laap-radius-md)">
      {/* Header */}
      <div className="shrink-0 px-4 py-3 border-b border-white/[0.08]">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-medium text-white/90 flex items-center gap-2">
            <Folder className="w-4 h-4 text-laap-accent" />
            文件浏览器
          </h2>
          <button type="button" onClick={loadTree}
            className="p-1 rounded-md hover:bg-white/[0.08] text-white/40 hover:text-white/70 transition-colors">
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/40" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索文件..."
            className="w-full h-8 pl-8 pr-3 text-xs bg-white/[0.06] border border-white/[0.10] rounded-lg
                       text-white/85 placeholder:text-white/30 outline-none
                       focus:border-laap-accent/40 focus:bg-white/[0.08] transition-colors"
          />
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* File tree */}
        <div className="w-1/2 min-w-0 overflow-y-auto border-r border-white/[0.06] p-1.5">
          {loading && (
            <div className="flex items-center justify-center py-8"><RotateCw className="w-4 h-4 text-white/40 animate-spin" /></div>
          )}
          {!loading && searchQuery ? (
            searchResults.length === 0 ? (
              <div className="text-center py-8 text-white/30 text-xs">无结果</div>
            ) : (
              searchResults.map((f) => (
                <button
                  key={f.path}
                  type="button"
                  onClick={() => { setSelectedPath(f.path); setSearchQuery('') }}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-colors text-left
                    ${selectedPath === f.path ? 'bg-laap-accent/15 text-laap-accent' : 'text-white/70 hover:bg-white/[0.04]'}
                  `}
                >
                  {getFileIcon(f.name)}
                  <span className="truncate">{f.name}</span>
                  <span className="ml-auto text-[9px] text-white/30">{f.path.split('/').slice(0, -1).pop()}</span>
                </button>
              ))
            )
          ) : !loading ? (
            tree.map((entry) => (
              <FileTreeNode
                key={entry.path}
                entry={entry}
                depth={0}
                onSelect={setSelectedPath}
                selectedPath={selectedPath}
              />
            ))
          ) : null}
        </div>

        {/* Preview */}
        <div className="w-1/2 min-w-0 overflow-y-auto p-3">
          {previewLoading ? (
            <div className="flex items-center justify-center py-8"><RotateCw className="w-4 h-4 text-white/40 animate-spin" /></div>
          ) : selectedPath && preview !== null ? (
            <div>
              <div className="text-[10px] text-white/40 font-mono mb-2 truncate">{selectedPath}</div>
              <pre className="text-[11px] text-white/70 font-mono whitespace-pre-wrap leading-relaxed">{preview.slice(0, 2000)}</pre>
              {preview.length > 2000 && (
                <div className="text-[10px] text-white/30 mt-2">仅显示前 2000 字符</div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-white/30 text-xs gap-2">
              <FileCode className="w-8 h-8 opacity-40" />
              <p>选择文件查看内容</p>
            </div>
          )}
        </div>
      </div>
    </GlassPanel>
  )
}

export default FilePanel
