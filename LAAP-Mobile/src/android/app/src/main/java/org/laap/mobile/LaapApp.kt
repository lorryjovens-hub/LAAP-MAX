package org.laap.mobile

import android.app.Activity
import android.app.Application
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.util.Log
import org.acra.ACRA
import org.acra.ReportField
import org.acra.config.CoreConfigurationBuilder
import org.acra.data.StringFormat
import coil.ImageLoader
import coil.ImageLoaderFactory
import org.laap.mobile.browser.BrowserTabPool
import org.laap.mobile.data.db.AppDatabase
import org.laap.mobile.data.repository.BackgroundSettingsRepository
import org.laap.mobile.data.repository.ChatRepository
import org.laap.mobile.data.repository.EnvVarRepository
import org.laap.mobile.data.MountedFoldersStore
import org.laap.mobile.data.repository.MemoryRepository
import org.laap.mobile.data.repository.ProviderRepository
import org.laap.mobile.data.repository.WebAppShortcutRepository
import org.laap.mobile.data.repository.MCPRepository
import org.laap.mobile.data.repository.ProjectRepository
import org.laap.mobile.data.repository.SkillRepository
import org.laap.mobile.notification.BackgroundTaskNotifier
import org.laap.mobile.logging.AppLogger
import org.laap.mobile.network.NetworkMonitor
import org.laap.mobile.offload.OffloadPermissionManager
import org.laap.mobile.provider.ModelsDevApi
import org.laap.mobile.sandbox.ExecutionCoordinator
import org.laap.mobile.sandbox.MountedFolderCoordinator
import org.laap.mobile.sandbox.NativeOffloadServer
import org.laap.mobile.sandbox.PRootKernel
import org.laap.mobile.sandbox.RootfsManager
import org.laap.mobile.ide.ProjectManager
import org.laap.mobile.ide.ProjectRunManager
import org.laap.mobile.laap.CognitiveBus
import org.laap.mobile.laap.PSILoop
import org.laap.mobile.laap.Metacognition
import org.laap.mobile.laap.CognitiveSpeciesLibrary
import org.laap.mobile.laap.ArisEngineClient
import org.laap.mobile.laap.MobilePerceptionService
import org.laap.mobile.laap.PsiForegroundService
import org.laap.mobile.sandbox.offload.AccessibilityOffloadHandler
import org.laap.mobile.sandbox.offload.AlarmOffloadHandler
import org.laap.mobile.sandbox.offload.BrowserUseOffloadHandler
import org.laap.mobile.sandbox.offload.CalendarOffloadHandler
import org.laap.mobile.sandbox.offload.ClipboardOffloadHandler
import org.laap.mobile.sandbox.offload.ContactsOffloadHandler
import org.laap.mobile.sandbox.offload.DeviceOffloadHandler
import org.laap.mobile.sandbox.offload.LocationOffloadHandler
import org.laap.mobile.sandbox.offload.ModelUseOffloadHandler
import org.laap.mobile.sandbox.offload.SessionsOffloadHandler
import org.laap.mobile.sandbox.offload.ShizukuOffloadHandler
import org.laap.mobile.sandbox.offload.NotificationOffloadHandler
import org.laap.mobile.sandbox.offload.OpenOffloadHandler
import org.laap.mobile.sandbox.offload.PhotosOffloadHandler
import org.laap.mobile.sandbox.offload.PlayerOffloadHandler
import org.laap.mobile.sandbox.offload.SpeakOffloadHandler
import org.laap.mobile.sandbox.offload.SpeechOffloadHandler
import org.laap.mobile.sandbox.offload.WeatherOffloadHandler
import org.laap.mobile.service.SessionActivityTracker
import org.laap.mobile.ui.LaapImageFetcher
import kotlinx.coroutines.launch

class LaapApp : Application(), ImageLoaderFactory {
    lateinit var database: AppDatabase
        private set
    lateinit var chatRepository: ChatRepository
        private set
    lateinit var providerRepository: ProviderRepository
        private set
    lateinit var envVarRepository: EnvVarRepository
        private set
    lateinit var skillRepository: SkillRepository
        private set
    lateinit var mcpRepository: MCPRepository
        private set
    lateinit var memoryRepository: MemoryRepository
        private set
    lateinit var webAppShortcutRepository: WebAppShortcutRepository
        private set
    lateinit var projectRepository: ProjectRepository
        private set
    lateinit var projectManager: ProjectManager
        private set
    lateinit var projectRunManager: ProjectRunManager
        private set
    lateinit var backgroundSettingsRepository: BackgroundSettingsRepository
        private set
    lateinit var backgroundTaskNotifier: BackgroundTaskNotifier
        private set
    lateinit var mountedFoldersStore: MountedFoldersStore
        private set

    // ── LAAP Cognitive Core ──────────────────────────────────────────────
    // Source-level integration of LAAP's PSI engine, metacognition loop,
    // cognitive species library, and mobile perception. These singletons
    // are initialized in onCreate() and live for the entire app process,
    // mirroring the desktop LAAP harness architecture.
    lateinit var cognitiveBus: CognitiveBus
        private set
    lateinit var psiLoop: PSILoop
        private set
    lateinit var metacognition: Metacognition
        private set
    lateinit var speciesLibrary: CognitiveSpeciesLibrary
        private set
    lateinit var arisEngineClient: ArisEngineClient
        private set
    lateinit var mobilePerceptionService: MobilePerceptionService
        private set

    /**
     * T180-bg-notif: foreground-Activity counter, mutated by the
     * ActivityLifecycleCallbacks registered in [onCreate]. Read by
     * [BackgroundTaskNotifier] to decide whether to suppress completion
     * notifications (no notification while the user is already looking
     * at the app).
     */
    @Volatile
    private var foregroundActivityCount: Int = 0

    fun isAppForeground(): Boolean = foregroundActivityCount > 0

    /**
     * T-bg-overlay phase 2: live "is the app foreground?" stream so the
     * AgentForegroundService can react to background ↔ foreground
     * transitions and toggle the floating tool-status overlay. Same
     * source as [isAppForeground] (started/stopped balanced count) —
     * just exposed as a StateFlow for collectors.
     */
    // Initial true: prevents overlay flash before first Activity onStart emits foreground=true
    // (T-overlay-startup-flash). ActivityLifecycleCallbacks below will flip to the real value
    // on the next lifecycle tick.
    private val _isAppForegroundFlow = kotlinx.coroutines.flow.MutableStateFlow(true)
    val isAppForegroundFlow: kotlinx.coroutines.flow.StateFlow<Boolean>
        get() = _isAppForegroundFlow

    /**
     * App-wide network monitor. Mirrors iOS NetworkMonitor.shared — observes
     * connectivity transitions, evicts shared OkHttp connection pools, and
     * refreshes the sandbox's /etc/resolv.conf when DNS servers change.
     */
    val networkMonitor: NetworkMonitor = NetworkMonitor()

    /**
     * Application-scoped BrowserTabPool for shell-invoked `laap-browser-use`.
     * Separate from the per-ChatViewModel pool so browser state driven from
     * within an ish shell doesn't collide with the agent's own tabs.
     */
    val sharedBrowserTabPool: BrowserTabPool by lazy {
        BrowserTabPool(this).also { it.setSession("laap-browser-use") }
    }

    override fun attachBaseContext(base: Context) {
        super.attachBaseContext(base)
        // T283: install ACRA before any app-level singleton runs so a crash
        // anywhere from onCreate forward is captured. CrashFileSender
        // (registered via META-INF/services/org.acra.sender.ReportSenderFactory)
        // writes filesDir/logs/crash-<stamp>.log — same dir + .log extension
        // that AppLogger.listLogFiles already filters for, so reports surface
        // in LogManagementScreen with no extra UI.
        ACRA.init(
            this,
            CoreConfigurationBuilder()
                .withBuildConfigClass(BuildConfig::class.java)
                .withReportFormat(StringFormat.JSON)
                .withLogcatArguments(listOf("-t", "200", "-v", "time"))
                .withReportContent(
                    ReportField.APP_VERSION_NAME,
                    ReportField.APP_VERSION_CODE,
                    ReportField.ANDROID_VERSION,
                    ReportField.BUILD,
                    ReportField.PHONE_MODEL,
                    ReportField.BRAND,
                    ReportField.STACK_TRACE,
                    ReportField.LOGCAT,
                ),
        )
    }

    override fun onCreate() {
        super.onCreate()

        // T287-followup: ACRA spawns a separate reporter process named
        // "<package>:acra" (declared by the library's manifest) to send
        // the crash report after the main process dies. Application
        // subclasses run in EVERY process of the package, so without
        // this early-return the :acra process would also try to bind
        // the abstract socket / boot the database / register offload
        // handlers — racing the next main-process spawn for resources
        // it doesn't need. Symptom: main process gets EADDRINUSE on
        // LocalServerSocket and stays in a permanent restart loop on
        // the splash screen. Skip everything except ACRA.init (already
        // done in attachBaseContext, which is what makes the :acra
        // process do its job).
        if (ACRA.isACRASenderServiceProcess()) {
            Log.i("LaapApp", "skipping app init in :acra reporter process")
            return
        }

        // [T-codex-fast-mode] Capture the app context + warm the Fast Mode
        // flag cache so the provider layer (no Context) can read it at
        // request-build time — including offload / title-gen calls that
        // never pass through a ViewModel.
        org.laap.mobile.data.FastModePrefs.prime(this)

        // T283: install NDK signal handler for native crashes (SIGSEGV/
        // SIGABRT/SIGBUS/SIGFPE/SIGILL/SIGSYS). Writes a one-shot text
        // report to filesDir/logs/native-crash-<stamp>.log before re-raising
        // the signal so the system tombstone is also generated. Runs
        // before any other native lib (proot, pty_bridge, …) is dlopen'd
        // by the rest of onCreate so the handler is in place when those
        // libs first execute.
        try {
            org.laap.mobile.crash.NativeCrashHandler.install(
                java.io.File(filesDir, "logs"),
            )
        } catch (t: Throwable) {
            Log.w("LaapApp", "NativeCrashHandler install failed: ${t.message}")
        }

        // T-android-fgs-timeout-crash: chain an UncaughtExceptionHandler
        // ahead of ACRA's so we can intercept
        // android.app.RemoteServiceException$ForegroundServiceDidNotStopInTimeException
        // specifically. The mediaPlayback FGS type change removes the
        // dataSync 6h cap that was tripping this, but this handler keeps
        // the user from seeing a raw process-death if a future Android
        // version adds a new cap to mediaPlayback too. We can't actually
        // survive this exception (it's thrown on the main looper after
        // SystemServer has already decided to kill us) but we CAN:
        //  - stop the foreground service explicitly so the notification
        //    drops cleanly instead of lingering as a zombie row
        //  - delegate to ACRA so the crash log still hits disk
        try {
            val priorHandler = Thread.getDefaultUncaughtExceptionHandler()
            Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
                try {
                    val isFgsTimeout = throwable.javaClass.name.endsWith(
                        "RemoteServiceException\$ForegroundServiceDidNotStopInTimeException",
                    ) || (throwable.message?.contains("foreground service of type") == true &&
                        throwable.message?.contains("did not stop within its timeout") == true)
                    if (isFgsTimeout) {
                        Log.w(
                            "LaapApp",
                            "FGS timeout caught; stopping service before deferring to ACRA: ${throwable.message}",
                        )
                        // Stop the service so the system tears the
                        // sticky binding down cleanly instead of
                        // re-spawning into the same trap.
                        runCatching {
                            val intent = Intent(this, org.laap.mobile.service.AgentForegroundService::class.java)
                            stopService(intent)
                        }
                    }
                } catch (t: Throwable) {
                    Log.w("LaapApp", "FGS-timeout handler internal failure: ${t.message}")
                }
                // Always defer to the prior handler so ACRA's
                // dump-and-relaunch flow runs intact.
                priorHandler?.uncaughtException(thread, throwable)
            }
        } catch (t: Throwable) {
            Log.w("LaapApp", "install FGS-timeout handler failed: ${t.message}")
        }

        // T-android-crash-freq-share: local fallback for Crashlytics (#458).
        // Scan filesDir/logs/ for crash-*.log + native-crash-*.log files
        // touched in the last hour; if THRESHOLD+ are present, stash the
        // list so MainActivity.onCreate can prompt to share them.
        org.laap.mobile.crash.CrashFrequencyDetector.checkAtLaunch(this)

        // Hard short-circuit: when checkAtLaunch flips safe-mode ON, skip
        // every heavy subsystem (DB, repositories, offload server, PRoot
        // bind mounts, network monitor, …). The only thing MainActivity
        // will do is pop the share-or-dismiss dialog and finish. Without
        // this guard, anything from `chatRepository = ChatRepository(...)`
        // onward is a potential re-crash trigger on a loop — the whole
        // point of safe-mode is to stop the bleeding before another
        // segfault rewrites the log files.
        if (org.laap.mobile.crash.CrashFrequencyDetector.isSafeMode()) {
            Log.w("LaapApp", "safe-mode ON — skipping app subsystem init")
            return
        }

        // Initialize the daily-rotating file logger first. When the user has
        // logging enabled in Settings, this also kicks off stdout/stderr
        // capture so subsequent println / Throwable.printStackTrace lines from
        // the rest of onCreate land in today's log file. Mirrors iOS
        // `LoggingManager.startIfEnabled()` (called from LaapApp.swift:143).
        AppLogger.init(this)

        // Bug 2 (MIUI silent kill) diagnostic: write a launch-cycle beacon
        // so a subsequent launch can observe whether the previous run
        // exited cleanly (onTerminate hit) or was force-killed by LMK /
        // MIUI's aggressive background cleaner. Read on next launch by
        // [org.laap.mobile.diagnostics.LaunchCycleBeacon].
        try {
            org.laap.mobile.diagnostics.LaunchCycleBeacon.recordLaunch(this)
        } catch (t: Throwable) {
            Log.w("LaapApp", "LaunchCycleBeacon.recordLaunch failed: ${t.message}")
        }

        // Start the main-thread hang watchdog before the heavier subsystems
        // (DB / repositories / iSH bring-up) get going so it can observe any
        // stall in onCreate itself. Posts heartbeats at 1s cadence; if the
        // main thread fails to land one for 3s, the detector dumps the main
        // stack to filesDir/logs/stall-<date>.log and bumps a persisted
        // counter. AppNavigation reads that counter on cold start to
        // override the launch destination to home after 3 hangs in a row,
        // so a user trapped opening a session that hangs the UI gets
        // unstuck on the next launch.
        org.laap.mobile.diagnostics.HangDetector.start(this)

        database = AppDatabase.getInstance(this)
        chatRepository = ChatRepository(database.chatDao())
        providerRepository = ProviderRepository(this)
        envVarRepository = EnvVarRepository(this)
        skillRepository = SkillRepository(this)
        mcpRepository = MCPRepository(this)
        memoryRepository = MemoryRepository(java.io.File(filesDir, "laap-global/memory"))
        webAppShortcutRepository = WebAppShortcutRepository(database.webAppShortcutDao())

        // [ide-mobile] IDE layer — wraps the new ide_projects / ide_run_configs
        // tables. Initialised after the database so the repositories can
        // resolve their DAOs. ProjectManager wires the global `projects`
        // bind mount implicitly (PRootKernel.registerGlobalBindMounts is
        // called further down and now includes `projects`).
        projectRepository = ProjectRepository(database.projectDao(), database.runConfigDao())
        projectManager = ProjectManager(this, projectRepository)
        projectRunManager = ProjectRunManager(projectRepository)

        // [T-soul-md] Seed SOUL.md with the default content on first launch
        // so the Soul settings page and chat bubble identity have a real
        // file to read. Safe no-op on subsequent launches — never
        // overwrites existing user edits. Cache refresh primes the
        // synchronous metadata read-path (chat header / system prompt).
        org.laap.mobile.agent.SoulStore.ensureExists(this)
        org.laap.mobile.agent.SoulStore.refreshCache(this)

        // T-config: laap-config CLI surface — registry / audit log /
        // master-switch store. Initialized eagerly here so
        // ConfigRegistry.get() is safe from any thread for the rest of
        // the process. Mirrors iOS ConfigRegistry.shared.registerBuiltinsIfNeeded().
        org.laap.mobile.config.LaapConfigPermissionStore.init(this)
        org.laap.mobile.config.audit.ConfigAuditLog.init(this)
        org.laap.mobile.config.ConfigRegistry.init(
            this, providerRepository, envVarRepository, chatRepository,
        )

        // Initialize models.dev registry (loads from bundled asset, refreshes in background)
        ModelsDevApi.init(this)

        // Initialize sandbox singletons (does not trigger extraction)
        RootfsManager.getInstance(this)
        ExecutionCoordinator.init(this)
        ExecutionCoordinator.envVarRepository = envVarRepository

        // GH#94: Clean stale sandbox temp files on startup (30-day retention).
        // Runs in background to avoid blocking app initialization.
        kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO).launch {
            try {
                RootfsManager.getInstance(this@LaapApp).cleanupStaleTempFiles()
            } catch (e: Exception) {
                android.util.Log.w("LaapApp", "cleanupStaleTempFiles failed: ${e.message}")
            }
        }

        // ── LAAP Cognitive Core Initialization ───────────────────────────
        // Source-level integration: CognitiveBus → PSILoop → Metacognition
        // → SpeciesLibrary → ArisEngineClient → MobilePerceptionService.
        // Mirrors the desktop LAAP harness lifecycle: the cognitive bus is
        // the event spine, PSILoop runs the perceive→select→act→learn
        // cycle, Metacognition adapts loop parameters, SpeciesLibrary
        // manages reusable skill templates, ArisEngineClient connects to
        // the desktop Aris instance, and MobilePerceptionService feeds
        // device sensor events into the bus.
        cognitiveBus = CognitiveBus.getInstance()
        metacognition = Metacognition.getInstance()
        psiLoop = PSILoop.getInstance()
        speciesLibrary = CognitiveSpeciesLibrary.getInstance()
        arisEngineClient = ArisEngineClient.getInstance()
        mobilePerceptionService = MobilePerceptionService.getInstance(this)

        // M1: bind the species library to Room so every register/updateUsage
        // persists across process restarts. Hydrate is async — the in-memory
        // cache stays authoritative for the current process and any species
        // registered during the hydrate window survive the eventual upsert.
        CognitiveSpeciesLibrary.init(this)

        // Start the PSI loop with a conservative tick interval (2000ms)
        // suitable for mobile battery constraints. The metacognition
        // layer will dynamically adjust this based on cognitive load.
        psiLoop.tickIntervalMs = 2000L
        // M1:PsiForegroundService — the foreground service owns the PSI
        // lifecycle (start in onCreate, stop in onDestroy) so the loop
        // survives backgrounding. START_STICKY + PsiKeepaliveWorker give
        // us two layers of recovery: system-restart after low-memory
        // kill, and WorkManager re-launch after OEM ROM kill.
        PsiForegroundService.startService(this)

        Log.i("LaapApp", "[OK] LAAP Cognitive Core initialized: CognitiveBus, PSILoop, Metacognition, SpeciesLibrary, ArisEngineClient, MobilePerceptionService")

        // Privacy Mode store + redactor wiring. Mirrors iOS
        // EnvVarPrivacyStore.init / EnvVarRedactor static handoff.
        org.laap.mobile.data.EnvVarPrivacyStore.init(this)
        org.laap.mobile.data.EnvVarRedactor.envVarRepository = envVarRepository

        // Start network monitoring — mirrors iOS NetworkMonitor.shared.start().
        // The monitor writes /etc/resolv.conf immediately and on every
        // ConnectivityManager callback so shells inside the sandbox see fresh
        // DNS servers after Wi-Fi ↔ cellular swaps or VPN toggles.
        networkMonitor.start(this)

        // Register global /var/laap/{memory,skills,shared} bind mounts up-front
        // so direct file I/O tools (file_read) resolve these paths even before
        // PRoot has booted or any shell has started.
        PRootKernel.registerGlobalBindMounts(this)

        // T219-1: load user-mounted external folders and seed PRoot's
        // bindMounts before the first proot invocation, so the very first
        // `shell_execute` already has `/var/laap/mounts/<name>/` visible.
        // Entries whose SAF tree URI didn't resolve to a real POSIX path
        // (cloud providers, unmounted SD card) are silently skipped by
        // bindMountSpecs.
        mountedFoldersStore = MountedFoldersStore(this)
        // T219-5: hand the singleton to PRootKernel so applyMountedFoldersSnapshot
        // can read the live state, and wire an onChange callback so any UI CRUD
        // (add/remove/rename/toggle) re-applies the snapshot.
        // T277: PersistentShell reuses one PRoot process per chat session for the
        // session's lifetime, so an applyMountedFoldersSnapshot call alone never
        // reaches the live shell — proot's `-b` argv is frozen at spawn time.
        // Kill any live shells so the next execute() rebuilds them with the
        // updated bind set. Mount CRUD is a Settings-screen action; the user
        // is not in chat mid-command, so this restart is safe and user-invisible.
        PRootKernel.mountedFoldersStore = mountedFoldersStore
        mountedFoldersStore.onChange = {
            PRootKernel.applyMountedFoldersSnapshot(this)
            ExecutionCoordinator.stopCurrentCommand()
        }
        // T219-6: route launch-time seeding through applyMountedFoldersSnapshot
        // so it (a) reads the live store consistently and (b) materializes the
        // /var/laap/mounts/<name> placeholder dirs that PRoot's `-b` needs.
        // Note: this runs before PRootKernel.boot, so rootfs may not yet exist —
        // applyMountedFoldersSnapshot tolerates that case (mkdirs fails silently
        // and PRootKernel.boot calls applyMountedFoldersSnapshot again at the
        // end of boot to materialize the targets once rootfs is on disk).
        PRootKernel.applyMountedFoldersSnapshot(this)

        // Register native_offload handlers and start the server eagerly —
        // the server only needs the rootfs tmp directory, which can be
        // materialized lazily. Starting here means the abstract socket is
        // reachable even before any shell session is launched.
        NativeOffloadServer.register("android-alarm", AlarmOffloadHandler(this))
        NativeOffloadServer.register("android-calendar", CalendarOffloadHandler(this))
        NativeOffloadServer.register("android-clipboard", ClipboardOffloadHandler(this))
        NativeOffloadServer.register("android-contacts", ContactsOffloadHandler(this))
        NativeOffloadServer.register("android-device", DeviceOffloadHandler(this))
        NativeOffloadServer.register("android-location", LocationOffloadHandler(this))
        NativeOffloadServer.register("android-notification", NotificationOffloadHandler(this))
        NativeOffloadServer.register("android-open", OpenOffloadHandler(this))
        NativeOffloadServer.register("android-photos", PhotosOffloadHandler(this))
        NativeOffloadServer.register("android-player", PlayerOffloadHandler())
        NativeOffloadServer.register("android-speak", SpeakOffloadHandler(this))
        NativeOffloadServer.register("android-speech", SpeechOffloadHandler(this))
        NativeOffloadServer.register("android-weather", WeatherOffloadHandler(this))
        // T323: UI-layer automation backed by LaapAccessibilityService.
        NativeOffloadServer.register("android-a11y-cli", AccessibilityOffloadHandler(this))
        NativeOffloadServer.register("laap-model-use", ModelUseOffloadHandler(this, providerRepository))
        // T-config: laap-config — agent-facing settings management
        // (read/write registered ConfigFields with audit + revert).
        // Mirrors iOS `config_offload_register()` in ISHKernel.m.
        NativeOffloadServer.register(
            "laap-config",
            org.laap.mobile.sandbox.offload.ConfigOffloadHandler(),
        )
        NativeOffloadServer.register("laap-browser-use", BrowserUseOffloadHandler(this))
        // T188: laap-sessions-cli — agent-side query of chat history.
        // Registers next to the other laap-* tools so PRootKernel.
        // installHandlerStubs() picks it up on the next rootfs boot
        // (writes a 17-byte exit-0 stub at /usr/local/bin/laap-sessions-cli
        // so PATH lookup succeeds; PRoot intercepts the execve before
        // the stub runs and routes to this handler).
        NativeOffloadServer.register("laap-sessions-cli", SessionsOffloadHandler(chatRepository))
        // [T-android-scheduled-tasks-full] laap-scheduled — create/list/run
        // timed AI tasks (new chat / follow-up / re-run), mirroring the in-app
        // Scheduled Tasks editor and the iOS Shortcuts intent set.
        NativeOffloadServer.register(
            "laap-scheduled",
            org.laap.mobile.sandbox.offload.ScheduledTaskOffloadHandler(this),
        )
        // T322: android-shizuku-cli — privileged Android control via Shizuku.
        // The handler short-circuits with a typed error envelope when the
        // user hasn't installed / started / authorized Shizuku, so we
        // can register unconditionally; ShizukuManager.init below wires
        // up the binder lifecycle listeners + StateFlow.
        NativeOffloadServer.register("android-shizuku-cli", ShizukuOffloadHandler(this))
        org.laap.mobile.offload.ShizukuManager.init(this)

        // T-android-laap-debug-cli: shell-side CLI wrapper around the in-app
        // DebugServer (127.0.0.1:5321) JSON-RPC. DEBUG-only — Release builds
        // ship neither the DebugServer nor this handler, so the
        // `/usr/local/bin/laap-debug` stub is also absent (PRootKernel.
        // installHandlerStubs enumerates currently-registered handlers).
        if (BuildConfig.DEBUG) {
            NativeOffloadServer.register(
                "laap-debug",
                org.laap.mobile.sandbox.offload.DebugOffloadHandler(this),
            )
        }

        NativeOffloadServer.start(RootfsManager.getInstance(this).rootfsDir)

        // Initialize session activity tracker for foreground service management
        SessionActivityTracker.init(this)

        // [T-android-session-paused-badge] Per-session badge-state queue
        // displayed in the session-list cell corner. Init early so the
        // session list can read persisted PAUSED badges on first compose.
        org.laap.mobile.service.SessionBadgeStore.init(this)

        // [T-android-session-paused-badge-hardkill] Reconcile PAUSED badges
        // against the DB's interrupted-session set. The lifecycle-callback push
        // (onActivityStarted, below) only fires on a graceful background→
        // foreground round-trip; a hard kill (force-quit / process death) never
        // runs it, so the badge would be missing after restart. The persisted
        // message tail is the durable source of truth — scan it off-main and
        // reconcile. Runs after init() so it merges with the restored queues.
        kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO).launch {
            val interrupted = runCatching { chatRepository.interruptedSessionIds() }.getOrElse { emptySet() }
            // Exclude any session that is already actively streaming (defensive;
            // at cold start this is empty, but keeps the rule "active ⇒ never
            // paused" uniform with the foreground reconcile path).
            val active = SessionActivityTracker.activeSessions.value
            org.laap.mobile.service.SessionBadgeStore.reconcileInterruptedSessions(interrupted - active)
        }

        // T180-bg-notif: background-settings + task-completion notifier.
        // The notifier is wired into SessionActivityTracker's completion
        // hook so any session whose stream finishes (success or error)
        // posts a tap-to-open notification when the app is backgrounded.
        // Mirrors iOS BackgroundKeepAliveManager.postBackgroundTaskNotification.
        backgroundSettingsRepository = BackgroundSettingsRepository(this)
        backgroundTaskNotifier = BackgroundTaskNotifier(
            context = this,
            chatRepository = chatRepository,
            backgroundSettings = backgroundSettingsRepository,
            isAppForeground = ::isAppForeground,
        )
        SessionActivityTracker.setCompletionListener { sessionId, isError ->
            backgroundTaskNotifier.notifyTaskCompleted(sessionId, isError)
        }

        // [T-android-config-confirm-timeout] Wire the config-confirm background
        // notifier into the (Context-free) gate, so a laap-config approval that
        // is waiting while the app is backgrounded nudges the user before the
        // 120s timeout. Mirrors iOS ConfigConfirmationGate.notifyIfBackgrounded.
        val configConfirmNotifier = org.laap.mobile.notification.ConfigConfirmNotifier(
            context = this,
            backgroundSettings = backgroundSettingsRepository,
            isAppForeground = ::isAppForeground,
        )
        org.laap.mobile.config.confirm.ConfigConfirmationGate.backgroundNotifier = {
            configConfirmNotifier.notifyIfBackgrounded(it)
        }
        org.laap.mobile.config.confirm.ConfigConfirmationGate.cancelNotification = {
            configConfirmNotifier.cancel(it)
        }

        // Track foreground state via ActivityLifecycleCallbacks. Counting
        // started/stopped balances out around configuration changes (the
        // Activity is briefly destroyed-then-created, so the count would
        // momentarily drop to zero if we used onResume/onPause). Started/
        // stopped is more conservative — counts non-zero while the
        // Activity is even partially visible.
        registerActivityLifecycleCallbacks(object : ActivityLifecycleCallbacks {
            override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {}
            override fun onActivityStarted(activity: Activity) {
                val wasBackgrounded = foregroundActivityCount == 0
                foregroundActivityCount++
                if (wasBackgrounded) _isAppForegroundFlow.value = true
                // T298: as soon as the app transitions background → foreground,
                // clear any task-completed notifications still in the tray.
                // The user is back in front of the app — there's no point
                // making them swipe away a "task completed" entry for the
                // result they're about to look at directly.
                if (wasBackgrounded && ::backgroundTaskNotifier.isInitialized) {
                    backgroundTaskNotifier.cancelAllCompletedNotifications()
                }
                // [T-android-session-paused-badge-hardkill] On foreground,
                // reconcile PAUSED badges from the DB tail (authoritative
                // interrupted-state) instead of the old heuristic that marked
                // every STILL-ACTIVE session paused. That heuristic was wrong:
                // a session still in activeSessions after backgrounding kept
                // RUNNING (keep-alive) — it is executing, not paused — which
                // surfaced a ⏸ badge on a live, spinning session. The DB tail
                // only looks "interrupted" for a session whose loop is actually
                // stranded; we additionally exclude currently-active sessions so
                // a mid-loop running session is never flagged.
                if (wasBackgrounded) {
                    kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO).launch {
                        val interrupted = runCatching { chatRepository.interruptedSessionIds() }.getOrElse { emptySet() }
                        val active = SessionActivityTracker.activeSessions.value
                        org.laap.mobile.service.SessionBadgeStore.reconcileInterruptedSessions(interrupted - active)
                    }
                }
            }
            override fun onActivityResumed(activity: Activity) {
                // T-android-crash-freq-share: if checkAtLaunch flagged a
                // recent burst, show the share-logs dialog on the first
                // Activity that resumes. One-shot — clears the pending
                // list internally so config-change re-resumes don't
                // re-prompt. Safe no-op when nothing is pending.
                org.laap.mobile.crash.CrashFrequencyDetector.maybeShowOnActivity(activity)
                // T219-1: re-probe mounted-folder writability on every
                // foreground resume so OS permission revocations (user
                // toggled "Allow access" off in system Files, removable
                // storage unmounted, etc.) propagate into the UI badge
                // and the read-only enforcement gate. Mirrors iOS
                // MountedFoldersManager.refreshAllWritability().
                kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO).launch {
                    runCatching { mountedFoldersStore.refreshWritability() }
                }
            }
            override fun onActivityPaused(activity: Activity) {}
            override fun onActivityStopped(activity: Activity) {
                foregroundActivityCount = (foregroundActivityCount - 1).coerceAtLeast(0)
                if (foregroundActivityCount == 0) {
                    _isAppForegroundFlow.value = false
                    // [T-android-config-confirm-timeout] The user switched away
                    // while a config-confirm dialog may still be showing — nudge
                    // them so they can come back before the 120s timeout.
                    org.laap.mobile.config.confirm.ConfigConfirmationGate.notifyPending()
                }
            }
            override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) {}
            override fun onActivityDestroyed(activity: Activity) {}
        })

        // Initialize offload permission manager
        OffloadPermissionManager.init(this)

        // Initialize speech-recognition adapter layer (system + provider engines).
        org.laap.mobile.speech.SpeechRecognitionManager.init(this)

        // Refresh model lists once per calendar day (mirrors iOS LaapApp.swift).
        // Runs per-instance in parallel; `autoRefreshModels` skips instances with custom models.
        providerRepository.refreshAllModelsIfNeeded(
            kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO)
        )

        // Propagate system timezone and HTTP-proxy changes into the sandbox.
        // iOS recomputes TZ for every command (ISHShellExecutor.m:335-353);
        // here we update PRootKernel.customEnvironment and push `export …`
        // into every live shell so interactive sessions pick up the change
        // without a restart.
        val sandboxSystemReceiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context, intent: Intent) {
                val scope = kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO)
                when (intent.action) {
                    Intent.ACTION_TIMEZONE_CHANGED -> scope.launch {
                        try {
                            ExecutionCoordinator.broadcastTimezoneChange()
                        } catch (t: Throwable) {
                            Log.w("LaapApp", "broadcastTimezoneChange failed: ${t.message}")
                        }
                    }
                    android.net.Proxy.PROXY_CHANGE_ACTION -> scope.launch {
                        try {
                            ExecutionCoordinator.broadcastProxyChange()
                        } catch (t: Throwable) {
                            Log.w("LaapApp", "broadcastProxyChange failed: ${t.message}")
                        }
                    }
                }
            }
        }
        registerReceiver(
            sandboxSystemReceiver,
            IntentFilter().apply {
                addAction(Intent.ACTION_TIMEZONE_CHANGED)
                addAction(android.net.Proxy.PROXY_CHANGE_ACTION)
            },
        )

        // Debug server: only start in debug builds (NEVER in release)
        if (BuildConfig.DEBUG) {
            try {
                org.laap.mobile.debug.DebugServer(this).start()
            } catch (e: Exception) {
                Log.w("LaapApp", "Failed to start debug server: ${e.message}")
            }
        }

        // T268: one-shot migration of pre-T266 internal alarms into the
        // system Clock app. Pre-T266 builds wrote alarms into LAAP's own
        // SharedPreferences + AlarmManager; T266 retired that path but old
        // installs still have ghost entries that fire only inside LAAP.
        // Replay each future-dated entry through the same SET_ALARM /
        // SET_TIMER intents the new path uses, then clear prefs so the
        // migration runs at most once. Wrapped in runCatching so an
        // unexpected prefs shape never blocks app launch.
        runCatching { migrateGhostAlarms() }
            .onFailure { Log.w("LaapApp", "ghost alarm migration failed: ${it.message}") }
    }

    /**
     * T268: replay any pre-T266 internal alarm/timer entries from
     * laap_alarms_prefs through SET_ALARM / SET_TIMER, then clear the
     * prefs blob so subsequent launches no-op. Past-dated entries are
     * dropped (the OS never re-fires them anyway). Idempotent: if the
     * blob is missing or empty the function returns immediately.
     *
     * Silent migration rather than an in-app dialog — Application has no
     * Activity context to host one, and the user-visible outcome (alarms
     * reappear in their Clock app) is what they want regardless of any
     * prompt. AlarmOffloadManager's PendingIntents are left in place; the
     * OS will fire them once more if scheduled, but T268 also clears the
     * prefs blob that AlarmOffloadHandler previously read, so list/cancel
     * commands will no longer surface them.
     */
    private fun migrateGhostAlarms() {
        val prefs = getSharedPreferences("laap_alarms_prefs", Context.MODE_PRIVATE)
        val raw = prefs.getString("alarms_json", null) ?: return
        if (raw.isBlank() || raw == "[]") return
        val arr = org.json.JSONArray(raw)
        if (arr.length() == 0) {
            prefs.edit().remove("alarms_json").apply()
            return
        }
        val now = System.currentTimeMillis()
        var migrated = 0
        var skipped = 0
        for (i in 0 until arr.length()) {
            val entry = arr.optJSONObject(i) ?: continue
            val triggerAt = entry.optLong("triggerAtMs", 0L)
            if (triggerAt in 1L..now && entry.optString("type") == "timer") {
                skipped++; continue  // Past timer — nothing to recover.
            }
            if (triggerAt in 1L..now && entry.optString("repeatMode", "ONCE") == "ONCE") {
                skipped++; continue  // Past one-shot alarm.
            }
            val migrationOk = runCatching {
                if (entry.optString("type") == "timer") {
                    val secs = entry.optInt("durationSec", -1)
                    val remaining = ((triggerAt - now) / 1000L).toInt()
                    if (remaining <= 0 && secs <= 0) return@runCatching false
                    val intent = android.content.Intent(android.provider.AlarmClock.ACTION_SET_TIMER).apply {
                        putExtra(android.provider.AlarmClock.EXTRA_LENGTH, if (remaining > 0) remaining else secs)
                        putExtra(android.provider.AlarmClock.EXTRA_MESSAGE, entry.optString("label", "Timer"))
                        putExtra(android.provider.AlarmClock.EXTRA_SKIP_UI, true)
                        addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    startActivity(intent)
                    true
                } else {
                    val intent = android.content.Intent(android.provider.AlarmClock.ACTION_SET_ALARM).apply {
                        putExtra(android.provider.AlarmClock.EXTRA_HOUR, entry.optInt("hour", 0))
                        putExtra(android.provider.AlarmClock.EXTRA_MINUTES, entry.optInt("minute", 0))
                        putExtra(android.provider.AlarmClock.EXTRA_MESSAGE, entry.optString("label", "Alarm"))
                        putExtra(android.provider.AlarmClock.EXTRA_SKIP_UI, true)
                        addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    startActivity(intent)
                    true
                }
            }.getOrDefault(false)
            if (migrationOk) migrated++ else skipped++
        }
        // Clear the blob unconditionally — entries we couldn't replay are
        // still useless ghosts, and leaving the blob would re-trigger
        // migration on every launch.
        prefs.edit().remove("alarms_json").apply()
        Log.i("LaapApp", "T268 ghost alarm migration: migrated=$migrated skipped=$skipped (prefs cleared)")
    }

    /**
     * Coil global ImageLoader — registers [LaapImageFetcher] so `laap://`
     * URIs in Markdown images (e.g. `![alt](laap://attachments/x.png)`)
     * resolve to local files under /var/laap/.
     */
    override fun newImageLoader(): ImageLoader =
        ImageLoader.Builder(this)
            .components {
                add(LaapImageFetcher.Factory())
                add(LaapImageFetcher.UriFactory())
                // T-image-cache-mtime-35133: include File.lastModified() in
                // memory + disk cache key so Grok-style in-place rewrites of
                // laap://attachments/foo.jpg invalidate Coil's cached bitmap.
                add(LaapImageFetcher.MtimeKeyer())
                add(LaapImageFetcher.StringMtimeKeyer())
            }
            .build()

    override fun onTerminate() {
        // onTerminate is called only on emulators or when the system
        // explicitly tears down — real devices usually skip it. Still
        // worth marking the beacon: a present clean_exit on a real
        // device proves we shut down voluntarily; its absence is the
        // signal we care about for [LaunchCycleBeacon].
        try {
            org.laap.mobile.diagnostics.LaunchCycleBeacon.recordCleanExit(this)
        } catch (t: Throwable) {
            Log.w("LaapApp", "LaunchCycleBeacon.recordCleanExit failed: ${t.message}")
        }
        super.onTerminate()
    }

}
