package org.laap.mobile.ui.ide

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
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
import org.laap.mobile.LaapApp
import org.laap.mobile.ide.ApkProjectGenerator
import org.laap.mobile.logging.AppLogger
import java.io.File
import java.util.Locale

/**
 * "Export independent APK" screen for an IDE project.
 *
 * The user picks the runtime permissions the exported app needs, then taps
 * Export. The screen generates the standalone Android shell-project sources
 * (manifest already carrying the selected permissions + a WebView activity
 * that prompts for them at runtime) and bundles everything into a `.zip`
 * shared via the Android share sheet. A desktop machine then runs the
 * Gradle `assembleRelease` step to produce the installable APK.
 *
 * The web assets are taken from the project's `dist/` (Vite-style build
 * output), `build/`, or the project root's `index.html` — in that order.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExportApkScreen(
    projectId: String,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val app = context.applicationContext as LaapApp
    val scope = rememberCoroutineScope()

    var appName by remember { mutableStateOf("") }
    var packageId by remember { mutableStateOf("") }
    var capabilities by remember { mutableStateOf(setOf<String>()) }
    var sourceDir by remember { mutableStateOf<File?>(null) }
    var detected by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var doneUri by remember { mutableStateOf<Uri?>(null) }

    // Resolve the project's built web assets once.
    LaunchedEffect(projectId) {
        val project = app.projectManager.get(projectId)
        appName = project?.name ?: "My App"
        val host = app.projectManager.hostDirFor(projectId)
        val found = resolveWebSource(host)
        sourceDir = found
        detected = when {
            found == null -> "未找到 index.html（请先构建 Web 应用）"
            found == host -> "使用项目根目录 ${found.absolutePath}"
            else -> "使用构建产物 ${found.absolutePath}"
        }
        val slug = (appName.replace(Regex("[^A-Za-z0-9]"), "").lowercase(Locale.ROOT))
            .ifEmpty { "webapp" }
        packageId = "org.laap.webapp.$slug"
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("导出独立 APK", fontWeight = FontWeight.SemiBold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
        ) {
            InfoBanner(detected)

            Spacer(Modifier.height(16.dp))
            Text("应用信息", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = appName,
                onValueChange = { appName = it },
                label = { Text("应用名称（桌面图标下显示）") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = packageId,
                onValueChange = { packageId = it },
                label = { Text("包名 (org.example.app)") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )

            Spacer(Modifier.height(20.dp))
            Text("运行时权限", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(4.dp))
            Text(
                "导出的应用会声明这些权限，并在运行时向用户弹窗申请。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(8.dp))
            PermissionRow("camera", "相机", "摄像头拍摄 / 扫码", capabilities) { capabilities = it }
            PermissionRow("microphone", "麦克风", "录音 / 语音输入", capabilities) { capabilities = it }
            PermissionRow("location", "定位", "GPS / 网络定位", capabilities) { capabilities = it }
            PermissionRow("storage", "存储", "读取图片 / 媒体文件", capabilities) { capabilities = it }
            PermissionRow("notifications", "通知", "推送 / 通知栏", capabilities) { capabilities = it }

            Spacer(Modifier.height(20.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            error?.let {
                Text(
                    it,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodyMedium,
                )
                Spacer(Modifier.height(8.dp))
            }

            val ready = sourceDir != null && appName.isNotBlank() && packageId.isNotBlank()
            Button(
                onClick = {
                    busy = true
                    error = null
                    doneUri = null
                    scope.launch {
                        val result = runCatching {
                            ApkProjectGenerator.generate(
                                context = context,
                                sourceDir = sourceDir!!,
                                appName = appName.trim(),
                                packageId = packageId.trim(),
                                capabilities = capabilities,
                            )
                        }
                        busy = false
                        result.onSuccess { uri ->
                            doneUri = uri
                            shareZip(context, uri, appName)
                        }.onFailure { t ->
                            error = t.message ?: "导出失败"
                            AppLogger.error("ExportApk", "export failed: ${t.message}")
                        }
                    }
                },
                enabled = ready && !busy,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (busy) {
                    Text("正在生成壳工程并打包…")
                } else {
                    Icon(Icons.Filled.Share, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("生成壳工程并分享 (.zip)")
                }
            }

            doneUri?.let {
                Spacer(Modifier.height(8.dp))
                OutlinedButton(onClick = { shareZip(context, it, appName) }, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Filled.Check, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("再次分享已生成的 .zip")
                }
                Spacer(Modifier.height(4.dp))
                Text(
                    "已生成：包名 $packageId，含 ${capabilities.size} 项权限。\n把 .zip 发送到桌面电脑，运行 export_webapp_apk.ps1 的构建步骤即可得到 APK。",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun InfoBanner(text: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(Icons.Filled.Info, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.width(8.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun PermissionRow(
    name: String,
    title: String,
    subtitle: String,
    selected: Set<String>,
    onChange: (Set<String>) -> Unit,
) {
    val checked = name in selected
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Checkbox(
            checked = checked,
            onCheckedChange = { c ->
                onChange(if (c) selected + name else selected - name)
            },
        )
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

/** Pick the best built-web source: dist/ → build/ → project root. */
private fun resolveWebSource(projectHost: File): File? {
    listOf("dist", "build").forEach { sub ->
        val candidate = File(projectHost, sub)
        if (File(candidate, "index.html").exists()) return candidate
    }
    return if (File(projectHost, "index.html").exists()) projectHost else null
}

private fun shareZip(context: Context, uri: Uri, appName: String) {
    val send = Intent(Intent.ACTION_SEND).apply {
        type = "application/zip"
        putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_SUBJECT, "$appName 壳工程")
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    val chooser = Intent.createChooser(send, "分享 APK 壳工程 (.zip)")
    chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    context.startActivity(chooser)
}