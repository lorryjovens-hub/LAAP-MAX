package org.laap.webapp.zip;

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
 * the device 鈥?no sandbox required.
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
                // Not yet granted 鈥?ask the user so the web app can actually
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