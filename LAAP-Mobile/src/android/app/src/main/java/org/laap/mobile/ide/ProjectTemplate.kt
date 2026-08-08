package org.laap.mobile.ide

/**
 * A project template is a static recipe the IDE materialises on disk when
 * the user creates a new project. It carries:
 *
 * - `id`           stable identifier stored on [org.laap.mobile.data.db.ide.ProjectEntity.templateId]
 * - `displayName`  short label shown in the create dialog
 * - `description`  one-line description
 * - `languageId`   language tag consumed by [org.laap.mobile.ui.ide.CodeEditor] for syntax highlight
 * - `files`        relative path → file content (UTF-8). Directories are implied by path separators.
 * - `defaultRun`   optional [RunConfig] pre-registered on project creation
 *
 * MVP keeps templates fully in-code (no remote fetch). Adding a new one
 * is just appending to [ProjectTemplates.ALL].
 */
data class ProjectTemplate(
    val id: String,
    val displayName: String,
    val description: String,
    val languageId: String,
    val files: Map<String, String>,
    val defaultRun: RunConfig? = null,
) {

    /**
     * Run-config recipe attached to a template. `runType` is one of
     * `DEV_SERVER`, `ONESHOT`, `BUILD` — see [org.laap.mobile.data.db.ide.RunConfigEntity].
     */
    data class RunConfig(
        val name: String,
        val command: String,
        val runType: String,
        val port: Int? = null,
        val envJson: String? = null,
        val isDefault: Boolean = true,
    )
}
