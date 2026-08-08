package org.laap.mobile.sandbox

import android.content.Context
import android.net.ConnectivityManager
import android.net.LinkProperties
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FilterInputStream
import java.io.InputStream
import java.nio.charset.Charset
import java.util.zip.GZIPInputStream

/**
 * Observable state for rootfs installation. Mirrors the conceptual iOS
 * `downloadRootfs(progress:)` contract: discrete phases with a 0..1 fraction
 * during the long-running extract step. Neither platform actually downloads
 * the rootfs from the network today — it ships bundled as an asset — so
 * "progress" tracks asset-stream consumption (compressed bytes) instead of
 * HTTP transfer. The fraction semantics are identical from the UI's viewpoint.
 */
sealed class RootfsInstallState {
    object Idle : RootfsInstallState()
    object Preparing : RootfsInstallState()
    /** progress in 0f..1f, based on compressed asset bytes consumed. */
    data class Extracting(val progress: Float) : RootfsInstallState()
    object Finalizing : RootfsInstallState()
    object Installed : RootfsInstallState()
    data class Failed(val error: String) : RootfsInstallState()
}

/**
 * Manages Alpine Linux rootfs installation and PRoot binary extraction.
 * Corresponds to iOS RootfsManager.swift.
 */
class RootfsManager private constructor(private val context: Context) {

    val rootfsDir: File = File(context.filesDir, "alpine-rootfs")
    val prootBinary: File = File(context.filesDir, "proot-aarch64")

    private val archFile: File get() = File(rootfsDir, ".arch")

    val isInstalled: Boolean
        get() {
            if (!rootfsDir.exists() || !archFile.exists()) return false
            if (archFile.readText().trim() != ARCH) return false
            // T-rootfs-shell-fix: the marker file alone is not enough; a
            // previous crash or symlink failure can leave rootfs without
            // bin/sh. Force re-extraction if critical files are missing.
            val required = listOf("bin/sh", "bin/busybox")
            return required.all { File(rootfsDir, it).exists() }
        }

    /**
     * Observable install progress. UI layers (OnboardingScreen,
     * RootfsManagementScreen) bind this and render a progress bar during
     * `installIfNeeded()` / `reset()`. Emits `Installed` on success and
     * `Failed` on error so callers can surface retry affordances.
     */
    private val _installState = MutableStateFlow<RootfsInstallState>(
        if (isInstalled) RootfsInstallState.Installed else RootfsInstallState.Idle
    )
    val installState: StateFlow<RootfsInstallState> = _installState.asStateFlow()

    /**
     * Install Alpine rootfs from assets if not already present.
     *
     * T-rootfs-robust: the rootfs is shipped as a fully unpacked directory tree
     * under assets/alpine-rootfs/ (prepared by scripts/prepare_android_sandbox.py).
     * This avoids all the fragility of parsing a POSIX tar stream on device
     * (symlink creation restrictions, AAPT compression, character-set issues).
     *
     * If the unpacked tree is unavailable or incomplete, we fall back to the
     * legacy .tar.gz asset, then to a network download.
     *
     * Progress is published to [installState] (Preparing → Extracting(f) →
     * Finalizing → Installed / Failed).
     */
    suspend fun installIfNeeded() = withContext(Dispatchers.IO) {
        if (isInstalled) {
            Log.d(TAG, "Rootfs already installed at $rootfsDir")
            _installState.value = RootfsInstallState.Installed
            return@withContext
        }

        try {
            _installState.value = RootfsInstallState.Preparing
            Log.i(TAG, "Installing Alpine rootfs...")

            // Clean up any partial install
            if (rootfsDir.exists()) {
                rootfsDir.deleteRecursively()
            }
            rootfsDir.mkdirs()

            // --- Phase 1: copy unpacked asset tree (preferred) ---
            val assetInstalled = tryInstallFromUnpackedAsset()

            if (!assetInstalled) {
                Log.w(TAG, "Unpacked asset copy failed, falling back to legacy tar asset")
                _installState.value = RootfsInstallState.Preparing
                if (rootfsDir.exists()) rootfsDir.deleteRecursively()
                rootfsDir.mkdirs()

                val tarInstalled = tryInstallFromTarAsset()
                if (!tarInstalled) {
                    Log.w(TAG, "Tar asset extraction failed, falling back to network download")
                    _installState.value = RootfsInstallState.Preparing
                    if (rootfsDir.exists()) rootfsDir.deleteRecursively()
                    rootfsDir.mkdirs()
                    tryInstallFromNetwork()
                }
            }

            // --- Common finalization ---
            finalizeInstallation()

        } catch (t: Throwable) {
            Log.e(TAG, "Rootfs installation failed", t)
            _installState.value = RootfsInstallState.Failed(t.message ?: t.javaClass.simpleName)
            throw t
        }
    }

    /**
     * Copy the pre-unpacked rootfs directory tree from assets/alpine-rootfs.
     * Returns true on success (critical files present), false on failure.
     */
    private fun tryInstallFromUnpackedAsset(): Boolean {
        return try {
            val entries = context.assets.list(ROOTFS_UNPACKED_ASSET) ?: emptyArray()
            if (entries.isEmpty()) {
                Log.w(TAG, "No unpacked rootfs assets found at $ROOTFS_UNPACKED_ASSET")
                return false
            }

            val totalEntries = countAssetEntries(ROOTFS_UNPACKED_ASSET)
            Log.i(TAG, "Copying unpacked rootfs ($totalEntries entries) from assets...")
            _installState.value = RootfsInstallState.Extracting(0f)

            var copied = 0
            val counter = java.util.concurrent.atomic.AtomicInteger(0)
            val reportedPercent = object { var value = -1 }
            for (name in entries) {
                copied += copyAssetDir(
                    "$ROOTFS_UNPACKED_ASSET/$name",
                    rootfsDir,
                    name,
                    counter,
                    onProgress = { current ->
                        if (totalEntries > 0) {
                            val pct = (current * 100 / totalEntries)
                            if (pct != reportedPercent.value) {
                                reportedPercent.value = pct
                                _installState.value = RootfsInstallState.Extracting(pct / 100f)
                            }
                        }
                    }
                )
            }

            val shFile = File(rootfsDir, "bin/sh")
            val busyboxFile = File(rootfsDir, "bin/busybox")
            if (!shFile.exists() || !busyboxFile.exists()) {
                Log.e(TAG, "Unpacked rootfs incomplete: bin/sh=${shFile.exists()}, bin/busybox=${busyboxFile.exists()}")
                return false
            }

            Log.i(TAG, "Rootfs copied from unpacked assets: $copied entries")
            true
        } catch (t: Throwable) {
            Log.e(TAG, "Unpacked asset copy failed", t)
            false
        }
    }

    /**
     * Count total file + directory entries under an asset path.
     */
    private fun countAssetEntries(assetPath: String): Int {
        val entries = context.assets.list(assetPath) ?: return 0
        if (entries.isEmpty()) return 1
        return entries.sumOf { countAssetEntries("$assetPath/$it") }
    }

    /**
     * Attempt to extract rootfs from bundled tar.gz/tar asset. Returns true on
     * success, false on failure.
     */
    private fun tryInstallFromTarAsset(): Boolean {
        return try {
            val assetName = try {
                context.assets.open(ROOTFS_ASSET).close()
                ROOTFS_ASSET
            } catch (_: java.io.FileNotFoundException) {
                try {
                    context.assets.open(ROOTFS_ASSET_TAR).close()
                    ROOTFS_ASSET_TAR
                } catch (_: java.io.FileNotFoundException) {
                    Log.e(TAG, "No rootfs tar asset found in APK")
                    return false
                }
            }

            val assetTotal: Long = try {
                context.assets.openFd(assetName).use { it.length }
            } catch (_: Exception) { 0L }

            _installState.value = RootfsInstallState.Extracting(0f)

            context.assets.open(assetName).use { rawAsset ->
                val progressStream = ProgressInputStream(rawAsset, assetTotal) { fraction ->
                    _installState.value = RootfsInstallState.Extracting(fraction)
                }
                if (assetName.endsWith(".gz")) {
                    GZIPInputStream(progressStream).use { gzipStream ->
                        extractTar(gzipStream, rootfsDir)
                    }
                } else {
                    extractTar(progressStream, rootfsDir)
                }
            }

            val shFile = File(rootfsDir, "bin/sh")
            val busyboxFile = File(rootfsDir, "bin/busybox")
            if (!shFile.exists() || !busyboxFile.exists()) {
                Log.e(TAG, "Tar asset extraction incomplete: bin/sh=${shFile.exists()}, bin/busybox=${busyboxFile.exists()}")
                return false
            }

            Log.i(TAG, "Rootfs extracted from tar asset")
            true
        } catch (t: Throwable) {
            Log.e(TAG, "Tar asset extraction failed", t)
            false
        }
    }

    /**
     * Download and extract rootfs from the Alpine CDN. Used as a fallback
     * when bundled assets fail. Requires INTERNET permission.
     */
    private fun tryInstallFromNetwork() {
        Log.i(TAG, "Downloading rootfs from $ROOTFS_DOWNLOAD_URL")
        _installState.value = RootfsInstallState.Extracting(0f)

        val url = java.net.URL(ROOTFS_DOWNLOAD_URL)
        val connection = url.openConnection() as java.net.HttpURLConnection
        connection.connectTimeout = 30_000
        connection.readTimeout = 300_000
        connection.instanceFollowRedirects = true

        try {
            val responseCode = connection.responseCode
            if (responseCode != java.net.HttpURLConnection.HTTP_OK) {
                throw java.io.IOException("HTTP $responseCode downloading rootfs")
            }

            val totalBytes = connection.contentLengthLong
            Log.i(TAG, "Rootfs download size: $totalBytes bytes")

            connection.inputStream.use { networkStream ->
                val progressStream = ProgressInputStream(networkStream, totalBytes) { fraction ->
                    _installState.value = RootfsInstallState.Extracting(fraction)
                }
                GZIPInputStream(progressStream).use { gzipStream ->
                    extractTar(gzipStream, rootfsDir)
                }
            }

            // Verify
            val shFile = File(rootfsDir, "bin/sh")
            val busyboxFile = File(rootfsDir, "bin/busybox")
            if (!shFile.exists() || !busyboxFile.exists()) {
                throw java.io.IOException(
                    "Network rootfs extraction incomplete: bin/sh=${shFile.exists()}, bin/busybox=${busyboxFile.exists()}"
                )
            }

            Log.i(TAG, "Rootfs downloaded and extracted successfully")
        } finally {
            connection.disconnect()
        }
    }

    /**
     * Common finalization: validate, write arch marker, create dirs, DNS.
     */
    private fun finalizeInstallation() {
        _installState.value = RootfsInstallState.Finalizing

        // Validate critical files
        val requiredFiles = listOf("bin/sh", "bin/busybox")
        for (required in requiredFiles) {
            if (!File(rootfsDir, required).exists()) {
                throw IllegalStateException(
                    "Rootfs installation incomplete: missing $required. " +
                    "Try Settings → Rootfs → Reset Rootfs."
                )
            }
        }

        // Write arch marker
        archFile.writeText(ARCH)

        // Pre-create /var/laap directories
        val laapSubdirs = listOf("attachments", "offloads", "workspace", "skills", "memory", "shared", "mounts")
        for (subdir in laapSubdirs) {
            File(rootfsDir, "var/laap/$subdir").mkdirs()
        }

        // Pre-create /opt/bin
        File(rootfsDir, "opt/bin").mkdirs()

        // Write resolv.conf
        refreshDns()

        // Flag fresh install for mirror auto-detection
        context.getSharedPreferences("mirror_settings", Context.MODE_PRIVATE)
            .edit()
            .putBoolean("rootfs.freshInstall", true)
            .apply()

        Log.i(TAG, "Rootfs installation complete")
        _installState.value = RootfsInstallState.Installed
    }

    /** Directory containing extracted native libraries (read-only, executable). */
    val nativeLibDir: File = File(context.applicationInfo.nativeLibraryDir)

    /** Directory where PRoot runtime dependencies are staged with SONAMEs. */
    val prootLibsDir: File = File(context.filesDir, "proot-libs")

    /**
     * Download PRoot .deb from Termux packages and extract the binary.
     * Used as a last-resort fallback when bundled assets and native libs
     * are all invalid.
     */
    private fun downloadAndExtractProot() {
        Log.i(TAG, "Downloading PRoot from $PROOT_DOWNLOAD_URL")
        val url = java.net.URL(PROOT_DOWNLOAD_URL)
        val conn = url.openConnection() as java.net.HttpURLConnection
        conn.connectTimeout = 30_000
        conn.readTimeout = 300_000
        conn.instanceFollowRedirects = true

        try {
            if (conn.responseCode != java.net.HttpURLConnection.HTTP_OK) {
                throw java.io.IOException("HTTP ${conn.responseCode} downloading PRoot")
            }

            // Read .deb to a temp file
            val debFile = File(context.cacheDir, "proot-download.deb")
            conn.inputStream.use { input ->
                debFile.outputStream().use { output -> input.copyTo(output) }
            }
            Log.i(TAG, "Downloaded PRoot deb: ${debFile.length()} bytes")

            // Extract proot binary from .deb (ar archive → data.tar.xz → proot)
            extractDebProot(debFile, prootBinary)
            debFile.delete()

            if (!prootBinary.exists() || prootBinary.length() < 4) {
                throw java.io.IOException("Extracted PRoot binary is empty or missing")
            }
            prootBinary.setExecutable(true, false)
            Log.i(TAG, "PRoot downloaded and extracted: ${prootBinary.length()} bytes")
        } finally {
            conn.disconnect()
        }
    }

    /**
     * Extract the 'proot' binary from a Termux .deb package.
     * Uses manual ar + tar parsing to avoid external dependencies.
     */
    private fun extractDebProot(debPath: File, dest: File) {
        val tmpDir = File(context.cacheDir, "proot-extract-${System.currentTimeMillis()}")
        tmpDir.mkdirs()

        try {
            debPath.inputStream().use { f ->
                val magic = ByteArray(8)
                f.read(magic)
                if (!magic.contentEquals(byteArrayOf('!'.code.toByte(), '<'.code.toByte(), 'a'.code.toByte(), 'r'.code.toByte(), 'c'.code.toByte(), 'h'.code.toByte(), '>'.code.toByte(), '\n'.code.toByte()))) {
                    throw java.io.IOException("Not an ar archive")
                }

                var dataTarFile: File? = null
                while (true) {
                    val header = ByteArray(60)
                    val n = f.read(header)
                    if (n < 60) break
                    val name = String(header, 0, 16).trim()
                    val sizeStr = String(header, 48, 10).trim()
                    val size = sizeStr.toIntOrNull() ?: 0
                    val pad = size % 2

                    if (name.startsWith("data.tar")) {
                        dataTarFile = File(tmpDir, name)
                        dataTarFile.outputStream().use { out ->
                            var remaining = size
                            val buf = ByteArray(8192)
                            while (remaining > 0) {
                                val toRead = minOf(buf.size, remaining)
                                val r = f.read(buf, 0, toRead)
                                if (r < 0) break
                                out.write(buf, 0, r)
                                remaining -= r
                            }
                        }
                        break
                    } else {
                        f.skip(size + pad.toLong())
                    }
                }

                val dataFile = dataTarFile ?: throw java.io.IOException("data.tar not found in .deb")

                // Extract data.tar to tmp dir using our manual tar parser.
                // data.tar is typically .xz compressed; Android has no built-in
                // xz support, so try plain tar first, then report if xz is needed.
                val extractDir = File(tmpDir, "extracted")
                extractDir.mkdirs()

                try {
                    dataFile.inputStream().use { stream ->
                        extractTar(stream, extractDir)
                    }
                } catch (t: Throwable) {
                    // Likely xz-compressed and we can't decode it. Fall back
                    // to scanning the raw bytes for the ELF header of proot.
                    Log.w(TAG, "Tar extraction of deb failed (likely xz), trying raw scan")
                    scanForProotBinary(dataFile, dest)
                    if (dest.exists() && dest.length() > 1000) return
                    throw t
                }

                // Find proot binary in extracted tree
                val prootFile = extractDir.walkTopDown()
                    .firstOrNull { it.name == "proot" && it.isFile && it.length() > 1000 }
                if (prootFile != null) {
                    prootFile.copyTo(dest, overwrite = true)
                    Log.i(TAG, "Extracted proot from deb: ${dest.length()} bytes")
                } else {
                    throw java.io.IOException("proot binary not found in extracted data.tar")
                }
            }
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    /**
     * Last-resort: scan raw bytes of a file for an ELF header preceded by
     * a path containing "proot", and extract the embedded binary. This is
     * a heuristic fallback for xz-compressed tars that Android can't decode.
     */
    private fun scanForProotBinary(data: File, dest: File) {
        val bytes = data.readBytes()
        val elfMagic = byteArrayOf(0x7f, 'E'.code.toByte(), 'L'.code.toByte(), 'F'.code.toByte())
        var i = 0
        while (i < bytes.size - 4) {
            if (bytes[i] == elfMagic[0] && bytes[i+1] == elfMagic[1] &&
                bytes[i+2] == elfMagic[2] && bytes[i+3] == elfMagic[3]) {
                // Check if "proot" appears in the 200 bytes before this ELF header
                val start = maxOf(0, i - 200)
                val before = String(bytes, start, i - start, Charsets.ISO_8859_1)
                if (before.contains("proot")) {
                    // Assume the ELF extends to the next tar header (512-byte aligned)
                    // or to end of file. Take a generous chunk.
                    val end = minOf(bytes.size, i + 2 * 1024 * 1024)  // max 2MB
                    dest.writeBytes(bytes.copyOfRange(i, end))
                    dest.setExecutable(true, false)
                    Log.i(TAG, "Raw-scanned proot binary: ${dest.length()} bytes from offset $i")
                    return
                }
            }
            i++
        }
    }

    /**
     * GH#94: Clean stale sandbox temp files on app startup.
     *
     * Removes files in /tmp and /var/tmp inside the rootfs that are older
     * than 30 days, plus leftover .native-offload-* files in the app's
     * files directory. Avoids /var/laap (user workspace), in-use files,
     * and never follows symlinks.
     */
    suspend fun cleanupStaleTempFiles() = withContext(Dispatchers.IO) {
        val retentionMs = 30L * 24 * 60 * 60 * 1000 // 30 days
        val cutoff = System.currentTimeMillis() - retentionMs
        var cleanedCount = 0

        // Clean /tmp and /var/tmp inside the rootfs
        val tempDirs = listOf(
            File(rootfsDir, "tmp"),
            File(rootfsDir, "var/tmp"),
        )
        for (tempDir in tempDirs) {
            if (!tempDir.exists() || !tempDir.isDirectory) continue
            try {
                tempDir.walkTopDown().forEach { file ->
                    if (file == tempDir) return@forEach
                    // Don't follow symlinks
                    if (java.nio.file.Files.isSymbolicLink(file.toPath())) return@forEach
                    try {
                        if (file.lastModified() < cutoff) {
                            if (file.isFile) {
                                file.delete()
                                cleanedCount++
                            } else if (file.isDirectory) {
                                // Only delete empty dirs (contents already cleaned)
                                if (file.listFiles()?.isEmpty() == true) {
                                    file.delete()
                                    cleanedCount++
                                }
                            }
                        }
                    } catch (e: Exception) {
                        Log.w(TAG, "cleanupStaleTempFiles: skip ${file.absolutePath}: ${e.message}")
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "cleanupStaleTempFiles: error cleaning ${tempDir.absolutePath}: ${e.message}")
            }
        }

        // Clean .native-offload-* leftover files in app filesDir
        val filesDir = context.filesDir
        filesDir.listFiles { f -> f.name.startsWith(".native-offload-") }?.forEach { f ->
            try {
                if (f.lastModified() < cutoff) {
                    f.delete()
                    cleanedCount++
                }
            } catch (e: Exception) {
                Log.w(TAG, "cleanupStaleTempFiles: skip ${f.absolutePath}: ${e.message}")
            }
        }

        if (cleanedCount > 0) {
            Log.i(TAG, "cleanupStaleTempFiles: removed $cleanedCount stale files (retention=${retentionMs / 86400000}d)")
        }
    }

    /**
     * Stage the shared libraries PRoot needs at runtime. The Android Gradle
     * plugin only packages files ending in `.so`; PRoot's DT_NEEDED is
     * `libtalloc.so.2`, so we copy the packaged `libtalloc.so` under its
     * SONAME in a writable app directory and add that directory to
     * LD_LIBRARY_PATH. Idempotent.
     */
    fun ensureProotLibs() {
        prootLibsDir.mkdirs()

        fun stageSoname(sourceName: String, destName: String) {
            val source = File(nativeLibDir, sourceName)
            val dest = File(prootLibsDir, destName)
            if (!source.exists()) {
                Log.w(TAG, "[ProotLibs] missing source: $source")
                return
            }
            if (!dest.exists() || dest.length() != source.length()) {
                source.copyTo(dest, overwrite = true)
                Log.i(TAG, "[ProotLibs] staged $destName from $sourceName")
            }
        }

        // PRoot's ELF header asks for libtalloc.so.2 / libandroid-shmem.so.
        stageSoname("libtalloc.so", "libtalloc.so.2")
        stageSoname("libandroid-shmem.so", "libandroid-shmem.so")
    }

    /**
     * Verify PRoot binary is available, extracting it from assets if needed.
     * The proot-aarch64 asset is shipped in src/main/assets and copied to
     * [filesDir] so it can be made executable (assets themselves are read-only).
     *
     * T-rootfs-shell-fix: validates the ELF header after extraction and retries
     * once if the asset was corrupted by AAPT compression or a partial install.
     * Also falls back to a statically-linked libproot.so shipped in jniLibs if
     * the asset is missing/invalid.
     */
    suspend fun installProotIfNeeded() = withContext(Dispatchers.IO) {
        fun isValidElf(file: File): Boolean {
            if (!file.exists() || file.length() < 4) return false
            return file.inputStream().use { input ->
                val magic = ByteArray(4)
                input.read(magic)
                magic.contentEquals(byteArrayOf(0x7f, 'E'.code.toByte(), 'L'.code.toByte(), 'F'.code.toByte()))
            }
        }

        fun extractFromAssets() {
            Log.i(TAG, "Extracting PRoot binary from assets to $prootBinary")
            prootBinary.delete()
            context.assets.open(PROOT_ASSET).use { input ->
                prootBinary.outputStream().use { output ->
                    input.copyTo(output)
                }
            }
            prootBinary.setExecutable(true, false)
        }

        fun extractFromNativeLib(): Boolean {
            // Some builds ship proot as a JNI library. Try to use it as fallback.
            val candidates = listOf(
                File(nativeLibDir, "libproot.so"),
                File(nativeLibDir, "libproot-aarch64.so"),
            )
            for (candidate in candidates) {
                if (isValidElf(candidate)) {
                    Log.i(TAG, "Falling back to PRoot from native lib: $candidate")
                    candidate.copyTo(prootBinary, overwrite = true)
                    prootBinary.setExecutable(true, false)
                    return true
                }
            }
            return false
        }

        if (!isValidElf(prootBinary)) {
            extractFromAssets()
        }
        if (!isValidElf(prootBinary)) {
            // AAPT may have compressed the asset, or a previous extraction was
            // interrupted. Try once more after deleting the broken file.
            Log.w(TAG, "PRoot ELF validation failed, retrying extraction")
            extractFromAssets()
        }
        if (!isValidElf(prootBinary) && !extractFromNativeLib()) {
            // T-rootfs-robust: final fallback — download PRoot from Termux
            Log.w(TAG, "PRoot binary invalid after all local attempts, trying network download")
            try {
                downloadAndExtractProot()
            } catch (t: Throwable) {
                throw IllegalStateException(
                    "PRoot binary not available or not a valid ELF at $prootBinary. " +
                    "Local extraction and network download both failed: ${t.message}",
                    t
                )
            }
        }

        if (!prootBinary.canExecute() && !prootBinary.setExecutable(true, false)) {
            throw IllegalStateException("Cannot make PRoot binary executable: $prootBinary")
        }

        // [T-rootfs-shell-fix] Termux PRoot and some custom builds link
        // libtalloc dynamically (DT_NEEDED = libtalloc.so.2). ensureProotLibs()
        // stages the packaged libtalloc.so under its SONAME and adds the
        // staging directory to LD_LIBRARY_PATH so PRoot can start on devices
        // where the host does not provide talloc.

        Log.d(TAG, "PRoot binary available at $prootBinary (size=${prootBinary.length()})")
    }

    /**
     * Reset rootfs. Optionally keeps user data (/root).
     * Returns the backup directory if keepUserData is true, null otherwise.
     */
    suspend fun reset(keepUserData: Boolean = false): File? = withContext(Dispatchers.IO) {
        var backupDir: File? = null

        if (keepUserData) {
            val rootHome = File(rootfsDir, "root")
            if (rootHome.exists()) {
                backupDir = File(context.cacheDir, "rootfs-backup-root")
                backupDir.deleteRecursively()
                rootHome.copyRecursively(backupDir, overwrite = true)
            }
        }

        rootfsDir.deleteRecursively()
        installIfNeeded()

        // Restore user data
        if (backupDir != null && backupDir.exists()) {
            val rootHome = File(rootfsDir, "root")
            backupDir.copyRecursively(rootHome, overwrite = true)
            backupDir.deleteRecursively()
        }

        backupDir
    }

    /**
     * Calculate the total size of the rootfs directory in bytes.
     */
    suspend fun getRootfsSize(): Long = withContext(Dispatchers.IO) {
        if (!rootfsDir.exists()) return@withContext 0L
        calculateDirSize(rootfsDir)
    }

    /**
     * Restore user data from a backup directory into /root.
     */
    suspend fun restoreUserData(backupDir: File) = withContext(Dispatchers.IO) {
        if (!backupDir.exists()) return@withContext
        val rootHome = File(rootfsDir, "root")
        rootHome.mkdirs()
        backupDir.copyRecursively(rootHome, overwrite = true)
        backupDir.deleteRecursively()
        Log.i(TAG, "User data restored from $backupDir")
    }

    private fun calculateDirSize(dir: File): Long {
        var total = 0L
        val files = dir.listFiles() ?: return 0L
        for (file in files) {
            total += if (file.isDirectory) {
                calculateDirSize(file)
            } else {
                file.length()
            }
        }
        return total
    }

    /**
     * Ensure session-specific directories exist on the host filesystem.
     */
    fun ensureSessionDirs(sessionId: String) {
        val sessionBase = File(context.filesDir, "laap-sessions/$sessionId")
        val subdirs = listOf("attachments", "offloads", "workspace", "browser")
        for (subdir in subdirs) {
            File(sessionBase, subdir).mkdirs()
        }
    }

    /**
     * Read system DNS servers and search domains from ConnectivityManager,
     * then write resolv.conf into the Alpine rootfs.
     * Mirrors iOS ISHKernel.configureDns / refreshDns.
     * Falls back to 8.8.8.8 / 8.8.4.4 if no system DNS available.
     */
    fun refreshDns() {
        if (!rootfsDir.exists()) return

        val resolvConf = StringBuilder()

        try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            val network = cm?.activeNetwork
            val linkProps: LinkProperties? = if (network != null) cm.getLinkProperties(network) else null

            if (linkProps != null) {
                // Search domains
                val domains = linkProps.domains
                if (!domains.isNullOrBlank()) {
                    resolvConf.append("search $domains\n")
                    Log.i(TAG, "[DNS] search domains: $domains")
                }

                // Nameservers
                val dnsServers = linkProps.dnsServers
                if (dnsServers.isNotEmpty()) {
                    for (server in dnsServers) {
                        val addr = server.hostAddress ?: continue
                        resolvConf.append("nameserver $addr\n")
                        Log.i(TAG, "[DNS] system server: $addr")
                    }
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "[DNS] Failed to read system DNS: ${e.message}")
        }

        // Fallback to public DNS if no system servers were found
        if (!resolvConf.contains("nameserver")) {
            Log.i(TAG, "[DNS] no system DNS — using fallback: 8.8.8.8, 8.8.4.4")
            resolvConf.append("nameserver 8.8.8.8\n")
            resolvConf.append("nameserver 8.8.4.4\n")
        }

        try {
            val file = File(rootfsDir, "etc/resolv.conf")
            file.parentFile?.mkdirs()
            file.writeText(resolvConf.toString())
            Log.i(TAG, "[DNS] resolv.conf updated:\n$resolvConf")
        } catch (e: Exception) {
            Log.e(TAG, "[DNS] Failed to write resolv.conf: ${e.message}")
        }
    }

    /**
     * Copy every file under `assets/default_mount/` into the rootfs, preserving
     * the directory layout. Mirrors iOS RootfsManager.applyDefaultMountOverlay
     * (src/ios/iSH/RootfsManager.swift:153-225) — runs on every boot so shipping
     * updated profile scripts / URL wrappers with an app release just works.
     *
     * Files under `bin` / `sbin` paths get the execute bit set. Existing files
     * are overwritten so users see the latest shipped version even if they
     * previously edited the file — matching iOS behavior.
     *
     * No-op when the asset dir is missing or the rootfs hasn't been extracted.
     */
    suspend fun applyDefaultMountOverlay() = withContext(Dispatchers.IO) {
        if (!rootfsDir.exists()) {
            Log.d(TAG, "[DefaultMount] rootfs missing, skipping overlay")
            return@withContext
        }

        // AssetManager.list() returns an empty array for both "leaf file" and
        // "missing path", so probe for children before recursing — otherwise
        // a missing overlay dir would be mistaken for a single leaf file.
        val rootEntries = try {
            context.assets.list(DEFAULT_MOUNT_ASSET)
        } catch (t: Throwable) {
            null
        }
        if (rootEntries.isNullOrEmpty()) {
            Log.d(TAG, "[DefaultMount] no default_mount assets found, skipping overlay")
            return@withContext
        }

        val startNs = System.nanoTime()
        var fileCount = 0
        try {
            fileCount = copyAssetDir(DEFAULT_MOUNT_ASSET, rootfsDir)
        } catch (t: Throwable) {
            Log.w(TAG, "[DefaultMount] overlay failed: ${t.message}", t)
            return@withContext
        }

        // Mirror iOS removeExternallyManagedMarker() — drop PEP 668 marker so
        // `pip install` Just Works inside this embedded Alpine rootfs even
        // when the shipped pip.conf isn't being read (e.g. pip invoked with
        // --isolated or via a venv). Safe: this is a single-tenant sandbox.
        val markerRemoved = removeExternallyManagedMarker()

        // [T-mcp-cli-readonly-android] Make the shipped laap-mcp-cli Python lib
        // read-only inside the guest so a user can't `vi`-tamper the bundled
        // scripts (mirrors iOS #707). Scoped to /usr/local/lib/laap-mcp-cli/
        // ONLY — the wrapper at /usr/local/bin/laap-mcp-cli stays executable +
        // writable (app-managed). Re-applied on every boot AFTER the copy; the
        // copyAssetDir leaf-copy above re-opens read-only files writable first,
        // so the next app-upgrade overlay still overwrites cleanly.
        val lockedCount = lockMcpCliLibReadOnly()

        val elapsedMs = (System.nanoTime() - startNs) / 1_000_000.0
        Log.i(TAG, "[DefaultMount] Done. $fileCount file(s) overlaid, $markerRemoved EXTERNALLY-MANAGED marker(s) removed, $lockedCount laap-mcp-cli lib path(s) locked read-only in %.1fms".format(elapsedMs))
    }

    /**
     * [T-mcp-cli-readonly-android] Set the `/usr/local/lib/laap-mcp-cli/`
     * subtree read-only for the guest: directories 0555 (read+execute, no
     * write), files 0444 (read-only). Java's File API has no octal chmod, so
     * we use setWritable(false, false) + setReadable(true, false)
     * (+ setExecutable(true, false) on dirs) — the `false` ownerOnly arg makes
     * the permission apply to all users, matching the setReadable style used
     * for libtalloc above. Returns the number of paths adjusted; 0 if the lib
     * dir is absent. Idempotent — the pre-copy unlock in copyAssetDir keeps the
     * upgrade path working across boots.
     */
    private fun lockMcpCliLibReadOnly(): Int {
        val libDir = File(rootfsDir, "usr/local/lib/laap-mcp-cli")
        if (!libDir.isDirectory) return 0
        var count = 0
        // walkBottomUp so child files are locked before their parent dir loses
        // write — dir mode doesn't gate chmod of already-visited children, but
        // bottom-up keeps the intent clear and avoids any traversal surprise.
        for (f in libDir.walkBottomUp()) {
            f.setWritable(false, false)
            f.setReadable(true, false)
            if (f.isDirectory) f.setExecutable(true, false)
            count++
        }
        return count
    }

    /**
     * Remove the PEP 668 EXTERNALLY-MANAGED marker file from every
     * `usr/lib/python3*` directory in the rootfs. Mirrors iOS
     * RootfsManager.removeExternallyManagedMarker (src/ios/iSH/RootfsManager.swift:228-239).
     * Returns the number of markers removed.
     */
    private fun removeExternallyManagedMarker(): Int {
        val usrLib = File(rootfsDir, "usr/lib")
        val children = usrLib.listFiles() ?: return 0
        var removed = 0
        for (entry in children) {
            if (!entry.name.startsWith("python3")) continue
            val marker = File(entry, "EXTERNALLY-MANAGED")
            if (marker.exists() && marker.delete()) {
                Log.i(TAG, "[DefaultMount] Removed EXTERNALLY-MANAGED from ${entry.name}")
                removed++
            }
        }
        return removed
    }

    /**
     * Recursively copy an assets path into [targetBase]. Returns the number of
     * regular files written. Files under /bin/, /sbin/, /usr/bin/, /usr/sbin/,
     * /usr/local/bin/, /usr/local/sbin/ get the execute bit set.
     */
    private fun copyAssetDir(
        assetPath: String,
        targetBase: File,
        prefix: String = "",
        counter: java.util.concurrent.atomic.AtomicInteger? = null,
        onProgress: ((Int) -> Unit)? = null
    ): Int {
        val entries = context.assets.list(assetPath) ?: return 0
        if (entries.isEmpty()) {
            // Leaf: asset is a file. Copy it.
            val dest = File(targetBase, prefix)
            dest.parentFile?.mkdirs()
            // [T-mcp-cli-readonly-android] A prior boot may have set this file
            // (and its dir) read-only — the laap-mcp-cli lib subtree, locked
            // below. Re-open both writable before overwriting, otherwise an app
            // upgrade can't replace the shipped file: truncating an existing
            // file needs write on the FILE, and creating a new one needs write
            // on the PARENT DIR. No-op when already writable / not yet present.
            dest.parentFile?.setWritable(true, true)
            if (dest.exists()) dest.setWritable(true, true)
            context.assets.open(assetPath).use { input ->
                dest.outputStream().use { out -> input.copyTo(out) }
            }
            if (isUnderBinDir(prefix)) {
                dest.setExecutable(true, false)
            }
            counter?.incrementAndGet()
            onProgress?.invoke(counter?.get() ?: 0)
            return 1
        }
        var count = 0
        for (name in entries) {
            val childAsset = "$assetPath/$name"
            val childPrefix = if (prefix.isEmpty()) name else "$prefix/$name"
            count += copyAssetDir(childAsset, targetBase, childPrefix, counter, onProgress)
        }
        return count
    }

    private fun isUnderBinDir(relativePath: String): Boolean {
        val normalized = "/$relativePath"
        return BIN_DIR_PREFIXES.any { normalized.startsWith(it) }
    }

    // --- POSIX tar extraction ---

    /**
     * Extract a POSIX tar stream into the target directory.
     * Handles regular files, directories, symlinks and hardlinks.
     * Does not depend on any external library.
     *
     * Alpine minirootfs places symlinks (e.g. bin/sh -> /bin/busybox) before
     * their target files, and uses absolute symlink targets. We therefore
     * defer link creation until after all regular files have been extracted.
     */
    internal fun extractTar(input: InputStream, targetDir: File) {
        val header = ByteArray(512)
        val deferredLinks = mutableListOf<DeferredLink>()

        while (true) {
            val bytesRead = readFully(input, header)
            if (bytesRead < 512) break

            // Check for end-of-archive (two consecutive zero blocks)
            if (header.all { it == 0.toByte() }) break

            val name = extractString(header, 0, 100)
            val modeOctal = extractString(header, 100, 8)
            val sizeOctal = extractString(header, 124, 12)
            val typeFlag = header[156].toInt().toChar()
            val linkName = extractString(header, 157, 100)
            val mode = modeOctal.trim().toIntOrNull(8) ?: 0

            // Handle GNU/POSIX long names via prefix field (bytes 345-500)
            val prefix = extractString(header, 345, 155)
            val rawName = if (prefix.isNotEmpty()) "$prefix/$name" else name

            // Alpine minirootfs ships entries with a leading "./" (e.g. "./bin/sh").
            // Strip it so File(targetDir, "./bin/sh") doesn't create a literal
            // "." subdirectory or confuse the existence checks used later.
            val fullName = rawName.removePrefix("./")

            if (fullName.isEmpty()) break

            val size = sizeOctal.trim().toLongOrNull(8) ?: 0L
            val outFile = File(targetDir, fullName)

            when (typeFlag) {
                '5', 'D' -> {
                    // Directory
                    outFile.mkdirs()
                }
                '2' -> {
                    // Symbolic link. Defer creation because Alpine places links
                    // like ./bin/sh before their target ./bin/busybox.
                    outFile.parentFile?.mkdirs()
                    deferredLinks.add(
                        DeferredLink(
                            outFile = outFile,
                            linkName = linkName,
                            mode = mode,
                            isSymlink = true
                        )
                    )
                }
                '0', '\u0000' -> {
                    // Regular file (type '0' or null/legacy)
                    outFile.parentFile?.mkdirs()
                    outFile.outputStream().use { output ->
                        var remaining = size
                        val buf = ByteArray(8192)
                        while (remaining > 0) {
                            val toRead = minOf(buf.size.toLong(), remaining).toInt()
                            val n = input.read(buf, 0, toRead)
                            if (n < 0) break
                            output.write(buf, 0, n)
                            remaining -= n
                        }
                    }
                    // Preserve executable permission from tar header
                    if (mode and 0b001_001_001 != 0) {
                        outFile.setExecutable(true, false)
                    }
                    // Skip padding to next 512-byte boundary
                    val remainder = (size % 512).toInt()
                    if (remainder != 0) {
                        skipFully(input, (512 - remainder).toLong())
                    }
                    continue // Already consumed data + padding
                }
                '1' -> {
                    // Hard link — also defer in case target appears later.
                    outFile.parentFile?.mkdirs()
                    deferredLinks.add(
                        DeferredLink(
                            outFile = outFile,
                            linkName = linkName,
                            mode = mode,
                            isSymlink = false
                        )
                    )
                }
                else -> {
                    // Unknown type, skip data
                }
            }

            // Skip data blocks for non-file entries that we didn't consume above
            if (typeFlag != '0' && typeFlag != '\u0000' && size > 0) {
                val blocks = (size + 511) / 512 * 512
                skipFully(input, blocks)
            }
        }

        // Second pass: create symlinks/hardlinks now that targets exist.
        for (link in deferredLinks) {
            createLink(link, targetDir)
        }
    }

    private data class DeferredLink(
        val outFile: File,
        val linkName: String,
        val mode: Int,
        val isSymlink: Boolean,
    )

    private fun createLink(link: DeferredLink, targetDir: File) {
        val outFile = link.outFile
        val rawLinkName = link.linkName
        val mode = link.mode

        // Alpine ships absolute targets like ./bin/sh -> /bin/busybox.
        // Normalize to rootfs-relative paths for fallback copies, and to
        // relative symlink targets so they resolve inside the rootfs.
        val normalizedLinkName = rawLinkName.removePrefix("./").let {
            if (it.startsWith("/")) it.removePrefix("/") else it
        }

        if (link.isSymlink) {
            val resolvedTarget = if (rawLinkName.startsWith("/")) {
                val parentPath = outFile.parentFile?.toPath() ?: targetDir.toPath()
                val absoluteTarget = File(targetDir, normalizedLinkName).toPath()
                try {
                    parentPath.relativize(absoluteTarget).toString()
                } catch (_: Exception) {
                    // Fallback: same directory, last component
                    File(rawLinkName).name
                }
            } else {
                rawLinkName.removePrefix("./")
            }

            try {
                java.nio.file.Files.createSymbolicLink(
                    outFile.toPath(),
                    java.nio.file.Paths.get(resolvedTarget)
                )
            } catch (_: Exception) {
                // Some Android versions restrict symlink creation.
                // Fallback: copy the target so the shell still works.
                val fallbackTarget = File(targetDir, normalizedLinkName)
                if (fallbackTarget.exists()) {
                    fallbackTarget.copyTo(outFile, overwrite = true)
                    if (mode and 0b001_001_001 != 0) {
                        outFile.setExecutable(true, false)
                    }
                    Log.i(TAG, "Symlink fallback: copied ${outFile.name} from $fallbackTarget")
                } else {
                    Log.w(TAG, "Failed to create symlink and target missing: ${outFile.path} -> $rawLinkName (resolved: $resolvedTarget)")
                }
            }
        } else {
            // Hard link fallback: copy the target.
            val linkTarget = File(targetDir, normalizedLinkName)
            if (linkTarget.exists()) {
                linkTarget.copyTo(outFile, overwrite = true)
                if (mode and 0b001_001_001 != 0) {
                    outFile.setExecutable(true, false)
                }
            } else {
                Log.w(TAG, "Hard link target missing: ${outFile.path} -> $normalizedLinkName")
            }
        }
    }

    internal fun extractString(header: ByteArray, offset: Int, length: Int): String {
        val end = minOf(offset + length, header.size)
        var actualEnd = offset
        for (i in offset until end) {
            if (header[i] == 0.toByte()) break
            actualEnd = i + 1
        }
        return String(header, offset, actualEnd - offset, Charset.forName("UTF-8"))
    }

    internal fun readFully(input: InputStream, buf: ByteArray): Int {
        var offset = 0
        while (offset < buf.size) {
            val n = input.read(buf, offset, buf.size - offset)
            if (n < 0) return offset
            offset += n
        }
        return offset
    }

    internal fun skipFully(input: InputStream, count: Long) {
        var remaining = count
        val buf = ByteArray(8192)
        while (remaining > 0) {
            val toRead = minOf(buf.size.toLong(), remaining).toInt()
            val n = input.read(buf, 0, toRead)
            if (n < 0) break
            remaining -= n
        }
    }

    /**
     * InputStream wrapper that reports cumulative bytes read as a 0..1 fraction.
     * Throttles updates so each +1% bump emits at most once. Designed to wrap
     * the asset stream (not the gzip stream) so progress is monotonic against
     * a size we can cheaply know up front.
     */
    private class ProgressInputStream(
        inner: InputStream,
        private val total: Long,
        private val onProgress: (Float) -> Unit,
    ) : FilterInputStream(inner) {
        private var read: Long = 0
        private var lastReportedPercent: Int = -1

        override fun read(): Int {
            val b = super.read()
            if (b >= 0) { read += 1; publish() }
            return b
        }

        override fun read(b: ByteArray, off: Int, len: Int): Int {
            val n = super.read(b, off, len)
            if (n > 0) { read += n; publish() }
            return n
        }

        override fun skip(n: Long): Long {
            val skipped = super.skip(n)
            if (skipped > 0) { read += skipped; publish() }
            return skipped
        }

        private fun publish() {
            if (total <= 0) return
            val pct = ((read * 100) / total).toInt().coerceIn(0, 99)
            if (pct != lastReportedPercent) {
                lastReportedPercent = pct
                onProgress(pct / 100f)
            }
        }
    }

    companion object {
        private const val TAG = "RootfsManager"
        private const val ARCH = "aarch64"
        private const val ROOTFS_UNPACKED_ASSET = "alpine-rootfs"
        private const val ROOTFS_ASSET = "alpine-minirootfs.tar.gz"
        private const val ROOTFS_ASSET_TAR = "alpine-minirootfs.tar"
        private const val PROOT_ASSET = "proot-aarch64"
        private const val DEFAULT_MOUNT_ASSET = "default_mount"

        // Runtime download fallback URLs — used when bundled assets are
        // missing/corrupt or AAPT compression mangles the tar. Keeping these
        // hardcoded (rather than configurable) matches the iOS approach.
        private const val ROOTFS_DOWNLOAD_URL =
            "https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/aarch64/alpine-minirootfs-3.21.3-aarch64.tar.gz"
        private const val PROOT_DOWNLOAD_URL =
            "https://packages.termux.dev/apt/termux-main/pool/main/p/proot/proot_5.1.107.88_aarch64.deb"

        /**
         * Rootfs paths whose contents must be executable. Matches iOS
         * RootfsManager.swift:199 byte-for-byte so the same overlay tree
         * produces identical file modes on both platforms.
         */
        private val BIN_DIR_PREFIXES = listOf(
            "/bin/",
            "/sbin/",
            "/usr/bin/",
            "/usr/sbin/",
            "/usr/local/bin/",
            "/usr/local/sbin/",
        )

        @Volatile
        private var instance: RootfsManager? = null

        fun getInstance(context: Context): RootfsManager {
            return instance ?: synchronized(this) {
                instance ?: RootfsManager(context.applicationContext).also {
                    instance = it
                }
            }
        }
    }
}
