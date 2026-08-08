package org.laap.mobile.ui.ide

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import org.laap.mobile.ide.ProjectTemplate
import org.laap.mobile.ide.ProjectTemplates

/**
 * "New Project" dialog: free-text name + one of [ProjectTemplates.ALL]
 * as the seed template. Creation is delegated to the parent — the dialog
 * just collects the form state and calls `onConfirm(name, templateId)`.
 *
 * The template picker uses [FilterChip] rather than radio buttons: the
 * template set is small (5 today), each has a short description, and the
 * chip row reads better on a phone than a vertical radio list.
 */
@Composable
fun CreateProjectDialog(
    onDismiss: () -> Unit,
    onConfirm: (name: String, templateId: String) -> Unit,
) {
    var name by remember { mutableStateOf("") }
    var selectedTemplate by remember { mutableStateOf(ProjectTemplates.ALL.first()) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Project") },
        text = {
            Column {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Project name") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(16.dp))
                Text(
                    "Template",
                    style = MaterialTheme.typography.labelLarge,
                )
                Spacer(Modifier.height(8.dp))
                ProjectTemplates.ALL.forEach { template ->
                    TemplateRow(
                        template = template,
                        selected = template.id == selectedTemplate.id,
                        onSelect = { selectedTemplate = it },
                    )
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(name.trim(), selectedTemplate.id) },
                enabled = name.trim().isNotEmpty(),
            ) { Text("Create") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        },
    )
}

@Composable
private fun TemplateRow(
    template: ProjectTemplate,
    selected: Boolean,
    onSelect: (ProjectTemplate) -> Unit,
) {
    Surface(
        shape = RoundedCornerShape(8.dp),
        color = if (selected) {
            MaterialTheme.colorScheme.primaryContainer
        } else {
            MaterialTheme.colorScheme.surface
        },
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .selectable(selected = selected, onClick = { onSelect(template) }),
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(12.dp),
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(template.displayName, fontWeight = FontWeight.SemiBold)
                Text(
                    template.description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
