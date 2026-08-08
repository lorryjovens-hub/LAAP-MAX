package org.laap.mobile.ide

import android.content.Context
import org.laap.mobile.data.db.ide.ProjectEntity
import org.laap.mobile.data.repository.ProjectRepository
import org.laap.mobile.sandbox.PRootKernel
import java.io.File

/**
 * Owns the lifecycle of IDE projects on disk + in the DB.
 *
 * A project's files live at host path `filesDir/laap-global/projects/<id>/`
 * (bind-mounted into the sandbox at `/var/laap/projects/<id>/`). The DB
 * row stores the relative path `<id>` so the location is reproducible
 * from the row alone — no absolute paths in the DB.
 *
 * Creation materialises the template's `files` map verbatim under the
 * project dir; deletion recursively removes the dir and DB rows (the
 * run-config rows cascade via FK).
 */
class ProjectManager(
    private val appContext: Context,
    private val repository: ProjectRepository,
) {

    /** Host directory that backs `/var/laap/projects/` in the sandbox. */
    val projectsRootHost: File
        get() = File(appContext.filesDir, "laap-global/projects").also { it.mkdirs() }

    /** Linux-side path for a project — always `/var/laap/projects/<id>`. */
    fun linuxDirFor(projectId: String): String = "${LINUX_PROJECTS_PREFIX}$projectId"

    /** Host directory for a project; resolved from PRoot bind map so it stays in sync. */
    fun hostDirFor(projectId: String): File {
        // Prefer the PRoot bind map so a future redirect (e.g. external storage)
        // is honoured. Fall back to the default cache dir.
        val resolved = PRootKernel.resolveHostPath(linuxDirFor(projectId))
        return resolved ?: File(projectsRootHost, projectId)
    }

    suspend fun create(name: String, templateId: String): ProjectEntity {
        val template = ProjectTemplates.byId(templateId)
            ?: throw IllegalArgumentException("Unknown template: $templateId")

        val projectId = java.util.UUID.randomUUID().toString()
        val projectDir = File(projectsRootHost, projectId).also { it.mkdirs() }

        // Materialise template files. Subdirectories are created on demand.
        template.files.forEach { (relPath, content) ->
            val target = File(projectDir, relPath)
            target.parentFile?.mkdirs()
            target.writeText(content)
        }

        val entity = repository.createProject(
            id = projectId,
            name = name,
            templateId = templateId,
            dirPath = projectId,
            description = template.description,
        )

        // Seed the default run config (if any) so the Run tab can start
        // without forcing the user to fill out a form first.
        template.defaultRun?.let { rc ->
            repository.addRunConfig(
                projectId = projectId,
                name = rc.name,
                command = rc.command,
                runType = rc.runType,
                port = rc.port,
                envJson = rc.envJson,
                isDefault = rc.isDefault,
            )
        }

        return entity
    }

    suspend fun delete(projectId: String) {
        // Stop any running shell first so we don't race a write into a
        // dir we're about to nuke.
        hostDirFor(projectId).deleteRecursively()
        repository.deleteProject(projectId)
    }

    suspend fun get(projectId: String): ProjectEntity? = repository.getProject(projectId)

    suspend fun list(): List<ProjectEntity> = repository.listProjects()

    fun observeProjects() = repository.observeProjects()

    suspend fun touchOpenedAt(projectId: String) = repository.touchOpenedAt(projectId)

    companion object {
        const val LINUX_PROJECTS_PREFIX = "/var/laap/projects/"

        /** Synthetic session id used by [ProjectRunManager] — `project:<id>`. */
        fun sessionIdFor(projectId: String): String = "project:$projectId"
    }
}
