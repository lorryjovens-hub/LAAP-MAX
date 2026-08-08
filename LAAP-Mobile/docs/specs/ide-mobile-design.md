# LAAP-Mobile IDE: Mobile App Development Tool Design

Turning LAAP-Mobile from a "Linux sandbox on phone" into a **mobile-first IDE**
with emulator/simulator capabilities, on top of the existing Alpine/PRoot sandbox
+ agent loop + CognitiveBus core.

---

## 1. Goal

Ship an on-phone development environment that lets the user:

1. **Create** a project from a template (web / Node / Python / static site).
2. **Edit** source files with a real code editor (syntax highlight, line
   numbers, monospace).
3. **Run** the project inside the existing Linux sandbox (dev server, script,
   or build command), capturing stdout/stderr into a live console.
4. **Preview** the running app:
   - Web projects → embedded WebView pointed at the dev server URL.
   - Static HTML/JS → `laap://` resource URL (existing preview path).
   - Android APK builds → install + launch on the host device via
     `PackageInstaller` / `adb`-equivalent (Shizuku path).
5. **Drive** the whole workflow from chat (LLM agent) via new `project_*`
   tools, exactly like the existing `shell_execute` / `file_*` tools.

## 2. What's Already There (Reuse)

| Capability | Existing Module |
|---|---|
| Linux sandbox (Alpine + PRoot) | `sandbox.PRootKernel`, `sandbox.RootfsManager` |
| Per-session persistent shell | `sandbox.PersistentShell`, `sandbox.ExecutionCoordinator` |
| Interactive PTY terminal | `sandbox.TerminalSession`, `ui.terminal.*` |
| File read/write/edit (host side) | `tools.FileReadTool`, `FileWriteTool`, `FileEditTool` |
| File browser UI | `ui.sandbox.FileBrowserScreen`, `FileBrowserViewModel` |
| HTML preview (laap://) | `ui.preview.WebPreviewFullscreenScreen`, `LaapImageFetcher` |
| WebView host | `webapp.WebAppActivity`, `ui.browser.BrowserWebView` |
| Markdown + syntax highlight | `ui.markdown.MarkdownParser`, `SyntaxHighlighter` |
| Agent tool registry | `tools.AgentTools` |
| Room DB + migrations | `data.db.AppDatabase` (v10) |
| Compose Nav | `ui.navigation.AppNavigation`, `Routes` |
| Cognitive core | `laap.CognitiveBus`, `PSILoop`, `ArisEngineClient`, … |

The IDE layer is **additive** — it composes these primitives rather than
replacing them.

## 3. New Components

### 3.1 Data Layer (`data/db/ide/`)

- `ProjectEntity` — `id, name, template_id, dir_path (relative to /var/laap/projects/), created_at, last_opened_at, description`
- `RunConfigEntity` — `id, project_id (FK), name, command, env_json, port, run_type {DEV_SERVER | ONESHOT | BUILD}, is_default`
- `ProjectDao`, `RunConfigDao`
- `AppDatabase` bumped v10 → v11 with a pure-additive migration.

### 3.2 Domain Layer (`ide/`)

- `ProjectTemplate` — id, displayName, description, file tree (relative
  path → content), default run config, language id for highlighter.
  Registry: `STATIC_HTML`, `VITE_REACT`, `NODE_EXPRESS`, `PYTHON_FLASK`,
  `PYTHON_SCRIPT`.
- `ProjectManager` — `create(name, templateId)`, `delete(id)`,
  `list()`, `get(id)`, `openInSandbox(id)`. Materializes the template
  file tree under `/var/laap/projects/<id>/` (host: `filesDir/laap-global/projects/<id>`).
  Uses `PRootKernel` bind mounts (existing pattern) so the sandbox
  path resolves.
- `ProjectRunManager` — `startRun(projectId, runConfigId)`,
  `stopRun(projectId)`, `tailOutput(projectId): Flow<String>`,
  `previewUrl(projectId): String?`. Backed by `ExecutionCoordinator`
  with a synthetic sessionId `"project:<id>"` so each project gets its
  own `PersistentShell` (existing per-session shell isolation).
  Output is teed into a `MutableSharedFlow` that the console UI
  collects.

### 3.3 UI Layer (`ui/ide/`)

- `CodeEditor.kt` — Compose `BasicTextField` with:
  - Monospace font (`ui.terminal.TerminalFonts`)
  - Optional line-number gutter
  - Regex-based syntax highlighting per language (extends
    `ui.markdown.SyntaxHighlighter`)
  - Save button (writes via `FileWriteTool` host-side logic)
- `IdeHomeScreen.kt` — project list + "New Project" FAB → template
  picker dialog → name input → create.
- `ProjectWorkspaceScreen.kt` — three-tab bottom nav:
  - **Files** — file tree (reuses `FileBrowserViewModel` pattern,
    rooted at the project dir) + tap to open in editor.
  - **Editor** — `CodeEditor` + open-tab strip.
  - **Run** — run-config picker + Start/Stop button + live console
    (reuses terminal-emulator primitives, simplified) + "Open Preview"
    chip when `run_type == DEV_SERVER`.
- `CreateProjectDialog.kt` — name + template picker.

### 3.4 Routing & Entry Points

- New `Routes.IDE_HOME = "ide"`, `Routes.IDE_PROJECT = "ide/project/{projectId}"`.
- Entry in `SessionListScreen` overflow menu (alongside "Shell Terminal"
  and "Rootfs Management").
- Deep-link `laap://ide` and `laap://ide/project/<id>` added to
  `DeepLinkCoordinator`.

### 3.5 Agent Tools (`tools/IdeTools.kt`)

Added to `AgentTools.makeAgentTools()`:

- `project_create(name, template_id)` → creates project, returns id + path.
- `project_open(project_id)` → returns file listing.
- `project_run(project_id, run_config_id?)` → starts run, returns
  early stdout + preview URL.
- `project_stop(project_id)` → kills the project's persistent shell.
- `project_log(project_id, lines?)` → tails recent output.

These compose cleanly with the existing `shell_execute`, `file_*`,
and `browser_use` tools — the agent can mix freely (e.g. create a
project, then `shell_execute` `npm install lodash`, then `project_run`).

## 4. Emulator / Simulator Strategy

The "emulator/simulator" requirement is interpreted as follows:

| Project Type | "Simulator" Approach |
|---|---|
| **Static HTML/JS/CSS** | `laap://` resource URL inside the existing `WebPreviewFullscreenScreen` — zero extra infra. |
| **Vite / dev-server web** | Dev server runs in sandbox; embedded WebView in `Run` tab points at `http://localhost:<port>`. Hot reload works. |
| **Node CLI / script** | Stdout → console. No preview needed. |
| **Python (Flask)** | Same as Vite — `http://localhost:<port>` in WebView. |
| **Android APK** | Build with `aapt`/`ecj`/`d8`/`zipalign` in sandbox (Alpine `apk add android-tools`); then `adb install`-equivalent via Shizuku (existing `ShizukuOffloadHandler`) or `PackageInstaller` intent for sideload. Launch via `pm`-equivalent or `startActivity`. The phone IS the emulator. |
| **iOS app** | Out of scope for on-device sim. Provide a "Push to remote Mac" stub that exports the project zip and calls a user-configured webhook (future work). |

The phone-as-emulator path for Android APKs is the most distinctive
capability: the user writes Java/Kotlin source in the editor, the
sandbox cross-compiles to an APK, and Shizuku installs it on the same
device — closing the loop without a desktop.

## 5. MVP Scope (What Ships in This Change)

**In:**
- Project entity + DAO + migration
- ProjectTemplate registry (5 templates)
- ProjectManager + ProjectRunManager
- CodeEditor composable (syntax highlight for: html, css, js, ts,
  json, py, kt, java, sh, md)
- IdeHomeScreen, ProjectWorkspaceScreen (Files/Editor/Run tabs)
- Routes + session-list entry + deep-links
- 5 `project_*` agent tools
- Strings

**Out (future work):**
- Multi-cursor / find-replace / LSP-grade autocomplete
- Git integration (use `shell_execute git …` for now)
- Remote Mac bridge for iOS sim
- On-device APK build (relies on `apk add` of android-tools at runtime;
  the IDE just runs the user's build script)
- iOS port of the new screens (Android-first; iOS parity tracked
  separately)

## 6. File Layout (New Files)

```
docs/specs/ide-mobile-design.md          ← this doc
src/android/app/src/main/java/org/laap/mobile/
  data/db/ide/
    ProjectEntity.kt
    RunConfigEntity.kt
    ProjectDao.kt
    RunConfigDao.kt
  data/repository/
    ProjectRepository.kt
  ide/
    ProjectTemplate.kt
    ProjectTemplates.kt
    ProjectManager.kt
    ProjectRunManager.kt
  ui/ide/
    CodeEditor.kt
    IdeHomeScreen.kt
    IdeHomeViewModel.kt
    ProjectWorkspaceScreen.kt
    ProjectWorkspaceViewModel.kt
    CreateProjectDialog.kt
  tools/
    IdeTools.kt
```

Modified files: `AppDatabase.kt` (bump v10→v11, add DAOs),
`AppNavigation.kt` (routes), `SessionListScreen.kt` (overflow entry),
`AgentTools.kt` (register `project_*`), `DeepLinkCoordinator.kt`
(routes), `LaapApp.kt` (init `ProjectRepository`), `strings.xml`.
