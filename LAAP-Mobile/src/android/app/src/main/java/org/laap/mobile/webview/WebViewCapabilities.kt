package org.laap.mobile.webview

import android.annotation.SuppressLint
import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.Uri
import android.os.Message
import android.webkit.CookieManager
import android.webkit.GeolocationPermissions
import android.webkit.PermissionRequest
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebView
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

/**
 * Shared capability layer for the WebViews that render user-built apps
 * (the in-chat preview via [org.laap.mobile.ui.preview.WebViewHolder] and
 * the standalone [org.laap.mobile.webapp.WebAppActivity]).
 *
 * Historically these WebViews only enabled JS + DOM storage, so a web app
 * that used the camera, microphone, geolocation or file upload silently
 * failed — the WebView never forwarded those capability requests to the
 * Android runtime permissions LAAP already declares in AndroidManifest.xml
 * (CAMERA, RECORD_AUDIO, ACCESS_FINE_LOCATION, …). This object closes that
 * gap:
 *
 *  - [applySettings] turns on the WebView feature flags those APIs need
 *    (geolocation, media playback without a gesture, cookies).
 *  - [chromeClient] returns a [WebChromeClient] that:
 *      * grants `getUserMedia` (camera/mic) & geolocation only when the
 *        backing Android runtime permission is granted, requesting it via
 *        [CapabilityHost.requestRuntimePermissions] on first use and
 *        re-granting the held web request once the user says yes;
 *      * routes `onShowFileChooser` (file/photo upload) to the host;
 *      * forwards title/icon to the host.
 *
 * The host ([CapabilityHost]) is responsible for the pieces that need an
 * Activity or user-visible state (launching the system file picker, the
 * runtime-permission dialog), so the same capability layer is reusable
 * from both the preview and the standalone WebApp host.
 */
object WebViewCapabilities {

    /**
     * Apply the feature flags required for a full-capability web app. Call
     * once from the WebView's factory.
     *
     * @param allowFileUrls true when the WebView must load `file://`
     *   resources (sandbox previews). When false, file access is locked
     *   down and content is served via WebViewAssetLoader instead.
     */
    @SuppressLint("SetJavaScriptEnabled")
    fun applySettings(webView: WebView, allowFileUrls: Boolean) {
        webView.settings.run {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
            // T-htmlpreview-2d5c4f3d: honour <meta viewport> so 100vh /
            // height:100% resolve against a real viewport instead of a 0x0
            // detached container.
            useWideViewPort = true
            loadWithOverviewMode = true
            // Geolocation needs setGeolocationEnabled(true) + the manifest
            // ACCESS_FINE_LOCATION / ACCESS_COARSE_LOCATION permissions.
            setGeolocationEnabled(true)
            // File access: sandbox previews resolve script/css siblings
            // over file://; the standalone WebApp host serves via
            // WebViewAssetLoader and keeps this locked down.
            allowFileAccess = allowFileUrls
            allowContentAccess = allowFileUrls
            if (allowFileUrls) {
                @Suppress("DEPRECATION")
                allowFileAccessFromFileURLs = true
                @Suppress("DEPRECATION")
                allowUniversalAccessFromFileURLs = true
            }
        }
        // First- + third-party cookies so OAuth/captcha iframes in user
        // apps behave like a real browser tab.
        CookieManager.getInstance().apply {
            setAcceptCookie(true)
            setAcceptThirdPartyCookies(webView, true)
        }
    }

    /**
     * A [WebChromeClient] with the capability handling. [context] is used
     * for permission checks; [scope] drives the async re-grant after the
     * runtime-permission dialog; [host] provides the Activity-dependent
     * callbacks.
     */
    fun chromeClient(
        context: Context,
        scope: CoroutineScope,
        host: CapabilityHost,
    ): WebChromeClient = object : WebChromeClient() {

        override fun onPermissionRequest(request: PermissionRequest) {
            val needed = androidPermissionsFor(request.resources)
            val missing = needed.filter { !isGranted(context, it) }
            if (missing.isEmpty()) {
                request.grant(request.resources)
                return
            }
            // Hold the web request; ask Android for the runtime permission.
            // If the user grants it, re-grant the (still valid) web request;
            // otherwise deny so the page can surface an error.
            scope.launch {
                val ok = host.requestRuntimePermissions(missing)
                if (ok) request.grant(request.resources) else request.deny()
            }
        }

        override fun onGeolocationPermissionsShowPrompt(
            origin: String,
            callback: GeolocationPermissions.Callback,
        ) {
            val needed = listOf(
                Manifest.permission.ACCESS_COARSE_LOCATION,
                Manifest.permission.ACCESS_FINE_LOCATION,
            )
            val missing = needed.filter { !isGranted(context, it) }
            if (missing.isEmpty()) {
                callback.invoke(origin, true, false)
                return
            }
            scope.launch {
                val ok = host.requestRuntimePermissions(missing)
                callback.invoke(origin, ok, false)
            }
        }

        override fun onShowFileChooser(
            webView: WebView,
            filePathCallback: ValueCallback<Array<Uri>>,
            fileChooserParams: FileChooserParams,
        ): Boolean = host.onShowFileChooser(filePathCallback, fileChooserParams)

        override fun onCreateWindow(
            view: WebView,
            isDialog: Boolean,
            isUserGesture: Boolean,
            resultMsg: Message,
        ): Boolean = host.onNewWindow(view, resultMsg)

        override fun onCloseWindow(window: WebView) = host.onCloseWindow(window)

        override fun onReceivedTitle(view: WebView?, title: String?) = host.onTitle(title)

        override fun onReceivedIcon(view: WebView?, icon: Bitmap?) = host.onIcon(icon)
    }

    /** Map a web capability request's resources to the Android runtime
     *  permissions that gate them. Resources with no Android permission
     *  (MIDI sysex, protected media id, cookies) resolve to an empty list
     *  and are granted as soon as the supported ones are. */
    private fun androidPermissionsFor(resources: Array<String>): List<String> {
        val perms = LinkedHashSet<String>()
        if (resources.contains(PermissionRequest.RESOURCE_VIDEO_CAPTURE)) {
            perms.add(Manifest.permission.CAMERA)
        }
        if (resources.contains(PermissionRequest.RESOURCE_AUDIO_CAPTURE)) {
            perms.add(Manifest.permission.RECORD_AUDIO)
        }
        return perms.toList()
    }

    private fun isGranted(context: Context, permission: String): Boolean =
        ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED

    /**
     * Activity-dependent callbacks the WebView needs. The shared layer
     * provides the policy; the host provides the parts that require a
     * real Activity (system file picker, runtime-permission dialog).
     */
    interface CapabilityHost {
        /** Launch the system file/photo picker. Return true if handled. */
        fun onShowFileChooser(
            filePathCallback: ValueCallback<Array<Uri>>,
            fileChooserParams: WebChromeClient.FileChooserParams,
        ): Boolean

        /** Handle `window.open` / target=_blank. Return true if handled. */
        fun onNewWindow(webView: WebView, resultMsg: Message): Boolean

        /** The popup window (if any) was closed. */
        fun onCloseWindow(webView: WebView) {}

        /** Page title changed. */
        fun onTitle(title: String?) {}

        /** Page favicon changed. */
        fun onIcon(icon: Bitmap?) {}

        /**
         * Request the given Android runtime permissions (suspends until the
         * user answers). Return true if all were granted. Defaults to false
         * so hosts that cannot drive a dialog (e.g. a detached preview) fail
         * closed rather than crashing.
         */
        suspend fun requestRuntimePermissions(permissions: List<String>): Boolean = false
    }
}