import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { Eye, EyeOff, CheckCircle2, AlertCircle, Loader2, User, LogOut } from 'lucide-react';
import { register, login, logout, getCurrentUser, isLoggedIn } from '@/lib/auth';
import { isGuest } from '@/lib/userMode';
import type { User as AuthUser } from '@/lib/auth';

export default function AuthPage() {
  const navigate = useNavigate();

  const [loggedIn, setLoggedIn] = useState(isLoggedIn());
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    let mounted = true;
    getCurrentUser().then((user) => {
      if (mounted) {
        setCurrentUser(user);
        // 游客也算返回了用户对象，但只有真实账户才算“已登录”
        setLoggedIn(!!user && !isGuest());
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  function resetForm() {
    setName('');
    setEmail('');
    setPassword('');
    setMessage(null);
  }

  function switchMode(next: 'login' | 'register') {
    setMode(next);
    resetForm();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    const result = mode === 'register'
      ? await register(name, email, password)
      : await login(email, password);

    setLoading(false);

    if (!result.ok) {
      setMessage({ type: 'error', text: result.error });
      return;
    }

    setCurrentUser(result.user);
    setLoggedIn(true);
    setMessage({ type: 'success', text: mode === 'register' ? '注册成功，正在进入…' : '登录成功，正在进入…' });
    setTimeout(() => navigate('/studio'), 800);
  }

  async function handleLogout() {
    await logout();
    setCurrentUser(null);
    setLoggedIn(false);
    resetForm();
    setMode('login');
    setMessage({ type: 'success', text: '已安全退出' });
  }

  return (
    <div className="min-h-screen bg-laap-bg-primary pt-32 pb-24">
      <div className="max-w-[420px] mx-auto px-6">
        <div className="text-center mb-10">
          <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-laap-gold mb-3">Identity</div>
          <h1 className="font-display text-3xl md:text-4xl text-white">
            {loggedIn ? '账户中心' : mode === 'login' ? '登录 LAAP' : '加入 LAAP'}
          </h1>
          <p className="mt-3 text-laap-text-secondary text-sm">
            {loggedIn
              ? '管理你的数字生命体身份'
              : '创建一个账户，开启与你的数字生命体的长期羁绊。'}
          </p>
        </div>

        <div className="border border-laap-border rounded-sm bg-laap-bg-secondary/30 p-8">
          {loggedIn ? (
            <div className="text-center space-y-6">
              <div className="w-16 h-16 mx-auto rounded-full bg-laap-gold/10 border border-laap-gold/30 flex items-center justify-center">
                <User size={28} className="text-laap-gold" />
              </div>
              <div>
                <div className="font-display text-xl text-white">{currentUser?.username}</div>
                <div className="text-sm text-laap-text-secondary mt-1">{currentUser?.email}</div>
              </div>
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-2 px-6 py-2.5 text-sm text-white border border-laap-border rounded-sm hover:border-laap-rose hover:text-laap-rose transition-colors"
              >
                <LogOut size={16} />
                退出登录
              </button>
            </div>
          ) : (
            <>
              <div className="flex border border-laap-border rounded-sm overflow-hidden mb-8">
                <button
                  type="button"
                  onClick={() => switchMode('login')}
                  className={`flex-1 py-3 text-sm font-medium transition-colors ${
                    mode === 'login' ? 'bg-laap-gold/10 text-laap-gold' : 'text-laap-text-secondary hover:text-white hover:bg-laap-bg-tertiary'
                  }`}
                >
                  登录
                </button>
                <button
                  type="button"
                  onClick={() => switchMode('register')}
                  className={`flex-1 py-3 text-sm font-medium transition-colors border-l border-laap-border ${
                    mode === 'register' ? 'bg-laap-gold/10 text-laap-gold' : 'text-laap-text-secondary hover:text-white hover:bg-laap-bg-tertiary'
                  }`}
                >
                  注册
                </button>
              </div>

              {message && (
                <div
                  className={`flex items-start gap-2.5 p-3 rounded-sm text-sm mb-6 ${
                    message.type === 'success'
                      ? 'bg-laap-emerald/10 text-laap-emerald border border-laap-emerald/30'
                      : 'bg-laap-rose/10 text-laap-rose border border-laap-rose/30'
                  }`}
                >
                  {message.type === 'success' ? <CheckCircle2 size={16} className="mt-0.5" /> : <AlertCircle size={16} className="mt-0.5" />}
                  <span>{message.text}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                {mode === 'register' && (
                  <div>
                    <label className="block text-xs uppercase tracking-wider text-laap-text-tertiary mb-2">名称</label>
                    <input
                      type="text"
                      required
                      minLength={3}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="你的名字或代号"
                      className="w-full bg-laap-bg-primary border border-laap-border rounded-sm px-4 py-3 text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none focus:border-laap-gold transition-colors"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs uppercase tracking-wider text-laap-text-tertiary mb-2">邮箱 / 用户名</label>
                  <input
                    type="text"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full bg-laap-bg-primary border border-laap-border rounded-sm px-4 py-3 text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none focus:border-laap-gold transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-laap-text-tertiary mb-2">密码</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      minLength={mode === 'register' ? 8 : 6}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={mode === 'register' ? '至少 8 位字符' : '至少 6 位字符'}
                      className="w-full bg-laap-bg-primary border border-laap-border rounded-sm px-4 py-3 pr-11 text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none focus:border-laap-gold transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-laap-text-tertiary hover:text-white transition-colors"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 bg-laap-gold text-laap-bg-primary font-medium text-sm py-3 rounded-sm hover:bg-laap-gold-light transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loading && <Loader2 size={16} className="animate-spin" />}
                  {mode === 'login' ? '登录' : '注册'}
                </button>
              </form>

              <p className="mt-6 text-center text-xs text-laap-text-tertiary">
                {mode === 'login' ? '还没有账户？' : '已有账户？'}
                <button
                  type="button"
                  onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
                  className="ml-1 text-laap-gold hover:underline"
                >
                  {mode === 'login' ? '立即注册' : '立即登录'}
                </button>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
