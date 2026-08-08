package org.laap.mobile.ui.community

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Public
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.outlined.Gamepad
import androidx.compose.material.icons.outlined.Language
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import org.laap.mobile.ui.ide.IdePreviewScreen
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * LAAP Community — browse, play and publish user-generated apps.
 *
 * Connects to the desktop Community Server (`http://<desktop-ip>:8790`) and:
 *   - lists published web apps / websites / games;
 *   - opens any app in an in-app WebView (play / 品鉴);
 *   - publishes a new app either as an external link or by uploading a zip
 *     of its built web assets.
 *
 * The server URL is remembered in SharedPreferences so a phone can reconnect
 * across sessions without re-typing the desktop's LAN IP.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CommunityScreen(
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val prefs = remember { context.getSharedPreferences("community", Context.MODE_PRIVATE) }

    var serverRoot by remember { mutableStateOf(prefs.getString("server", "http://localhost:8790") ?: "http://localhost:8790") }
    var draftServer by remember { mutableStateOf(serverRoot) }
    var apps by remember { mutableStateOf<List<CommunityApi.CommunityApp>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var showServerDialog by remember { mutableStateOf(false) }
    var showPublishDialog by remember { mutableStateOf(false) }
    var playUrl by remember { mutableStateOf<String?>(null) }
    var pendingDelete by remember { mutableStateOf<CommunityApi.CommunityApp?>(null) }
    var refreshing by remember { mutableStateOf(false) }

    fun load() {
        scope.launch {
            refreshing = true
            val result = CommunityApi.listApps(serverRoot)
            refreshing = false
            result.onSuccess { apps = it; error = null }
                .onFailure { error = it.message ?: "无法连接服务器" }
        }
    }

    LaunchedEffect(serverRoot) { load() }

    if (playUrl != null) {
        IdePreviewScreen(url = playUrl!!, onBack = { playUrl = null })
        return
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("LAAP 社区", fontWeight = FontWeight.SemiBold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { showServerDialog = true }) {
                        Icon(Icons.Filled.Cloud, contentDescription = "服务器设置")
                    }
                    IconButton(onClick = { load() }) {
                        Icon(Icons.Filled.Refresh, contentDescription = "刷新")
                    }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showPublishDialog = true }) {
                Icon(Icons.Filled.Add, contentDescription = "发布应用")
            }
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            Text(
                "服务器：$serverRoot",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
            )
            error?.let {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                ) {
                    Icon(Icons.Filled.Info, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                    Spacer(Modifier.width(8.dp))
                    Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }
            }
            when {
                refreshing && apps == null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                apps.isNullOrEmpty() -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Filled.Public, contentDescription = null, modifier = Modifier.size(56.dp))
                        Text("社区还是空的", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 12.dp))
                        Text("点 + 发布你的第一个应用", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
                else -> LazyColumn(Modifier.fillMaxSize()) {
                    items(apps.orEmpty(), key = { it.id }) { app ->
                        CommunityAppRow(
                            app = app,
                            onOpen = { playUrl = CommunityApi.absoluteUrl(serverRoot, app.url) },
                            onDelete = { pendingDelete = app },
                        )
                    }
                }
            }
        }
    }

    if (showServerDialog) {
        ServerDialog(
            current = serverRoot,
            onDismiss = { showServerDialog = false },
            onConfirm = {
                showServerDialog = false
                serverRoot = draftServer.trim().trimEnd('/').ifBlank { "http://localhost:8790" }
                prefs.edit().putString("server", serverRoot).apply()
            },
            draft = draftServer,
            onDraftChange = { draftServer = it },
        )
    }

    if (showPublishDialog) {
        PublishDialog(
            onDismiss = { showPublishDialog = false },
            onPublishLink = { name, desc, type, author, url ->
                showPublishDialog = false
                scope.launch {
                    val r = CommunityApi.publishLink(serverRoot, name, desc, type, author, url)
                    if (r.isSuccess) load()
                }
            },
            onPublishZip = { file, name, desc, type, author ->
                showPublishDialog = false
                scope.launch {
                    val r = CommunityApi.publishZip(serverRoot, file, name, desc, type, author)
                    if (r.isSuccess) load()
                }
            },
        )
    }

    pendingDelete?.let { target ->
        AlertDialog(
            onDismissRequest = { pendingDelete = null },
            title = { Text("删除应用？") },
            text = { Text("删除「${target.name}」？") },
            confirmButton = {
                TextButton(onClick = {
                    pendingDelete = null
                    scope.launch {
                        runCatching {
                            okhttp3.OkHttpClient().newCall(
                                okhttp3.Request.Builder()
                                    .url(serverRoot.trimEnd('/') + "/api/apps/" + target.id)
                                    .delete()
                                    .build()
                            ).execute().close()
                        }
                        load()
                    }
                }) { Text("删除") }
            },
            dismissButton = { TextButton(onClick = { pendingDelete = null }) { Text("取消") } },
        )
    }
}

@Composable
private fun CommunityAppRow(
    app: CommunityApi.CommunityApp,
    onOpen: () -> Unit,
    onDelete: () -> Unit,
) {
    val typeIcon = when (app.type) {
        "game" -> Icons.Outlined.Gamepad
        "website" -> Icons.Outlined.Language
        else -> Icons.Outlined.Language
    }
    ListItem(
        leadingContent = {
            Icon(typeIcon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        },
        headlineContent = {
            Text(app.name, fontWeight = FontWeight.SemiBold)
        },
        supportingContent = {
            Column {
                if (app.description.isNotBlank()) Text(app.description, style = MaterialTheme.typography.bodySmall)
                Text(
                    "${typeLabel(app.type)} · ${app.author} · ${app.downloads} 次下载 · ${timeAgo(app.createdAt)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        },
        trailingContent = {
            IconButton(onClick = onDelete) {
                Icon(Icons.Filled.Delete, contentDescription = "删除")
            }
        },
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onOpen),
    )
}

@Composable
private fun ServerDialog(
    current: String,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
    draft: String,
    onDraftChange: (String) -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("社区服务器") },
        text = {
            Column {
                Text(
                    "手机通过局域网连接桌面端社区服务器。默认 localhost（模拟器）。真机请改为桌面电脑的局域网 IP，例如 http://192.168.1.100:8790",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = draft,
                    onValueChange = onDraftChange,
                    label = { Text("服务器地址") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = { TextButton(onClick = onConfirm) { Text("保存") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("取消") } },
    )
}

@Composable
private fun PublishDialog(
    onDismiss: () -> Unit,
    onPublishLink: (name: String, desc: String, type: String, author: String, url: String) -> Unit,
    onPublishZip: (file: java.io.File, name: String, desc: String, type: String, author: String) -> Unit,
) {
    val context = LocalContext.current
    var name by remember { mutableStateOf("") }
    var desc by remember { mutableStateOf("") }
    var type by remember { mutableStateOf("web") }
    var author by remember { mutableStateOf("") }
    var url by remember { mutableStateOf("") }
    var zipText by remember { mutableStateOf("未选择 .zip 文件") }

    val zipLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri == null) return@rememberLauncherForActivityResult
        zipText = "已选择：$uri"
        onPublishZipWithUri(context, uri, name, desc, type, author, onPublishZip)
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("发布到社区") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                OutlinedTextField(
                    value = name, onValueChange = { name = it },
                    label = { Text("名称") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = desc, onValueChange = { desc = it },
                    label = { Text("描述") }, modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TypeChip("web", "网页应用", type) { type = it }
                    TypeChip("website", "网站", type) { type = it }
                    TypeChip("game", "游戏", type) { type = it }
                }
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = author, onValueChange = { author = it },
                    label = { Text("作者") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(16.dp))
                Text("方式一：外部链接", style = MaterialTheme.typography.titleSmall)
                OutlinedTextField(
                    value = url, onValueChange = { url = it },
                    label = { Text("应用的 URL (http/https)") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = { onPublishLink(name, desc, type, author, url) },
                    enabled = name.isNotBlank() && url.startsWith("http"),
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                ) { Text("发布链接") }
                Spacer(Modifier.height(16.dp))
                Text("方式二：上传 zip（构建好的网页资源）", style = MaterialTheme.typography.titleSmall)
                OutlinedButton(onClick = { zipLauncher.launch(arrayOf("application/zip")) }, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Text("选择 .zip 文件")
                }
                Text(zipText, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        },
        confirmButton = { TextButton(onClick = onDismiss) { Text("关闭") } },
    )
}

@Composable
private fun TypeChip(label: String, text: String, current: String, onSelect: (String) -> Unit) {
    val selected = current == label
    OutlinedButton(onClick = { onSelect(label) }) {
        Text(text, color = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

private fun onPublishZipWithUri(
    context: Context,
    uri: Uri,
    name: String,
    desc: String,
    type: String,
    author: String,
    onPublishZip: (java.io.File, String, String, String, String) -> Unit,
) {
    val tmp = java.io.File(context.cacheDir, "community-upload.zip")
    context.contentResolver.openInputStream(uri)?.use { input ->
        tmp.outputStream().use { output -> input.copyTo(output) }
    }
    onPublishZip(tmp, name, desc, type, author)
}

private fun typeLabel(type: String) = when (type) {
    "game" -> "游戏"
    "website" -> "网站"
    else -> "网页应用"
}

private fun timeAgo(ts: Long): String {
    if (ts <= 0) return ""
    val diff = System.currentTimeMillis() - ts
    val min = diff / 60000
    return when {
        min < 1 -> "刚刚"
        min < 60 -> "$min 分钟前"
        min < 1440 -> "${min / 60} 小时前"
        else -> SimpleDateFormat("MMM d", Locale.getDefault()).format(Date(ts))
    }
}