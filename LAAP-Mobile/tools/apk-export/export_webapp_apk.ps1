#Requires -Version 5.1
<#
.SYNOPSIS
    Package a built static web app into a standalone, installable Android APK.

.DESCRIPTION
    Generates a complete, self-contained minimal Android Gradle project (a
    WebView shell that loads the app's bundled assets) and builds it into a
    signed APK. This gives a web app developed inside LAAP-Mobile a real
    "independent app" home-screen presence with its own permissions — it no
    longer has to run inside the LAAP sandbox.

    The generated shell declares whatever runtime permissions the app needs
    (camera / microphone / location / …), so the web app can use the phone's
    hardware on its own, without going through LAAP.

.PARAMETER SourceDir
    Directory containing the built static web app. Must contain index.html.
    e.g. a Vite `dist/` folder, or a static-html project dir.

.PARAMETER AppName
    Human-readable app name shown under the icon. Default: "My Web App".

.PARAMETER PackageId
    Reverse-domain package id, e.g. "org.laap.webapp.demoapp". Default uses
    the app name slugified under org.laap.webapp.

.PARAMETER Permissions
    Array of capability names to declare. Allowed: camera, microphone,
    location, storage, notifications. Default: none (just network).

.PARAMETER OutDir
    Where to write the generated project and the final APK.
    Default: $PSScriptRoot\out

.PARAMETER Build
    If set, builds the APK after generating. If not, only generates the
    project source.

.EXAMPLE
    .\export_webapp_apk.ps1 -SourceDir .\myapp\dist -AppName "My App" `
        -Permissions camera,location -Build
#>
param(
    [Parameter(Mandatory = $true)][string]$SourceDir,
    [string]$AppName = "My Web App",
    [string]$PackageId = "",
    [string[]]$Permissions = @(),
    [string]$OutDir = (Join-Path $PSScriptRoot "out"),
    [switch]$Build
)

$ErrorActionPreference = "Stop"

# Write UTF-8 WITHOUT a BOM. Windows PowerShell 5.1's `Set-Content -Encoding
# UTF8` emits a BOM, which Gradle (Java) reads as part of the first property
# name in gradle.properties (e.g. "\uFEFFandroid.useAndroidX") — silently
# disabling android.useAndroidX and breaking the build. PowerShell 7 defaults
# to no BOM, which is why direct runs worked but server-triggered ones failed.
function Write-NoBom {
    param([string]$Path, [string]$Value)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Value, $utf8NoBom)
}

# ── Resolve inputs ─────────────────────────────────────────────────────────
$src = (Resolve-Path $SourceDir).Path
if (-not (Test-Path (Join-Path $src "index.html"))) {
    throw "SourceDir '$src' does not contain an index.html — point this at a built static web app."
}

if ([string]::IsNullOrWhiteSpace($PackageId)) {
    $slug = ($AppName -replace '[^a-zA-Z0-9]', '').ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($slug)) { $slug = "webapp" }
    $PackageId = "org.laap.webapp.$slug"
}
if ($PackageId -notmatch '^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$') {
    throw "PackageId '$PackageId' must look like org.example.app."
}

$laapMobile = Join-Path $PSScriptRoot "..\..\src\android"
if (-not (Test-Path (Join-Path $laapMobile "gradlew.bat"))) {
    throw "Could not find LAAP-Mobile android project at '$laapMobile'. Run this from LAAP-Mobile\tools\apk-export."
}

$projDir = Join-Path $OutDir "project"
$appPkg = $PackageId -replace '\.', '/'
$label = $AppName

# ── Permission → manifest uses-permission mapping ─────────────────────────
$permMap = @{
    "camera"      = @("android.permission.CAMERA")
    "microphone"  = @("android.permission.RECORD_AUDIO")
    "location"    = @("android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION")
    "storage"     = @("android.permission.READ_EXTERNAL_STORAGE", "android.permission.READ_MEDIA_IMAGES", "android.permission.READ_MEDIA_VISUAL_USER_SELECTED")
    "notifications" = @("android.permission.POST_NOTIFICATIONS")
}
$known = @($Permissions) | ForEach-Object { $_.ToLowerInvariant().Split(',') } |
    ForEach-Object { $_.Trim() } | Where-Object { $_ -and $_ -ne 'none' } |
    Sort-Object -Unique
$unknown = $known | Where-Object { $_ -notin $permMap.Keys }
if ($unknown) {
    throw "Unknown permission(s): $($unknown -join ', '). Allowed: $($permMap.Keys -join ', ')."
}
$permLines = @()
foreach ($k in $known) {
    foreach ($p in $permMap[$k]) {
        $maxSdk = ""
        if ($p -eq "android.permission.READ_EXTERNAL_STORAGE") { $maxSdk = ' android:maxSdkVersion="32"' }
        $permLines += "    <uses-permission android:name=""$p""$maxSdk />"
    }
}
$permBlock = $permLines -join "`r`n"

# ── Manifest ───────────────────────────────────────────────────────────────
$manifest = @"
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
`r`n$permBlock

    <application
        android:label="$label"
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
"@

# ── MainActivity.java ─────────────────────────────────────────────────────
$mainActivity = @'
package <APP_PKG>;

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
                // Keep http(s) in the shell; push everything else out.
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
'@
$mainActivity = $mainActivity.Replace("<APP_PKG>", $PackageId)

# ── Gradle files ───────────────────────────────────────────────────────────
$settingsGradle = @'
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
'@

$rootGradle = @'
plugins {
    id("com.android.application") version "8.7.3" apply false
}
'@

$gradleProps = @'
android.useAndroidX=true
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
org.gradle.daemon=false
# AAPT2's detached daemon fails to start when the build is spawned from a
# non-interactive server (node). Run aapt2 in-process instead.
android.enableAapt2Daemon=false
'@

$appGradle = @"
plugins {
    id("com.android.application")
}

android {
    namespace = "$PackageId"
    compileSdk = 35
    defaultConfig {
        applicationId = "$PackageId"
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

// AndroidX pulls kotlin-stdlib via different versions (1.8.22 from core-ktx,
// 1.6.21 jdk7/jdk8 from activity). kotlin-stdlib 1.8.22 already contains the
// jdk7/jdk8 classes, so drop the legacy split jars to avoid duplicate classes.
configurations.configureEach {
    exclude(group = "org.jetbrains.kotlin", module = "kotlin-stdlib-jdk7")
    exclude(group = "org.jetbrains.kotlin", module = "kotlin-stdlib-jdk8")
}
"@

$strings = @"
<resources>
    <string name="app_name">$label</string>
</resources>
"@

$colors = @'
<resources>
    <color name="ic_launcher_background">#1A1A2E</color>
</resources>
'@

$theme = @'
<resources>
    <style name="Theme.App" parent="android:Theme.Material.Light.NoActionBar">
        <item name="android:windowBackground">@android:color/white</item>
    </style>
</resources>
'@

function New-AdaptiveIcon {
    param([string]$BaseDir, [string]$Char)
    $iconBase = Join-Path $BaseDir "mipmap-anydpi-v26"
    New-Item -ItemType Directory -Force -Path $iconBase | Out-Null
    # Simple adaptive icon referencing just a background color and a
    # foreground vector with the first letter of the app name.
    $fg = @"
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <group android:translateX="8" android:translateY="8">
        <path android:fillColor="#FFFFFF"
            android:pathData="M46,46h16v16h-16z" />
    </group>
</vector>
"@
    Write-NoBom -Path (Join-Path $iconBase "ic_launcher_foreground.xml") -Value $fg
    $legacyXml = @'
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
'@
    Write-NoBom -Path (Join-Path $iconBase "ic_launcher.xml") -Value $legacyXml
}

# ── Write project tree ─────────────────────────────────────────────────────
Write-Host "[OK] Generating shell project at $projDir"
if (Test-Path $projDir) { Remove-Item -Recurse -Force $projDir }
$appSrcMain = Join-Path $projDir "app\src\main"
New-Item -ItemType Directory -Force -Path (Join-Path $appSrcMain "java\$appPkg") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $appSrcMain "assets\www") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $appSrcMain "res\values") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $appSrcMain "res\mipmap-anydpi-v26") | Out-Null

Write-NoBom -Path (Join-Path $projDir "settings.gradle.kts") -Value $settingsGradle
Write-NoBom -Path (Join-Path $projDir "build.gradle.kts") -Value $rootGradle
Write-NoBom -Path (Join-Path $projDir "gradle.properties") -Value $gradleProps
Write-NoBom -Path (Join-Path $projDir "app\build.gradle.kts") -Value $appGradle
Write-NoBom -Path (Join-Path $projDir "app\src\main\AndroidManifest.xml") -Value $manifest
Write-NoBom -Path (Join-Path $projDir "app\src\main\java\$appPkg\MainActivity.java") -Value $mainActivity
Write-NoBom -Path (Join-Path $projDir "app\src\main\res\values\strings.xml") -Value $strings
Write-NoBom -Path (Join-Path $projDir "app\src\main\res\values\colors.xml") -Value $colors
Write-NoBom -Path (Join-Path $projDir "app\src\main\res\values\themes.xml") -Value $theme
New-AdaptiveIcon -BaseDir (Join-Path $appSrcMain "res") -Char $label

# Copy web assets
Copy-Item -Recurse -Force (Join-Path $src "*") (Join-Path $appSrcMain "assets\www")

# Copy the Gradle wrapper from LAAP-Mobile so no downloads are needed beyond
# what an Android build already cached.
$wrapperFrom = Join-Path $laapMobile "gradle\wrapper"
$wrapperTo = Join-Path $projDir "gradle\wrapper"
New-Item -ItemType Directory -Force -Path $wrapperTo | Out-Null
Copy-Item -Force (Join-Path $wrapperFrom "gradle-wrapper.jar") $wrapperTo
Copy-Item -Force (Join-Path $wrapperFrom "gradle-wrapper.properties") $wrapperTo
Copy-Item -Force (Join-Path $laapMobile "gradlew") $projDir
Copy-Item -Force (Join-Path $laapMobile "gradlew.bat") $projDir

Write-Host "[OK] Project generated. Permissions: $(if ($known) { $known -join ', ' } else { 'none (network only)' })"

if (-not $Build) {
    Write-Host "[INFO] Skipping build (-Build not set). To build:"
    Write-Host ("       .\" + $PSScriptRoot + "\export_webapp_apk.ps1 -SourceDir '" + $SourceDir + "' -Permissions " + ($Permissions -join ',') + " -Build")
    exit 0
}

# ── Build ──────────────────────────────────────────────────────────────────
Write-Host "[BUILD] Running Gradle assembleRelease in $projDir (this may take a while)"
Push-Location $projDir
try {
    & .\gradlew.bat assembleRelease --console=plain
    if ($LASTEXITCODE -ne 0) { throw "Gradle build failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

$apk = Join-Path $projDir "app\build\outputs\apk\release\app-release.apk"
if (-not (Test-Path $apk)) { throw "Expected APK not found at $apk" }

$final = Join-Path $OutDir "$($PackageId -replace '\.', '_').apk"
Copy-Item -Force $apk $final
Write-Host "[COMPLETE] APK: $final"