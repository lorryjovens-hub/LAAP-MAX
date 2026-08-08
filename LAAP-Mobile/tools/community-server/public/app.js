"use strict";

const TYPE_ICON = { web: "🌐", site: "🧭", game: "🎮" };
const TYPE_LABEL = { web: "网页应用", site: "网站", game: "游戏" };

let apps = [];

async function api(url, opts) {
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({ error: "bad response" }));
  if (!res.ok) throw new Error(data.error || ("HTTP " + res.status));
  return data;
}

async function loadApps() {
  try {
    apps = await api("/api/apps");
  } catch (e) {
    apps = [];
  }
  renderGrid();
}

function renderGrid() {
  const grid = document.getElementById("app-grid");
  if (!apps.length) {
    grid.innerHTML = `<p class="hint">社区还没有作品，点击上方「发布」成为第一个创作者。</p>`;
    return;
  }
  grid.innerHTML = apps
    .map(
      (a) => `
      <div class="app-card" data-id="${a.id}">
        <div class="thumb">${TYPE_ICON[a.type] || "🌐"}</div>
        <h3>${escapeHtml(a.name)}</h3>
        <div class="meta">
          <span class="type-tag">${TYPE_LABEL[a.type] || "应用"}</span>
          <span>${escapeHtml(a.author || "匿名")}</span>
          <span>${a.downloads || 0} 次游玩</span>
        </div>
      </div>`,
    )
    .join("");
}

function showDetail(id) {
  const a = apps.find((x) => x.id === id);
  if (!a) return;
  const detail = document.getElementById("app-detail");
  detail.classList.remove("hidden");
  document.getElementById("app-grid").style.display = "none";
  document.getElementById("app-detail").innerHTML = `
    <div class="row">
      <h2>${escapeHtml(a.name)}</h2>
      <span class="type-tag">${TYPE_LABEL[a.type] || "应用"}</span>
      <button class="back" onclick="closeDetail()">返回</button>
      <button class="play" onclick="playApp('${a.id}')">▶ 打开品鉴</button>
    </div>
    <p class="hint">${escapeHtml(a.author || "匿名")} · ${escapeHtml(a.description || "暂无简介")}</p>
    <div id="app-frame-wrap"></div>
  `;
  detail.scrollIntoView({ behavior: "smooth" });
}

function closeDetail() {
  document.getElementById("app-detail").classList.add("hidden");
  document.getElementById("app-detail").innerHTML = "";
  document.getElementById("app-grid").style.display = "";
}

function playApp(id) {
  const a = apps.find((x) => x.id === id);
  if (!a) return;
  const wrap = document.getElementById("app-frame-wrap");
  if (a.url && (a.url.startsWith("http://") || a.url.startsWith("https://"))) {
    wrap.innerHTML = `<iframe src="${escapeHtml(a.url)}" allow="camera; microphone; geolocation; fullscreen; autoplay"></iframe>`;
  } else {
    wrap.innerHTML = `<iframe src="/app/${encodeURIComponent(id)}/" allow="camera; microphone; geolocation; fullscreen; autoplay"></iframe>`;
  }
  a.downloads = (a.downloads || 0) + 1;
}

document.getElementById("app-grid").addEventListener("click", (e) => {
  const card = e.target.closest(".app-card");
  if (card) showDetail(card.dataset.id);
});

document.getElementById("nav-browse").addEventListener("click", () => switchView("browse"));
document.getElementById("nav-publish").addEventListener("click", () => switchView("publish"));

function switchView(name) {
  document.getElementById("nav-browse").classList.toggle("active", name === "browse");
  document.getElementById("nav-publish").classList.toggle("active", name === "publish");
  document.getElementById("browse-view").classList.toggle("hidden", name !== "browse");
  document.getElementById("publish-view").classList.toggle("hidden", name !== "publish");
  if (name === "browse") loadApps();
}

document.getElementById("publish-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const msg = document.getElementById("publish-msg");
  const file = document.getElementById("p-file").files[0];
  const url = document.getElementById("p-url").value.trim();
  const name = document.getElementById("p-name").value.trim();
  const type = document.getElementById("p-type").value;
  const author = document.getElementById("p-author").value.trim();
  const description = document.getElementById("p-desc").value.trim();

  try {
    if (file) {
      const fd = new FormData();
      fd.append("name", name);
      fd.append("type", type);
      fd.append("author", author);
      fd.append("description", description);
      fd.append("file", file);
      await api("/api/apps", { method: "POST", body: fd });
    } else {
      if (!url) throw new Error("请上传 zip 或填写外部网址");
      await api("/api/apps", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, type, author, description, url }),
      });
    }
    msg.textContent = "发布成功！";
    document.getElementById("publish-form").reset();
    loadApps();
  } catch (e) {
    msg.textContent = "发布失败：" + e.message;
  }
});

function escapeHtml(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

loadApps();