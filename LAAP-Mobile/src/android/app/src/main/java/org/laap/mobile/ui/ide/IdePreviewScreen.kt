package org.laap.mobile.ui.ide

import android.annotation.SuppressLint
import android.view.ViewGroup
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView

/**
 * Minimal WebView host for IDE project previews. Loads either an
 * `http://localhost:<port>` dev-server URL or any reachable URL the
 * caller passes in. For static-HTML projects the caller pre-resolves
 * the URL — the IDE keeps no laap:// resource resolver here (that path
 * is owned by the chat attachment preview via [LaapImageFetcher]).
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IdePreviewScreen(
    url: String,
    onBack: () -> Unit,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Preview") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        Box(
            Modifier
                .fillMaxSize()
                .padding(padding),
            contentAlignment = Alignment.Center,
        ) {
            if (url.startsWith("http://") || url.startsWith("https://")) {
                IdeWebView(url)
            } else {
                Text("Unsupported preview URL: $url")
            }
        }
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun IdeWebView(url: String) {
    AndroidView(
        factory = { ctx ->
            WebView(ctx).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT,
                )
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                webViewClient = WebViewClient()
                webChromeClient = WebChromeClient()
                loadUrl(url)
            }
        },
        modifier = Modifier.fillMaxSize(),
    )
}
