import { useEffect, useState } from 'react';
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { login, register, notifyAuthChange } from '@/lib/auth';

interface AuthModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function AuthModal({ open, onOpenChange, onSuccess }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) resetForm();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function resetForm() {
    setUsername('');
    setEmailOrUsername('');
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setShowPassword(false);
    setError(null);
  }

  function switchMode(next: 'login' | 'register') {
    setMode(next);
    resetForm();
  }

  function validate(): string | null {
    if (mode === 'register') {
      if (!username.trim()) return '请输入用户名';
      if (!email.trim()) return '请输入邮箱';
      if (!email.trim().includes('@')) return '邮箱格式不正确';
      if (password.length < 6) return '密码至少 6 位';
      if (password !== confirmPassword) return '两次输入的密码不一致';
    } else {
      if (!emailOrUsername.trim()) return '请输入邮箱或用户名';
      if (!password) return '请输入密码';
    }
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      setIsLoading(false);
      return;
    }

    const result =
      mode === 'register'
        ? await register(username.trim(), email.trim(), password)
        : await login(emailOrUsername.trim(), password);

    setIsLoading(false);

    if (!result.ok) {
      setError(result.error);
      return;
    }

    notifyAuthChange();
    onSuccess?.();
    onOpenChange(false);
    resetForm();
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        showCloseButton
        className="bg-laap-bg-secondary border-laap-border text-laap-text-primary w-full max-w-sm sm:max-w-md max-h-[85dvh] overflow-y-auto"
      >
        <DialogHeader>
          <DialogTitle className="text-white">
            {mode === 'login' ? '登录 LAAP' : '加入 LAAP'}
          </DialogTitle>
          <DialogDescription className="text-laap-text-tertiary">
            {mode === 'login'
              ? '登录后可在多设备同步你的数字生命体数据'
              : '创建一个账户，开启长期羁绊'}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-2 flex border border-laap-border rounded-sm overflow-hidden">
          <button
            type="button"
            onClick={() => switchMode('login')}
            className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
              mode === 'login'
                ? 'bg-laap-gold/10 text-laap-gold'
                : 'text-laap-text-secondary hover:text-white hover:bg-laap-bg-tertiary'
            }`}
          >
            登录
          </button>
          <button
            type="button"
            onClick={() => switchMode('register')}
            className={`flex-1 py-2.5 text-sm font-medium transition-colors border-l border-laap-border ${
              mode === 'register'
                ? 'bg-laap-gold/10 text-laap-gold'
                : 'text-laap-text-secondary hover:text-white hover:bg-laap-bg-tertiary'
            }`}
          >
            注册
          </button>
        </div>

        {error && (
          <div className="flex items-start gap-2.5 p-3 rounded-sm text-sm bg-laap-rose/10 text-laap-rose border border-laap-rose/30">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-xs uppercase tracking-wider text-laap-text-tertiary mb-1.5">
                用户名
              </label>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="你的名字或代号"
                className="w-full bg-laap-bg-primary border border-laap-border rounded-sm px-4 py-2.5 text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none focus:border-laap-gold transition-colors"
              />
            </div>
          )}

          {mode === 'login' ? (
            <div>
              <label className="block text-xs uppercase tracking-wider text-laap-text-tertiary mb-1.5">
                邮箱 / 用户名
              </label>
              <input
                type="text"
                required
                value={emailOrUsername}
                onChange={(e) => setEmailOrUsername(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-laap-bg-primary border border-laap-border rounded-sm px-4 py-2.5 text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none focus:border-laap-gold transition-colors"
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs uppercase tracking-wider text-laap-text-tertiary mb-1.5">
                邮箱
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-laap-bg-primary border border-laap-border rounded-sm px-4 py-2.5 text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none focus:border-laap-gold transition-colors"
              />
            </div>
          )}

          <div>
            <label className="block text-xs uppercase tracking-wider text-laap-text-tertiary mb-1.5">
              密码
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="至少 6 位字符"
                className="w-full bg-laap-bg-primary border border-laap-border rounded-sm px-4 py-2.5 pr-11 text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none focus:border-laap-gold transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-laap-text-tertiary hover:text-white transition-colors"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-xs uppercase tracking-wider text-laap-text-tertiary mb-1.5">
                确认密码
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={6}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="再次输入密码"
                className="w-full bg-laap-bg-primary border border-laap-border rounded-sm px-4 py-2.5 text-sm text-white placeholder:text-laap-text-tertiary focus:outline-none focus:border-laap-gold transition-colors"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 bg-laap-gold text-laap-bg-primary font-medium text-sm py-2.5 rounded-sm hover:bg-laap-gold-light transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isLoading && <Loader2 size={16} className="animate-spin" />}
            {mode === 'login' ? '登录' : '注册'}
          </button>
        </form>

        <p className="text-center text-xs text-laap-text-tertiary">
          {mode === 'login' ? '还没有账户？' : '已有账户？'}
          <button
            type="button"
            onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
            className="ml-1 text-laap-gold hover:underline"
          >
            {mode === 'login' ? '立即注册' : '立即登录'}
          </button>
        </p>
      </DialogContent>
    </Dialog>
  );
}
