import { useCallback, useEffect, useState } from 'react';
import {
  Play, ThumbsUp, MessageSquare, Eye, Upload, LogIn, LogOut,
  Globe, Box, Gamepad2, Layout, Loader2, Trash2, RefreshCw,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';
import {
  Tabs, TabsList, TabsTrigger, TabsContent,
} from '@/components/ui/tabs';
import {
  communityListWorks, communityGetWork, communityPublish, communityDeleteWork,
  communityLike, communityPlay, communityListComments, communityAddComment,
  communityLogin, communityRegister, communityLogout,
  getCommunityUser, isCommunityLoggedIn, communityWorkUrl,
  type CommunityWork, type CommunityComment, type CommunityUser,
} from '@/lib/community';

const TYPE_META: Record<string, { label: string; icon: typeof Globe; color: string }> = {
  webapp: { label: '网页应用', icon: Layout, color: 'text-laap-cyan' },
  site: { label: '网站', icon: Globe, color: 'text-laap-gold' },
  game: { label: '游戏', icon: Gamepad2, color: 'text-laap-rose' },
};

function fmtDate(s?: string) {
  if (!s) return '';
  const d = new Date(s);
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ── 登录 / 注册弹窗 ────────────────────────────────────
function AuthDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!email || !password) return toast.error('请填写邮箱和密码');
    if (mode === 'register' && !name) return toast.error('请填写昵称');
    setBusy(true);
    try {
      if (mode === 'login') await communityLogin(email, password);
      else await communityRegister(email, password, name);
      toast.success(mode === 'login' ? '登录成功' : '注册成功');
      onOpenChange(false);
      setEmail(''); setPassword(''); setName('');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '操作失败');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>{mode === 'login' ? '登录 LAAP 社区' : '注册 LAAP 社区账号'}</DialogTitle>
          <DialogDescription>
            登录后可发布作品、点赞、评论。账号用于云端公共社区。
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {mode === 'register' && (
            <Input placeholder="昵称" value={name} onChange={(e) => setName(e.target.value)} />
          )}
          <Input type="email" placeholder="邮箱" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input type="password" placeholder="密码" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button className="w-full" onClick={submit} disabled={busy}>
            {busy && <Loader2 className="animate-spin" />}
            {mode === 'login' ? '登录' : '注册'}
          </Button>
          <button
            className="w-full text-center text-[13px] text-laap-text-tertiary hover:text-laap-gold"
            onClick={() => setMode((m) => (m === 'login' ? 'register' : 'login'))}
          >
            {mode === 'login' ? '没有账号？去注册' : '已有账号？去登录'}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── 作品详情 / 游玩弹窗 ────────────────────────────────
function WorkDialog({ work, open, onOpenChange, onChanged }: {
  work: CommunityWork | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onChanged: () => void;
}) {
  const [likes, setLikes] = useState(work?.likes ?? 0);
  const [comments, setComments] = useState<CommunityComment[]>([]);
  const [comment, setComment] = useState('');
  const [busyLike, setBusyLike] = useState(false);
  const [playing, setPlaying] = useState(false);
  const user: CommunityUser | null = getCommunityUser();

  useEffect(() => {
    if (open && work) {
      setLikes(work.likes);
      setPlaying(false);
      communityPlay(work.id);
      communityListComments(work.id).then(setComments).catch(() => {});
    }
  }, [open, work]);

  async function toggleLike() {
    if (!isCommunityLoggedIn()) return toast.error('请先登录');
    if (!work) return;
    setBusyLike(true);
    try {
      const r = await communityLike(work.id);
      setLikes(r.likes);
      toast.success(r.liked ? '已点赞' : '已取消点赞');
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '操作失败');
    } finally {
      setBusyLike(false);
    }
  }

  async function submitComment() {
    if (!isCommunityLoggedIn()) return toast.error('请先登录');
    if (!work || !comment.trim()) return;
    try {
      await communityAddComment(work.id, comment.trim());
      setComment('');
      const list = await communityListComments(work.id);
      setComments(list);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '评论失败');
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[860px] max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            {work?.title}
            {work && <Meta type={work.type} likes={likes} plays={work.plays} createdAt={work.published_at} />}
          </DialogTitle>
          <DialogDescription>{work?.description || '暂无简介'}</DialogDescription>
        </DialogHeader>

        <div className="flex-1 min-h-0 overflow-y-auto space-y-4">
          {work && (
            <>
              <div className="flex items-center gap-3">
                <Button size="sm" onClick={() => setPlaying((p) => !p)}>
                  {playing ? <Box size={14} /> : <Play size={14} />}
                  {playing ? '关闭预览' : '游玩'}
                </Button>
                <Button size="sm" variant="outline" onClick={toggleLike} disabled={busyLike}>
                  <ThumbsUp size={14} />
                  {likes}
                </Button>
              </div>

              {playing && (
                <div className="rounded-lg border border-laap-border overflow-hidden bg-black aspect-video">
                  <iframe
                    src={communityWorkUrl(work.id)}
                    className="w-full h-full"
                    title={work.title}
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                  />
                </div>
              )}

              <div>
                <h4 className="text-[13px] font-mono text-laap-gold uppercase tracking-wider mb-2">评论</h4>
                <div className="space-y-2 mb-3 max-h-40 overflow-y-auto">
                  {comments.length === 0 && (
                    <p className="text-[13px] text-laap-text-tertiary">暂无评论，来抢沙发。</p>
                  )}
                  {comments.map((c) => (
                    <div key={c.id} className="text-[13px] text-laap-text-secondary border-b border-laap-border/50 pb-2">
                      <span className="text-laap-cyan font-medium">{c.author}</span>
                      <span className="mx-2 text-laap-text-tertiary">·</span>
                      <span>{c.text}</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder={isCommunityLoggedIn() ? `以 ${user?.name} 的身份评论` : '登录后评论'}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && submitComment()}
                  />
                  <Button onClick={submitComment}><MessageSquare size={14} />发送</Button>
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Meta({ type, likes, plays, createdAt }: { type: string; likes: number; plays: number; createdAt?: string }) {
  const t = TYPE_META[type] || TYPE_META.webapp;
  const Icon = t.icon;
  return (
    <span className="inline-flex items-center gap-2 text-[12px] text-laap-text-tertiary font-normal">
      <span className={`inline-flex items-center gap-1 ${t.color}`}><Icon size={13} />{t.label}</span>
      <span className="inline-flex items-center gap-1"><ThumbsUp size={13} />{likes}</span>
      <span className="inline-flex items-center gap-1"><Eye size={13} />{plays}</span>
      {createdAt && <span>{fmtDate(createdAt)}</span>}
    </span>
  );
}

function WorkCard({ work, onOpen, isMine, onDelete }: {
  work: CommunityWork;
  onOpen: () => void;
  isMine: boolean;
  onDelete: () => void;
}) {
  const t = TYPE_META[work.type] || TYPE_META.webapp;
  const Icon = t.icon;
  return (
    <div className="group relative bg-laap-bg-secondary border border-[#27272a] rounded-xl p-5 transition-all hover:border-laap-gold/40 hover:bg-[#111111]">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg bg-laap-gold/10 flex items-center justify-center ${t.color}`}>
          <Icon size={20} strokeWidth={1.8} />
        </div>
        {isMine && (
          <button
            onClick={onDelete}
            className="text-laap-text-tertiary hover:text-laap-rose transition-colors"
            title="下架"
          >
            <Trash2 size={15} />
          </button>
        )}
      </div>
      <h3 className="text-white font-medium mb-1 group-hover:text-laap-gold transition-colors">{work.title}</h3>
      <p className="text-[13px] text-laap-text-secondary mb-3 line-clamp-2 min-h-[36px]">{work.description || '暂无简介'}</p>
      <div className="flex flex-wrap gap-1.5 mb-3">
        {work.tags?.slice(0, 3).map((tag) => (
          <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
        ))}
      </div>
      <div className="flex items-center justify-between">
        <Meta type={work.type} likes={work.likes} plays={work.plays} createdAt={work.published_at} />
        <Button size="sm" variant="outline" onClick={onOpen}>
          <Play size={14} />品鉴
        </Button>
      </div>
    </div>
  );
}

// ── 发布表单 ───────────────────────────────────────────
function PublishPanel({ onChanged }: { onChanged: () => void }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState('webapp');
  const [tags, setTags] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!title.trim()) return toast.error('请填写作品名称');
    if (!file) return toast.error('请选择作品 zip（需含 index.html）');
    if (!isCommunityLoggedIn()) return toast.error('请先登录');
    setBusy(true);
    try {
      const fileBase64 = await file.arrayBuffer().then((b) => {
        let binary = '';
        const bytes = new Uint8Array(b);
        const chunk = 0x8000;
        for (let i = 0; i < bytes.length; i += chunk) {
          binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
        }
        return btoa(binary);
      });
      await communityPublish({
        title: title.trim(),
        description: description.trim(),
        type,
        tags: tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
        fileBase64,
      });
      toast.success('发布成功，已同步到云端社区');
      setTitle(''); setDescription(''); setTags(''); setFile(null);
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '发布失败');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto bg-laap-bg-secondary border border-[#27272a] rounded-xl p-7 space-y-4">
      <h3 className="text-lg text-white font-medium">发布到云端社区</h3>
      <p className="text-[13px] text-laap-text-secondary">上传已构建的 Web 应用 zip（需含 index.html）。发布后任何人可通过公网链接品鉴游玩。</p>
      <Input placeholder="作品名称" value={title} onChange={(e) => setTitle(e.target.value)} />
      <Textarea placeholder="一句话简介" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
      <div className="flex gap-3">
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="h-9 flex-1 rounded-md border border-laap-border bg-laap-bg-primary px-3 text-sm text-laap-text-primary outline-none focus:border-laap-gold"
        >
          <option value="webapp">网页应用</option>
          <option value="site">网站</option>
          <option value="game">游戏</option>
        </select>
        <Input placeholder="标签，逗号分隔" value={tags} onChange={(e) => setTags(e.target.value)} />
      </div>
      <label className="flex items-center gap-3 rounded-lg border border-dashed border-laap-border p-4 cursor-pointer hover:border-laap-gold/50 transition-colors">
        <Upload className="text-laap-gold" size={18} />
        <span className="text-[13px] text-laap-text-secondary">
          {file ? file.name : '选择作品 zip（含 index.html）'}
        </span>
        <input type="file" accept=".zip" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      </label>
      <Button className="w-full" onClick={submit} disabled={busy}>
        {busy && <Loader2 className="animate-spin" />}
        发布
      </Button>
    </div>
  );
}

// ── 主页面 ─────────────────────────────────────────────
export default function CommunityPage() {
  const [works, setWorks] = useState<CommunityWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [authOpen, setAuthOpen] = useState(false);
  const [detail, setDetail] = useState<CommunityWork | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [user, setUser] = useState<CommunityUser | null>(getCommunityUser());
  const [tab, setTab] = useState('discover');

  const load = useCallback(async (p: number, mine: boolean) => {
    setLoading(true);
    try {
      const r = await communityListWorks({ page: p, limit: 12, mine });
      setWorks(r.works);
      setHasMore(r.hasMore);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '加载社区失败');
      setWorks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(0, tab === 'mine');
    setPage(0);
  }, [tab, load]);

  useEffect(() => {
    const onAuth = () => setUser(getCommunityUser());
    window.addEventListener('laap-community-auth', onAuth);
    return () => window.removeEventListener('laap-community-auth', onAuth);
  }, []);

  async function openDetail(w: CommunityWork) {
    setDetail(w);
    setDetailOpen(true);
    try {
      const fresh = await communityGetWork(w.id);
      setDetail(fresh);
    } catch { /* keep cached */ }
  }

  async function deleteWork(w: CommunityWork) {
    if (!window.confirm(`确定下架「${w.title}」？`)) return;
    try {
      await communityDeleteWork(w.id);
      toast.success('已下架');
      load(page, tab === 'mine');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '下架失败');
    }
  }

  const isMine = (w: CommunityWork) => user?.id === w.owner_id;

  return (
    <div className="min-h-screen bg-laap-bg-primary pt-32 pb-24">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <div className="relative mb-10 overflow-hidden rounded-sm border border-laap-border bg-laap-bg-secondary/30 p-8 md:p-12">
          <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-laap-gold mb-3">Community</div>
          <h1 className="font-display text-4xl md:text-5xl text-white mb-4">LAAP 社区</h1>
          <p className="text-laap-text-secondary max-w-[640px]">
            由 LAAP 数字生命生成的网页应用、网站与游戏，云端公共社区。浏览品鉴、发布作品、点赞评论。
          </p>
          <div className="mt-5 flex items-center gap-3">
            <Button variant="outline" onClick={() => setAuthOpen(true)}>
              {user ? <LogOut size={15} /> : <LogIn size={15} />}
              {user ? user.name : '登录 / 注册'}
            </Button>
            {user && (
              <Button
                variant="ghost"
                onClick={() => { communityLogout(); toast.success('已退出登录'); }}
                className="text-laap-text-tertiary"
              >
                <LogOut size={14} />退出
              </Button>
            )}
            <Button variant="ghost" onClick={() => load(page, tab === 'mine')} className="text-laap-text-tertiary">
              <RefreshCw size={14} />刷新
            </Button>
          </div>
        </div>

        <Tabs value={tab} onValueChange={setTab} className="mb-8">
          <TabsList>
            <TabsTrigger value="discover">发现</TabsTrigger>
            {user && <TabsTrigger value="mine">我的作品</TabsTrigger>}
            <TabsTrigger value="publish">发布</TabsTrigger>
          </TabsList>

          <TabsContent value="discover" className="mt-6">
            {loading ? (
              <div className="flex justify-center py-20 text-laap-text-tertiary"><Loader2 className="animate-spin" /></div>
            ) : works.length === 0 ? (
              <div className="text-center py-20 text-laap-text-tertiary">社区还没有作品，去发布第一个吧。</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {works.map((w) => (
                  <WorkCard key={w.id} work={w} isMine={isMine(w)} onOpen={() => openDetail(w)} onDelete={() => deleteWork(w)} />
                ))}
              </div>
            )}
            {hasMore && (
              <div className="flex justify-center mt-8">
                <Button variant="outline" onClick={() => { const np = page + 1; setPage(np); load(np, tab === 'mine'); }}>
                  加载更多
                </Button>
              </div>
            )}
          </TabsContent>

          {user && (
            <TabsContent value="mine" className="mt-6">
              {loading ? (
                <div className="flex justify-center py-20 text-laap-text-tertiary"><Loader2 className="animate-spin" /></div>
              ) : works.length === 0 ? (
                <div className="text-center py-20 text-laap-text-tertiary">你还没有发布作品。</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                  {works.map((w) => (
                    <WorkCard key={w.id} work={w} isMine onOpen={() => openDetail(w)} onDelete={() => deleteWork(w)} />
                  ))}
                </div>
              )}
            </TabsContent>
          )}

          <TabsContent value="publish" className="mt-6">
            <PublishPanel onChanged={() => load(0, tab === 'mine')} />
          </TabsContent>
        </Tabs>
      </div>

      <AuthDialog open={authOpen} onOpenChange={setAuthOpen} />
      <WorkDialog work={detail} open={detailOpen} onOpenChange={setDetailOpen} onChanged={() => load(page, tab === 'mine')} />
    </div>
  );
}