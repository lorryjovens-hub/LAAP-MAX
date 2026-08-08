package org.laap.mobile.ui.ide

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.InsertDriveFile
import androidx.compose.material.icons.filled.OpenInBrowser
import androidx.compose.material.icons.filled.PhoneAndroid
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.AssistChip
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import org.laap.mobile.LaapApp
import org.laap.mobile.ui.terminal.JetBrainsMonoFontFamily

/**
 * Three-tab workspace: Files / Editor / Run.
 *
 * - Files: depth-1 listing of the project dir, tap to open in editor.
 * - Editor: [CodeEditor] with Save button. Title shows the open file's
 *   relative path.
 * - Run: run-config picker + Start/Stop + live console + preview chip.
 *
 * The Run tab's preview chip launches the existing WebPreviewFullscreenScreen
 * when `previewUrl != null` (i.e. dev server is up). Static HTML projects
 * (no run config) bypass the Run tab and the preview chip wires to a
 * `laap://` resource URL pointing at the project's index.html.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProjectWorkspaceScreen(
    projectId: String,
    onBack: () -> Unit,
    onOpenPreview: (url: String) -> Unit,
    onExportApk: () -> Unit = {},
) {
    val app = LocalContext.current.applicationContext as LaapApp
    val vm: ProjectWorkspaceViewModel = viewModel(
        factory = ProjectWorkspaceViewModel.factory(
            projectId, app, app.projectManager, app.projectRunManager,
        ),
    )
    val project by vm.project.collectAsState()
    val filesState by vm.files.collectAsState()
    val editorState by vm.editor.collectAsState()
    val runState by vm.run.collectAsState()

    var tab by remember { mutableStateOf(0) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(project?.name ?: "Loading…", fontWeight = FontWeight.SemiBold)
                        if (editorState.openFile != null && tab == 1) {
                            Text(
                                editorState.openFile!!,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    if (tab == 1 && editorState.openFile != null) {
                        IconButton(onClick = { vm.saveOpenFile() }, enabled = editorState.isDirty) {
                            Icon(Icons.Filled.Save, contentDescription = "Save")
                        }
                    }
                    if (tab == 0) {
                        IconButton(onClick = { vm.refreshFiles() }) {
                            Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                        }
                    }
                    IconButton(onClick = onExportApk) {
                        Icon(Icons.Filled.PhoneAndroid, contentDescription = "Export APK")
                    }
                },
            )
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            TabRow(selectedTabIndex = tab) {
                Tab(selected = tab == 0, onClick = { tab = 0 }, text = { Text("Files") })
                Tab(selected = tab == 1, onClick = { tab = 1 }, text = { Text("Editor") })
                Tab(selected = tab == 2, onClick = { tab = 2 }, text = { Text("Run") })
            }
            when (tab) {
                0 -> FilesTab(
                    state = filesState,
                    onOpenFile = { rel ->
                        vm.openFile(rel)
                        tab = 1
                    },
                )
                1 -> EditorTab(
                    state = editorState,
                    onContentChange = vm::updateContent,
                    onSave = vm::saveOpenFile,
                )
                2 -> RunTab(
                    state = runState,
                    onSelectConfig = vm::selectRunConfig,
                    onStart = vm::startRun,
                    onStop = vm::stopRun,
                    onOpenPreview = onOpenPreview,
                )
            }
        }
    }
}

@Composable
private fun FilesTab(
    state: FilesTabState,
    onOpenFile: (String) -> Unit,
) {
    if (state.isLoading) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Loading…")
        }
        return
    }
    if (state.entries.isEmpty()) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("No files")
        }
        return
    }
    LazyColumn(Modifier.fillMaxSize()) {
        items(state.entries, key = { it.relativePath }) { entry ->
            ListItem(
                leadingContent = {
                    Icon(
                        if (entry.isDirectory) Icons.Filled.Folder else Icons.Filled.InsertDriveFile,
                        contentDescription = null,
                        tint = if (entry.isDirectory) MaterialTheme.colorScheme.primary
                               else MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                },
                headlineContent = { Text(entry.name) },
                supportingContent = if (!entry.isDirectory) {
                    { Text(humanBytes(entry.size), style = MaterialTheme.typography.bodySmall) }
                } else null,
                modifier = Modifier.clickable { onOpenFile(entry.relativePath) },
            )
            HorizontalDivider()
        }
    }
}

@Composable
private fun EditorTab(
    state: EditorTabState,
    onContentChange: (String) -> Unit,
    onSave: () -> Unit,
) {
    if (state.openFile == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Open a file from the Files tab")
        }
        return
    }
    CodeEditor(
        code = state.content,
        onCodeChange = onContentChange,
        languageId = state.languageId,
        modifier = Modifier.fillMaxSize(),
    )
}

@Composable
private fun RunTab(
    state: RunTabState,
    onSelectConfig: (String) -> Unit,
    onStart: () -> Unit,
    onStop: () -> Unit,
    onOpenPreview: (String) -> Unit,
) {
    Column(Modifier.fillMaxSize().padding(12.dp)) {
        if (state.runConfigs.isEmpty()) {
            Text(
                "This project has no run configurations. Static HTML projects are previewed directly — use the Files tab to open index.html.",
                style = MaterialTheme.typography.bodyMedium,
            )
            Spacer(Modifier.height(12.dp))
            // Static HTML fallback: surface a preview chip pointing at the
            // project root + "index.html" via the laap:// scheme.
            OutlinedButton(onClick = { onOpenPreview("laap://projects/index.html") }) {
                Icon(Icons.Filled.OpenInBrowser, contentDescription = null)
                Spacer(Modifier.size(8.dp))
                Text("Open Preview")
            }
        } else {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Config:", style = MaterialTheme.typography.labelLarge)
                Spacer(Modifier.size(8.dp))
                ConfigPicker(
                    configs = state.runConfigs,
                    selectedId = state.selectedConfigId,
                    onSelect = onSelectConfig,
                )
            }
            Spacer(Modifier.height(12.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (state.isRunning) {
                    OutlinedButton(onClick = onStop) {
                        Icon(Icons.Filled.Stop, contentDescription = null)
                        Spacer(Modifier.size(8.dp))
                        Text("Stop")
                    }
                } else {
                    OutlinedButton(onClick = onStart) {
                        Icon(Icons.Filled.PlayArrow, contentDescription = null)
                        Spacer(Modifier.size(8.dp))
                        Text("Start")
                    }
                }
                Spacer(Modifier.size(12.dp))
                if (state.previewUrl != null) {
                    AssistChip(
                        onClick = { onOpenPreview(state.previewUrl) },
                        label = { Text("Open Preview") },
                        leadingIcon = { Icon(Icons.Filled.OpenInBrowser, contentDescription = null) },
                    )
                }
            }
            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(8.dp))
            ConsoleOutput(state.outputLines)
        }
    }
}

@Composable
private fun ConsoleOutput(lines: List<String>) {
    val listState = rememberLazyListState()
    LaunchedEffect(lines.size) {
        if (lines.isNotEmpty()) listState.animateScrollToItem(lines.size - 1)
    }
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
            .padding(8.dp),
        state = listState,
    ) {
        items(lines) { line ->
            Text(
                line,
                fontFamily = JetBrainsMonoFontFamily,
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.fillMaxWidth(),
            )
        }
        if (lines.isEmpty()) {
            item { Text("Console output will appear here.", style = MaterialTheme.typography.bodySmall) }
        }
    }
}

@Composable
private fun ConfigPicker(
    configs: List<org.laap.mobile.data.db.ide.RunConfigEntity>,
    selectedId: String?,
    onSelect: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val selected = configs.firstOrNull { it.id == selectedId }
    Box {
        OutlinedButton(onClick = { expanded = true }) {
            Text(selected?.name ?: "Pick config")
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            configs.forEach { c ->
                DropdownMenuItem(
                    text = { Text(c.name) },
                    onClick = {
                        onSelect(c.id)
                        expanded = false
                    },
                )
            }
        }
    }
}

private fun humanBytes(bytes: Long): String = when {
    bytes < 1024 -> "${bytes} B"
    bytes < 1024 * 1024 -> "%.1f KB".format(bytes / 1024.0)
    else -> "%.1f MB".format(bytes / (1024.0 * 1024.0))
}
