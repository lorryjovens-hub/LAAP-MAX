package org.laap.mobile.sandbox

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Debug receiver for ADB-driven rootfs reset/install.
 *
 * Intended for development / CI only. Allows a connected workstation to
 * uninstall, reinstall, and re-extract the rootfs without manual UI taps:
 *
 *   adb shell am broadcast -a org.laap.mobile.action.RESET_ROOTFS \
 *       -n org.laap.mobile/org.laap.mobile.sandbox.RootfsDebugReceiver
 *
 * The receiver is not exported, so it can only be triggered by the shell
 * user (root/adb) or by the app itself.
 */
class RootfsDebugReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "RootfsDebugReceiver"
        const val ACTION_RESET_ROOTFS = "org.laap.mobile.action.RESET_ROOTFS"
        const val ACTION_RESET_ROOTFS_KEEP_HOME = "org.laap.mobile.action.RESET_ROOTFS_KEEP_HOME"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        if (action != ACTION_RESET_ROOTFS && action != ACTION_RESET_ROOTFS_KEEP_HOME) return

        val keepHome = action == ACTION_RESET_ROOTFS_KEEP_HOME
        Log.i(TAG, "Received $action, keepHome=$keepHome")

        val rootfsManager = RootfsManager.getInstance(context.applicationContext)
        val scope = CoroutineScope(Dispatchers.IO)
        scope.launch {
            try {
                rootfsManager.reset(keepUserData = keepHome)
                Log.i(TAG, "Rootfs reset completed")
            } catch (t: Throwable) {
                Log.e(TAG, "Rootfs reset failed", t)
            }
        }
    }
}
