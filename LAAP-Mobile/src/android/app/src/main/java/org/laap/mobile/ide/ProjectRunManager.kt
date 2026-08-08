package org.laap.mobile.ide

import android.util.Log
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import org.laap.mobile.data.db.ide.RunConfigEntity
import org.laap.mobile.data.repository.ProjectRepository
import org.laap.mobile.sandbox.ExecutionCoordinator

/**
 * Bridges IDE projects to the existing [ExecutionCoordinator] sandbox.
 *
 * Each project gets a synthetic session id `"project:<projectId>"` so it
 * owns a dedicated [org.laap.mobile.sandbox.PersistentShell] with its own
 * bind mounts, working dir, and per-session mutex. Concurrency:
 * - Different projects run in parallel (different shells).
 * - Same project's runs are serialised by the per-session mutex.
 *
 * Output: each line emitted by the shell is teed into a per-project
 * [MutableSharedFlow] that the Run console collects. We use a SharedFlow
 * (not a StateFlow) because dev-server output is high-volume and we
 * don't want to keep the last N lines in memory indefinitely — late
 * collectors simply miss early lines, which is the expected terminal
 * behaviour. The in-memory ring is bounded by `replay = 0` plus the
 * SharedFlow's internal buffer (default 64).
 */
class ProjectRunManager(
    private val repository: ProjectRepository,
) {

    private val TAG = "ProjectRunManager"

    /** Per-project output stream. Created lazily, never removed. */
    private val flows = mutableMapOf<String, MutableSharedFlow<String>>()

    /** Tracks the run config currently executing per project (for stop semantics). */
    private val activeRunConfig = mutableMapOf<String, String>()

    /**
     * Start a run. If `runConfigId` is null, picks the project's default
     * run config (or the first one if none is flagged default).
     *
     * For `DEV_SERVER` runs the call returns as soon as the shell emits
     * its first output line OR a fixed startup window elapses (the dev
     * server keeps running in the background). For `ONESHOT` / `BUILD`
     * the call blocks until the command finishes and returns the full
     * stdout snapshot.
     *
     * Returns null if the project has no run configs or the requested id
     * doesn't exist.
     */
    suspend fun startRun(
        projectId: String,
        runConfigId: String? = null,
        oneshotTimeoutMs: Long = 60_000L,
        devServerStartupMs: Long = 8_000L,
    ): RunConfigEntity? {
        val config = pickRunConfig(projectId, runConfigId) ?: return null
        val sessionId = ProjectManager.sessionIdFor(projectId)
        val flow = flowFor(projectId)

        activeRunConfig[projectId] = config.id

        // The ExecutionCoordinator per-session mutex serialises concurrent
        // calls with the same sessionId — so we don't need our own lock
        // for "same project already running"; the second call just queues.
        when (config.runType) {
            RUN_TYPE_DEV_SERVER -> {
                // Kick the long-running command and return after the startup
                // window. We do NOT await full completion (vite/flask never exit).
                val result = ExecutionCoordinator.execute(
                    sessionId = sessionId,
                    command = "cd ${ProjectManager.LINUX_PROJECTS_PREFIX}$projectId && ${config.command}",
                    timeout = devServerStartupMs,
                    lineCallback = { line -> flow.tryEmit(line) },
                )
                // The coordinator returns when timeout fires (dev server still up)
                // OR when the process died early (e.g. compile error). Either way
                // surface the trailing summary line.
                if (result.exitCode != 0 && result.exitCode != 124) {
                    flow.tryEmit("(exit ${result.exitCode}) ${result.output.take(200)}")
                }
            }
            RUN_TYPE_ONESHOT, RUN_TYPE_BUILD -> {
                val result = ExecutionCoordinator.execute(
                    sessionId = sessionId,
                    command = "cd ${ProjectManager.LINUX_PROJECTS_PREFIX}$projectId && ${config.command}",
                    timeout = oneshotTimeoutMs,
                    lineCallback = { line -> flow.tryEmit(line) },
                )
                if (result.exitCode != 0) {
                    flow.tryEmit("(exit ${result.exitCode}) ${result.output.take(500)}")
                }
            }
            else -> {
                Log.w(TAG, "Unknown run_type='${config.runType}' for project $projectId")
            }
        }

        activeRunConfig.remove(projectId)
        return config
    }

    /** Kill the project's persistent shell (if any). */
    fun stopRun(projectId: String) {
        ExecutionCoordinator.stopCurrentCommand(sessionId = ProjectManager.sessionIdFor(projectId))
        activeRunConfig.remove(projectId)
        flowFor(projectId).tryEmit("[stopped by user]")
    }

    /** Live output stream for the console UI. */
    fun tailOutput(projectId: String): SharedFlow<String> = flowFor(projectId).asSharedFlow()

    /** Convenience: list run configs for a project (UI dropdown source). */
    suspend fun runConfigsForProject(projectId: String): List<RunConfigEntity> =
        repository.getRunConfigs(projectId)

    /**
     * Non-suspending snapshot of the preview URL — for UI flows that
     * can't await [previewUrl] (e.g. right after [startRun] returned).
     * Returns null when the project isn't running a dev server.
     */
    suspend fun previewUrlNow(projectId: String): String? = previewUrl(projectId)

    /**
     * Preview URL when the project is a running dev server; null otherwise.
     * Format: `http://localhost:<port>`.
     */
    suspend fun previewUrl(projectId: String): String? {
        val config = activeRunConfig[projectId] ?: return null
        val rc = repository.getRunConfig(config) ?: return null
        if (rc.runType != RUN_TYPE_DEV_SERVER) return null
        val port = rc.port ?: return null
        return "http://localhost:$port"
    }

    /** True iff the project currently has a startRun in-flight. */
    fun isRunning(projectId: String): Boolean = activeRunConfig.containsKey(projectId)

    private suspend fun pickRunConfig(projectId: String, runConfigId: String?): RunConfigEntity? {
        if (runConfigId != null) {
            return repository.getRunConfig(runConfigId)?.takeIf { it.projectId == projectId }
        }
        return repository.getDefaultRunConfig(projectId)
            ?: repository.getRunConfigs(projectId).firstOrNull()
    }

    @Synchronized
    private fun flowFor(projectId: String): MutableSharedFlow<String> {
        return flows.getOrPut(projectId) {
            MutableSharedFlow(
                replay = 0,
                extraBufferCapacity = 256,
                onBufferOverflow = kotlinx.coroutines.channels.BufferOverflow.DROP_OLDEST,
            )
        }
    }

    companion object {
        const val RUN_TYPE_DEV_SERVER = "DEV_SERVER"
        const val RUN_TYPE_ONESHOT = "ONESHOT"
        const val RUN_TYPE_BUILD = "BUILD"
    }
}
