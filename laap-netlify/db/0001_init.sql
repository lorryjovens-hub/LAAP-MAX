-- ============================================================
--  LAAP Community · 数据库 Schema 迁移 (0001_init)
--  PostgreSQL（兼容 Supabase SQL Editor / Neon）
--  执行后创建：users / works / comments / work_likes / sync_cursors
-- ============================================================

-- UUID 生成
create extension if not exists pgcrypto;

-- ── 枚举 ────────────────────────────────────────────────────
create type work_type as enum ('webapp', 'site', 'game');
create type work_status as enum ('published', 'hidden', 'reported');

-- ── users ───────────────────────────────────────────────────
create table if not exists users (
  id            uuid primary key default gen_random_uuid(),
  email         text not null unique,
  password_hash text not null,
  name          text not null,
  avatar_url    text,
  bio           text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ── works ──────────────────────────────────────────────────
create table if not exists works (
  id           uuid primary key default gen_random_uuid(),
  owner_id     uuid not null references users(id) on delete cascade,
  title        text not null,
  description  text,
  type         work_type not null default 'webapp',
  files_ref    text not null,          -- 对象存储路径/引用
  size         bigint not null default 0,
  tags         text[] not null default '{}',
  likes        int not null default 0,
  plays        int not null default 0,
  status       work_status not null default 'published',
  published_at timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists works_owner_idx  on works(owner_id);
create index if not exists works_status_idx on works(status, published_at desc);

-- ── comments ───────────────────────────────────────────────
create table if not exists comments (
  id         uuid primary key default gen_random_uuid(),
  work_id    uuid not null references works(id) on delete cascade,
  user_id    uuid not null references users(id) on delete cascade,
  text       text not null,
  created_at timestamptz not null default now()
);
create index if not exists comments_work_idx on comments(work_id);

-- ── work_likes（点赞去重） ─────────────────────────────────
create table if not exists work_likes (
  work_id    uuid not null references works(id) on delete cascade,
  user_id    uuid not null references users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (work_id, user_id)
);

-- ── sync_cursors（本地↔云端同步游标） ─────────────────────
create table if not exists sync_cursors (
  device_id      text primary key,
  user_id        uuid references users(id) on delete set null,
  last_synced_at timestamptz not null default now(),
  pending_ops    jsonb not null default '[]'
);

-- ── updated_at 自动维护 ────────────────────────────────────
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_users_updated on users;
create trigger trg_users_updated
  before update on users
  for each row execute function set_updated_at();

drop trigger if exists trg_works_updated on works;
create trigger trg_works_updated
  before update on works
  for each row execute function set_updated_at();