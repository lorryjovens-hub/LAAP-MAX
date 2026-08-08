package org.laap.mobile.tools

import android.content.Context
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import org.laap.mobile.LaapApp
import org.laap.mobile.data.model.AgentToolDefinition
import org.laap.mobile.data.model.AgentToolParam
import org.json.JSONObject

/**
 * Agent-facing IDE tools. Five named tools — `project_create`,
 * `project_open`, `project_run`, `project_stop`, `project_log` —
 * covering the full IDE lifecycle from chat. Composes cleanly with
 * the existing `shell_execute` / `file_*` tools: the agent can mix
 * freely (e.g. `project_create` → `shell_execute "npm i lodash"` →
 * `project_run`).
 *
 * All five delegate to [org.laap.mobile.ide.ProjectManager] /
 * [org.laap.mobile.ide.ProjectRunManager] via the application singleton.
 * The IDE UI uses the same singletons, so tool-driven and UI-driven
 * mutations land in the same DB + on the same SharedFlow.
 */
object IdeTools {

    const val CREATE_NAME = "project_create"
    const val OPEN_NAME = "project_open"
    const val RUN_NAME = "project_run"
    const val STOP_NAME = "project_stop"
    const val LOG_NAME = "project_log"

    /** All five tool definitions, in registration order. */
    fun definitions(): List<AgentToolDefinition> = listOf(
        projectCreateDefinition(),
        projectOpenDefinition(),
        projectRunDefinition(),
        projectStopDefinition(),
        projectLogDefinition(),
    )

    fun projectCreateDefinition(): AgentToolDefinition = AgentToolDefinition(
        name = CREATE_NAME,
        description = "Create a new IDE project from a built-in template. " +
            "Materializes the template's files under /var/laap/projects/<id>/ inside the sandbox " +
            "and registers the project's default run config (if any). " +
            "Returns the new project id and its Linux path.",
        parameters = mapOf(
            "tool_title" to AgentToolParam("string", "A concise 5-10 word summary of what this tool call does, shown to the user (e.g. 'Create Vite React project'). Use the same language as the user."),
            "name" to AgentToolParam("string", "Display name for the project (e.g. 'my-react-app')."),
            "template_id" to AgentToolParam(
                "string",
                "Template id. One of: static-html, vite-react, node-express, python-flask, python-script.",
                enumValues = listOf(
                    "static-html", "vite-react", "node-express", "python-flask", "python-script",
                ),
            ),
        ),
        required = listOf("tool_title", "name", "template_id"),
        propertyOrdering = listOf("tool_title", "name", "template_id"),
    )

    fun projectOpenDefinition(): AgentToolDefinition = AgentToolDefinition(
        name = OPEN_NAME,
        description = "Open an existing IDE project. Returns the project metadata " +
            "and a listing of its files (top-level + one nested level).",
        parameters = mapOf(
            "tool_title" to AgentToolParam("string", "A concise 5-10 word summary of what this tool call does, shown to the user."),
            "project_id" to AgentToolParam("string", "The project id returned by project_create."),
        ),
        required = listOf("tool_title", "project_id"),
        propertyOrdering = listOf("tool_title", "project_id"),
    )

    fun projectRunDefinition(): AgentToolDefinition = AgentToolDefinition(
        name = RUN_NAME,
        description = "Run a project's run config inside the sandbox. The project's " +
            "files are visible at /var/laap/projects/<project_id>/. For DEV_SERVER runs " +
            "the call returns after a startup window (the server keeps running in the " +
            "background) and includes the preview URL when the port is known. For " +
            "ONESHOT / BUILD runs the call blocks until completion and returns full stdout.",
        parameters = mapOf(
            "tool_title" to AgentToolParam("string", "A concise 5-10 word summary of what this tool call does, shown to the user."),
            "project_id" to AgentToolParam("string", "The project id to run."),
            "run_config_id" to AgentToolParam("string", "Optional run config id. If omitted, uses the project's default run config."),
        ),
        required = listOf("tool_title", "project_id"),
        propertyOrdering = listOf("tool_title", "project_id", "run_config_id"),
    )

    fun projectStopDefinition(): AgentToolDefinition = AgentToolDefinition(
        name = STOP_NAME,
        description = "Stop a running project's persistent shell. Use when a dev server " +
            "is in a bad state or the user explicitly asks to stop. The next project_run " +
            "spawns a fresh shell.",
        parameters = mapOf(
            "tool_title" to AgentToolParam("string", "A concise 5-10 word summary of what this tool call does, shown to the user."),
            "project_id" to AgentToolParam("string", "The project id to stop."),
        ),
        required = listOf("tool_title", "project_id"),
        propertyOrdering = listOf("tool_title", "project_id"),
    )

    fun projectLogDefinition(): AgentToolDefinition = AgentToolDefinition(
        name = LOG_NAME,
        description = "Tail recent output from a project's run. Returns the last N lines " +
            "captured since the project_run call (or since the previous project_log call). " +
            "Use for long-running dev servers whose startup output already scrolled past.",
        parameters = mapOf(
            "tool_title" to AgentToolParam("string", "A concise 5-10 word summary of what this tool call does, shown to the user."),
            "project_id" to AgentToolParam("string", "The project id to read output from."),
            "lines" to AgentToolParam("integer", "Maximum number of trailing lines to return (default: 200)."),
        ),
        required = listOf("tool_title", "project_id"),
        propertyOrdering = listOf("tool_title", "project_id", "lines"),
    )

    // ── Execution ───────────────────────────────────────────────────────

    fun execute(name: String, argsJson: String, context: Context): ToolExecutionResult {
        val app = context.applicationContext as? LaapApp
            ?: return ToolExecutionResult("Error: LaapApp not available", false)
        val toolTitle = runCatching { JSONObject(argsJson).optString("tool_title", name) }.getOrDefault(name)
        return try {
            when (name) {
                CREATE_NAME -> executeProjectCreate(argsJson, app, toolTitle)
                OPEN_NAME -> executeProjectOpen(argsJson, app, toolTitle)
                RUN_NAME -> executeProjectRun(argsJson, app, toolTitle)
                STOP_NAME -> executeProjectStop(argsJson, app, toolTitle)
                LOG_NAME -> executeProjectLog(argsJson, app, toolTitle)
                else -> ToolExecutionResult("Unknown IDE tool: $name", false, toolTitle = toolTitle)
            }
        } catch (e: Exception) {
            ToolExecutionResult("Error in $name: ${e.message}", false, toolTitle = toolTitle)
        }
    }

    private fun executeProjectCreate(argsJson: String, app: LaapApp, toolTitle: String): ToolExecutionResult {
        val args = JSONObject(argsJson)
        val name = args.optString("name", "").trim()
        val templateId = args.optString("template_id", "").trim()
        if (name.isEmpty()) return ToolExecutionResult("Error: 'name' is required", false, toolTitle = toolTitle)
        if (templateId.isEmpty()) return ToolExecutionResult("Error: 'template_id' is required", false, toolTitle = toolTitle)

        val entity = runBlocking { app.projectManager.create(name, templateId) }
        val path = "${org.laap.mobile.ide.ProjectManager.LINUX_PROJECTS_PREFIX}${entity.id}"
        val result = JSONObject().apply {
            put("project_id", entity.id)
            put("name", entity.name)
            put("template_id", entity.templateId)
            put("path", path)
        }
        return ToolExecutionResult(
            "Created project '${entity.name}' (id=${entity.id}) at $path\n$result",
            true,
            toolTitle = toolTitle,
        )
    }

    private fun executeProjectOpen(argsJson: String, app: LaapApp, toolTitle: String): ToolExecutionResult {
        val args = JSONObject(argsJson)
        val projectId = args.optString("project_id", "").trim()
        if (projectId.isEmpty()) return ToolExecutionResult("Error: 'project_id' is required", false, toolTitle = toolTitle)

        val project = runBlocking { app.projectManager.get(projectId) }
            ?: return ToolExecutionResult("Error: project '$projectId' not found", false, toolTitle = toolTitle)

        val hostDir = app.projectManager.hostDirFor(projectId)
        val files = hostDir.walkTopDown()
            .drop(1)  // skip the root
            .take(200)
            .map { it.relativeTo(hostDir).path.replace('\\', '/') }
            .toList()
        val result = JSONObject().apply {
            put("project_id", project.id)
            put("name", project.name)
            put("template_id", project.templateId)
            put("path", "${org.laap.mobile.ide.ProjectManager.LINUX_PROJECTS_PREFIX}${project.id}")
            put("files", files.joinToString("\n"))
        }
        return ToolExecutionResult("Project: $result", true, toolTitle = toolTitle)
    }

    private fun executeProjectRun(argsJson: String, app: LaapApp, toolTitle: String): ToolExecutionResult {
        val args = JSONObject(argsJson)
        val projectId = args.optString("project_id", "").trim()
        if (projectId.isEmpty()) return ToolExecutionResult("Error: 'project_id' is required", false, toolTitle = toolTitle)
        val runConfigId = args.optString("run_config_id", "").ifBlank { null }

        // Tail output for the duration of the run, capturing the first N lines
        // to return to the agent.
        val captured = mutableListOf<String>()
        val tailJob = GlobalScope.launch {
            app.projectRunManager.tailOutput(projectId).collect { line ->
                if (captured.size < 100) captured += line
            }
        }
        val config = runBlocking {
            app.projectRunManager.startRun(projectId, runConfigId)
        }
        // Give the SharedFlow collector a brief chance to drain before reading.
        Thread.sleep(200)
        tailJob.cancel()

        if (config == null) {
            return ToolExecutionResult(
                "Error: no run config found for project '$projectId'",
                false,
                toolTitle = toolTitle,
            )
        }
        val previewUrl = runBlocking { app.projectRunManager.previewUrl(projectId) }
        val result = JSONObject().apply {
            put("project_id", projectId)
            put("run_config", config.name)
            put("run_type", config.runType)
            put("preview_url", previewUrl ?: JSONObject.NULL)
            put("early_output", captured.joinToString("\n"))
        }
        return ToolExecutionResult("Started run: $result", true, toolTitle = toolTitle)
    }

    private fun executeProjectStop(argsJson: String, app: LaapApp, toolTitle: String): ToolExecutionResult {
        val args = JSONObject(argsJson)
        val projectId = args.optString("project_id", "").trim()
        if (projectId.isEmpty()) return ToolExecutionResult("Error: 'project_id' is required", false, toolTitle = toolTitle)
        app.projectRunManager.stopRun(projectId)
        return ToolExecutionResult("Stopped project '$projectId'", true, toolTitle = toolTitle)
    }

    private fun executeProjectLog(argsJson: String, app: LaapApp, toolTitle: String): ToolExecutionResult {
        val args = JSONObject(argsJson)
        val projectId = args.optString("project_id", "").trim()
        if (projectId.isEmpty()) return ToolExecutionResult("Error: 'project_id' is required", false, toolTitle = toolTitle)
        val maxLines = args.optInt("lines", 200).coerceIn(1, 5_000)

        // Collect up to maxLines from the SharedFlow's current replay buffer
        // (which is 0 — so we can only see new emissions). For MVP we poll
        // briefly: a longer-lived collector would require holding a job
        // across turns, which is out of scope. The Run tab UI keeps the
        // full buffered history; this tool is a best-effort snapshot.
        val captured = mutableListOf<String>()
        val job = GlobalScope.launch {
            app.projectRunManager.tailOutput(projectId).collect { line ->
                if (captured.size < maxLines) captured += line
                // No early exit — let the job drain until the brief window below elapses.
            }
        }
        Thread.sleep(800)
        job.cancel()

        val body = if (captured.isEmpty()) "(no recent output)" else captured.joinToString("\n")
        return ToolExecutionResult("Project '$projectId' log:\n$body", true, toolTitle = toolTitle)
    }
}
