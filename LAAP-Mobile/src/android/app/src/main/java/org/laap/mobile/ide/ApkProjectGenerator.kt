package org.laap.mobile.ide

import android.content.Context
import android.net.Uri
import androidx.core.content.FileProvider
import org.laap.mobile.logging.AppLogger
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.util.UUID
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * Generates the source of a standalone Android APK shell project from a
 * built static web app, then bundles it into a single `.zip` the user can
 * hand to a desktop machine (which runs the Gradle `assembleRelease` step
 * to produce the installable APK).
 *
 * This is the on-device counterpart of the desktop
 * `tools/apk-export/export_webapp_apk.ps1` generator: it produces the exact
 * same project tree (manifest + [MainActivity] + Gradle files + `assets/www`)
 * so the artifact is interchangeable with what the desktop script generates
 * from `.SourceDir`.
 *
 * The generated [MainActivity] declares the runtime permissions selected by
 * the user and drives the WebView permission prompts, so the exported app can
 * use the camera / microphone / geolocation / file upload directly on the
 * device — no LAAP sandbox in the picture.
 */
object ApkProjectGenerator {

    private const val LOG_CATEGORY = "ApkProjectGenerator"

    /** Capability name → manifest `<uses-permission>` entries. */
    private val PERMISSION_MAP: Map<String, List<Pair<String, Int?>>> = mapOf(
        "camera" to listOf("android.permission.CAMERA" to null),
        "microphone" to listOf("android.permission.RECORD_AUDIO" to null),
        "location" to listOf(
            "android.permission.ACCESS_FINE_LOCATION" to null,
            "android.permission.ACCESS_COARSE_LOCATION" to null,
        ),
        "storage" to listOf(
            "android.permission.READ_MEDIA_IMAGES" to null,
            "android.permission.READ_MEDIA_VIDEO" to null,
            "android.permission.READ_MEDIA_VISUAL_USER_SELECTED" to null,
            "android.permission.READ_EXTERNAL_STORAGE" to 32,
        ),
        "notifications" to listOf("android.permission.POST_NOTIFICATIONS" to null),
    )

    val knownPermissions: Set<String> = PERMISSION_MAP.keys

    /**
     * Build the shell-project zip and return a content [Uri] for sharing.
     *
     * @param sourceDir host dir containing the built web app (must contain
     *   `index.html`).
     * @param appName  human-readable launcher label.
     * @param packageId reverse-domain package id, e.g. "org.laap.webapp.demo".
     * @param capabilities subset of [knownPermissions] to declare.
     */
    fun generate(
        context: Context,
        sourceDir: File,
        appName: String,
        packageId: String,
        capabilities: Set<String>,
    ): Uri {
        require(sourceDir.isDirectory) { "sourceDir is not a directory: ${sourceDir.absolutePath}" }
        require(File(sourceDir, "index.html").exists()) {
            "Source dir must contain index.html: ${sourceDir.absolutePath}"
        }
        require(packageId.matches(Regex("^[a-zA-Z_][a-zA-Z0-9_]*(\\.[a-zA-Z_][a-zA-Z0-9_]*)+$"))) {
            "PackageId '$packageId' must look like org.example.app"
        }
        val unknown = capabilities - knownPermissions
        require(unknown.isEmpty()) { "Unknown capability(s): $unknown" }

        val staging = File(context.cacheDir, "apk-export/${UUID.randomUUID().toString()}")
        staging.mkdirs()

        try {
            val projectDir = File(staging, "project")
            val appMain = File(projectDir, "app/src/main")
            val appPkgDir = File(appMain, "java/${packageId.replace('.', '/')}")
            appPkgDir.mkdirs()
            File(appMain, "assets/www").mkdirs()
            File(appMain, "res/values").mkdirs()
            File(appMain, "res/mipmap-anydpi-v26").mkdirs()

            writeText(File(projectDir, "settings.gradle.kts"), settingsGradle())
            writeText(File(projectDir, "build.gradle.kts"), rootGradle())
            writeText(File(projectDir, "gradle.properties"), gradleProps())
            writeText(File(projectDir, "app/build.gradle.kts"), appGradle(packageId))
            writeText(File(appMain, "AndroidManifest.xml"), manifest(appName, packageId, capabilities))
            writeText(File(appPkgDir, "MainActivity.java"), mainActivity(packageId))
            writeText(File(appMain, "res/values/strings.xml"), strings(appName))
            writeText(File(appMain, "res/values/colors.xml"), colors())
            writeText(File(appMain, "res/values/themes.xml"), theme())
            writeText(
                File(appMain, "res/mipmap-anydpi-v26/ic_launcher_foreground.xml"),
                launcherForeground(),
            )
            writeText(
                File(appMain, "res/mipmap-anydpi-v26/ic_launcher.xml"),
                launcherAdaptiveIcon(),
            )

            // Copy the built web app into assets/www.
            sourceDir.copyRecursively(
                File(appMain, "assets/www"),
                overwrite = true,
            )

            // Zip the project tree.
            val sharedDir = File(context.cacheDir, "shared").apply { mkdirs() }
            val safeName = packageId.replace('.', '_')
            val zipFile = File(sharedDir, "$safeName.zip")
            if (zipFile.exists()) zipFile.delete()
            ZipOutputStream(FileOutputStream(zipFile).buffered()).use { zos ->
                zipDir(zos, projectDir, projectDir)
            }

            val authority = "${context.packageName}.fileprovider"
            val uri = FileProvider.getUriForFile(context, authority, zipFile)
            AppLogger.info(LOG_CATEGORY, "generated ${zipFile.absolutePath} (${zipFile.length()} bytes)")
            return uri
        } finally {
            runCatching { staging.deleteRecursively() }
        }
    }

    /** Zip [dir]'s subtree into [zos] with paths relative to [base]. */
    private fun zipDir(zos: ZipOutputStream, dir: File, base: File) {
        dir.listFiles()?.forEach { child ->
            val rel = base.toPath().relativize(child.toPath()).toString().replace('\\', '/')
            if (child.isDirectory) {
                zos.putNextEntry(ZipEntry("$rel/"))
                zos.closeEntry()
                zipDir(zos, child, base)
            } else {
                zos.putNextEntry(ZipEntry(rel))
                FileInputStream(child).use { it.copyTo(zos, bufferSize = 16 * 1024) }
                zos.closeEntry()
            }
        }
    }

    private fun writeText(file: File, content: String) {
        file.parentFile?.mkdirs()
        file.writeText(content, Charsets.UTF_8)
    }

    // ── Template content (mirrors tools/apk-export/export_webapp_apk.ps1) ──

    private fun manifest(appName: String, packageId: String, capabilities: Set<String>): String {
        val perms = StringBuilder("    <uses-permission android:name=\"android.permission.INTERNET\" />\n")
        capabilities.forEach { cap ->
            PERMISSION_MAP[cap].orEmpty().forEach { (perm, maxSdk) ->
                val maxAttr = if (maxSdk != null) " android:maxSdkVersion=\"$maxSdk\"" else ""
                perms.append("    <uses-permission android:name=\"$perm\"$maxAttr />\n")
            }
        }
        return """
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
$perms
    <application
        android:label="$appName"
        android:icon="@mipmap/ic_launcher"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.App">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden|screenLayout|smallestScreenSize|uiMode">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""".trimIndent()
    }

    private fun mainActivity(packageId: String): String = """
package $packageId;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.GeolocationPermissions;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.activity.ComponentActivity;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.core.content.ContextCompat;

/**
 * Full-capability WebView shell for a LAAP-exported web app. Loads the
 * bundled assets from assets/www/index.html and drives the runtime
 * permissions the app declares in AndroidManifest.xml so the web content
 * can use the camera, microphone, geolocation and file upload directly on
 * the device — no sandbox required.
 */
public class MainActivity extends ComponentActivity {

    private static final int PERMISSION_REQUEST = 1001;
    private static final int GEOLOCATION_REQUEST = 1002;
    private WebView web;
    private PermissionRequest heldRequest = null;
    private GeolocationPermissions.Callback heldLocationCallback = null;
    private String heldLocationOrigin = null;
    private ValueCallback<Uri[]> pendingFileCallback = null;

    private final androidx.activity.result.ActivityResultLauncher<String[]>
            openDocuments = registerForActivityResult(
                    new ActivityResultContracts.OpenMultipleDocuments(), uris -> {
                        if (pendingFileCallback != null) {
                            pendingFileCallback.onReceiveValue(
                                    uris == null ? null : uris.toArray(new Uri[uris.size()]));
                            pendingFileCallback = null;
                        }
                    });

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme() == null
                        ? "" : request.getUrl().getScheme().toLowerCase();
                return !(scheme.equals("http") || scheme.equals("https"));
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(PermissionRequest request) {
                java.util.List<String> needed = new java.util.ArrayList<>();
                for (String r : request.getResources()) {
                    if (r.equals(PermissionRequest.RESOURCE_VIDEO_CAPTURE)) {
                        needed.add(Manifest.permission.CAMERA);
                    } else if (r.equals(PermissionRequest.RESOURCE_AUDIO_CAPTURE)) {
                        needed.add(Manifest.permission.RECORD_AUDIO);
                    }
                }
                java.util.List<String> missing = new java.util.ArrayList<>();
                for (String p : needed) {
                    if (ContextCompat.checkSelfPermission(MainActivity.this, p)
                            != PackageManager.PERMISSION_GRANTED) {
                        missing.add(p);
                    }
                }
                if (missing.isEmpty()) {
                    request.grant(request.getResources());
                    return;
                }
                heldRequest = request;
                requestPermissions(missing.toArray(new String[0]), PERMISSION_REQUEST);
            }

            @Override
            public void onGeolocationPermissionsShowPrompt(
                    String origin, GeolocationPermissions.Callback callback) {
                boolean granted = ContextCompat.checkSelfPermission(
                        MainActivity.this, Manifest.permission.ACCESS_FINE_LOCATION)
                        == PackageManager.PERMISSION_GRANTED
                        || ContextCompat.checkSelfPermission(
                        MainActivity.this, Manifest.permission.ACCESS_COARSE_LOCATION)
                        == PackageManager.PERMISSION_GRANTED;
                if (granted) {
                    callback.invoke(origin, true, false);
                    return;
                }
                // Not yet granted — ask the user so the web app can actually
                // use navigator.geolocation instead of silently failing.
                heldLocationCallback = callback;
                heldLocationOrigin = origin;
                requestPermissions(new String[]{
                                Manifest.permission.ACCESS_FINE_LOCATION,
                                Manifest.permission.ACCESS_COARSE_LOCATION},
                        GEOLOCATION_REQUEST);
            }

            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback,
                                             FileChooserParams fileChooserParams) {
                if (pendingFileCallback != null) {
                    pendingFileCallback.onReceiveValue(null);
                }
                pendingFileCallback = filePathCallback;
                String[] mime = fileChooserParams.getAcceptTypes();
                if (mime == null || mime.length == 0) {
                    mime = new String[]{"*/*"};
                }
                openDocuments.launch(mime);
                return true;
            }
        });

        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setGeolocationEnabled(true);
        web.getSettings().setMediaPlaybackRequiresUserGesture(false);
        web.getSettings().setUseWideViewPort(true);
        web.getSettings().setLoadWithOverviewMode(true);
        web.getSettings().setAllowFileAccess(true);
        web.getSettings().setAllowContentAccess(true);
        web.getSettings().setAllowFileAccessFromFileURLs(true);
        web.getSettings().setAllowUniversalAccessFromFileURLs(true);

        setContentView(web);
        web.loadUrl("file:///android_asset/www/index.html");
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST && heldRequest != null) {
            boolean allGranted = grantResults.length > 0;
            for (int r : grantResults) {
                if (r != PackageManager.PERMISSION_GRANTED) {
                    allGranted = false;
                    break;
                }
            }
            if (allGranted) {
                heldRequest.grant(heldRequest.getResources());
            } else {
                heldRequest.deny();
            }
            heldRequest = null;
        } else if (requestCode == GEOLOCATION_REQUEST && heldLocationCallback != null) {
            boolean granted = false;
            for (int r : grantResults) {
                if (r == PackageManager.PERMISSION_GRANTED) {
                    granted = true;
                    break;
                }
            }
            heldLocationCallback.invoke(heldLocationOrigin, granted, false);
            heldLocationCallback = null;
            heldLocationOrigin = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
""".trimIndent()

    private fun settingsGradle(): String = """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "WebAppShell"
include(":app")
""".trimIndent()

    private fun rootGradle(): String = """
plugins {
    id("com.android.application") version "8.7.3" apply false
}
""".trimIndent()

    private fun gradleProps(): String = """
android.useAndroidX=true
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
""".trimIndent()

    private fun appGradle(packageId: String): String = """
plugins {
    id("com.android.application")
}

android {
    namespace = "$packageId"
    compileSdk = 35
    defaultConfig {
        applicationId = "$packageId"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }
    signingConfigs {
        create("release") {
            storeFile = file(System.getProperty("user.home") + "/.android/debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
            enableV1Signing = true
            enableV2Signing = true
            enableV3Signing = true
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity:1.9.3")
}

configurations.configureEach {
    exclude(group = "org.jetbrains.kotlin", module = "kotlin-stdlib-jdk7")
    exclude(group = "org.jetbrains.kotlin", module = "kotlin-stdlib-jdk8")
}
""".trimIndent()

    private fun strings(appName: String): String = """
<resources>
    <string name="app_name">$appName</string>
</resources>
""".trimIndent()

    private fun colors(): String = """
<resources>
    <color name="ic_launcher_background">#1A1A2E</color>
</resources>
""".trimIndent()

    private fun theme(): String = """
<resources>
    <style name="Theme.App" parent="android:Theme.Material.Light.NoActionBar">
        <item name="android:windowBackground">@android:color/white</item>
    </style>
</resources>
""".trimIndent()

    private fun launcherForeground(): String = """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <group android:translateX="8" android:translateY="8">
        <path android:fillColor="#FFFFFF"
            android:pathData="M46,46h16v16h-16z" />
    </group>
</vector>
""".trimIndent()

    private fun launcherAdaptiveIcon(): String = """
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
""".trimIndent()
}