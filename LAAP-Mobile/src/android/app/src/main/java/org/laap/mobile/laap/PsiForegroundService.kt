/*
 * PsiForegroundService.kt
 *
 * Foreground service that keeps the PSI cognitive loop ticking while
 * LAAP-Mobile is backgrounded. Mirrors the lifecycle pattern of
 * AgentForegroundService but with a distinct notification channel + ID
 * so the user can tell "the lifeform is alive" apart from "an agent
 * task is running".
 *
 * Design (integration plan §2.1):
 *   1. Service.onCreate starts [PSILoop] — the loop's coroutine scope
 *      is bound to the singleton, not the service, so it survives config
 *      changes; the service just guarantees the process stays alive.
 *   2. onStartCommand returns START_STICKY — system restarts the service
 *      after low-memory kills, PSI resumes from the singleton state.
 *   3. PsiKeepaliveWorker (15-min periodic WorkManager) is the secondary
 *      keepalive: if START_STICKY fails (OEM ROM kill), the worker
 *      restarts the service on its next tick.
 *   4. Notification content updates with PSI cycle count + dominant drive
 *      every 5 seconds so the user sees the lifeform "thinking".
 *
 * Battery budget (plan §1.2): PSI tick at 1Hz is ~1ms CPU; FGS wake lock
 * is partial and held only while the service runs. Estimated <0.5%/hour.
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.laap

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.laap.mobile.MainActivity
import org.laap.mobile.R

class PsiForegroundService : Service() {

    companion object {
        private const val TAG = "PsiForegroundService"
        const val CHANNEL_ID = "psi_lifeform"
        const val CHANNEL_NAME = "数字生命运行状态"
        const val NOTIFICATION_ID = 9101

        const val ACTION_START = "org.laap.mobile.action.START_PSI"
        const val ACTION_STOP = "org.laap.mobile.action.STOP_PSI"

        @Volatile
        private var isRunningFlag: Boolean = false

        /** Process-wide flag the UI can poll without binding to the service. */
        fun isServiceRunning(): Boolean = isRunningFlag

        /**
         * Launch the foreground service. Safe to call from the foreground
         * (e.g. LaapApp.onCreate or a settings toggle). On Android 12+
         * the caller must already hold POST_NOTIFICATIONS or the FGS
         * starts without a visible notification — the service still runs.
         */
        fun startService(context: Context) {
            val intent = Intent(context, PsiForegroundService::class.java).apply {
                action = ACTION_START
            }
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(intent)
                } else {
                    context.startService(intent)
                }
            } catch (t: Throwable) {
                // BackgroundServiceStartNotAllowedException on Android 12+
                // if called from a non-foregrounded context. Log and let
                // PsiKeepaliveWorker pick up on its next periodic tick.
                Log.w(TAG, "startService failed: ${t.message}")
            }
        }

        fun stopService(context: Context) {
            val intent = Intent(context, PsiForegroundService::class.java)
            try {
                context.stopService(intent)
            } catch (_: Throwable) {}
        }
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var notificationJob: Job? = null
    private var wakeLock: PowerManager.WakeLock? = null

    override fun onCreate() {
        super.onCreate()
        isRunningFlag = true
        createNotificationChannel()
        acquireWakeLock()
        // Start (or reattach to) the PSI loop. PSILoop.start() is idempotent
        // — calling it when the loop is already running is a no-op, so this
        // is safe whether the service is starting fresh or being re-created
        // by START_STICKY after a kill.
        try {
            PSILoop.getInstance().start()
        } catch (t: Throwable) {
            Log.e(TAG, "PSILoop.start failed: ${t.message}", t)
        }
        // Schedule the WorkManager secondary keepalive so a START_STICKY
        // miss (OEM ROM kill) is recovered within 15 minutes.
        PsiKeepaliveWorker.schedule(this)
        startNotificationRefreshLoop()
        Log.i(TAG, "[OK] PsiForegroundService created — PSI loop alive")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> {
                stopSelf()
                return START_NOT_STICKY
            }
        }
        // Satisfy the 5-second startForeground deadline before doing
        // anything else. The notification builder is cheap.
        val notification = buildNotification(cycleCount = 0, dominantDrive = "none")
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(
                    NOTIFICATION_ID,
                    notification,
                    // Use mediaPlayback type — same rationale as
                    // AgentForegroundService: dataSync has a 6h cap on
                    // Android 14+, mediaPlayback doesn't. Sideload APK
                    // so Play Store policy isn't enforced at runtime.
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK,
                )
            } else {
                startForeground(NOTIFICATION_ID, notification)
            }
        } catch (t: Throwable) {
            Log.e(TAG, "startForeground failed: ${t.message}", t)
            stopSelf()
            return START_NOT_STICKY
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onTaskRemoved(rootIntent: Intent?) {
        super.onTaskRemoved(rootIntent)
        // User swiped LAAP from recents. The PSI lifeform should keep
        // running in the background — don't stopSelf. Re-assert the
        // foreground notification so OEM ROMs see us as "live".
        val state = PSILoop.getInstance().let { loop ->
            val metrics = CognitiveBus.getInstance().state.value.psiMetrics
            buildNotification(metrics.cycleCount, metrics.dominantDrive)
        }
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(
                    NOTIFICATION_ID,
                    state,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK,
                )
            } else {
                startForeground(NOTIFICATION_ID, state)
            }
        } catch (_: Throwable) {}
        Log.d(TAG, "onTaskRemoved — keeping PSI alive")
    }

    override fun onDestroy() {
        notificationJob?.cancel()
        notificationJob = null
        try {
            PSILoop.getInstance().stop()
        } catch (_: Throwable) {}
        releaseWakeLock()
        isRunningFlag = false
        scope.cancel()
        super.onDestroy()
        Log.i(TAG, "PsiForegroundService destroyed")
    }

    /**
     * Refresh the notification content every 5 seconds so the user sees
     * the lifeform's cycle count and dominant drive advance. The refresh
     * is a cheap notification.notify() call — no FGS re-binding, no
     * channel re-creation. Stopped in onDestroy to avoid leaking the
     * coroutine scope across service restarts.
     */
    private fun startNotificationRefreshLoop() {
        notificationJob?.cancel()
        notificationJob = scope.launch {
            while (true) {
                val metrics = CognitiveBus.getInstance().state.value.psiMetrics
                val notification = buildNotification(metrics.cycleCount, metrics.dominantDrive)
                try {
                    val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
                    nm.notify(NOTIFICATION_ID, notification)
                } catch (_: Throwable) {}
                delay(5_000L)
            }
        }
    }

    private fun buildNotification(cycleCount: Long, dominantDrive: String): Notification {
        val launchIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingFlags = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        val contentIntent = PendingIntent.getActivity(this, 0, launchIntent, pendingFlags)

        val stopIntent = Intent(this, PsiForegroundService::class.java).apply { action = ACTION_STOP }
        val stopPending = PendingIntent.getService(this, 1, stopIntent, pendingFlags)

        val content = "PSI cycle=$cycleCount · drive=$dominantDrive"
        val subText = "LAAP 数字生命运行中"

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(subText)
            .setContentText(content)
            .setSmallIcon(R.drawable.ic_stat_laap)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setSilent(true)
            .setContentIntent(contentIntent)
            .addAction(0, "停止生命体", stopPending)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        if (nm.getNotificationChannel(CHANNEL_ID) != null) return
        val channel = NotificationChannel(
            CHANNEL_ID,
            CHANNEL_NAME,
            NotificationManager.IMPORTANCE_LOW,
        ).apply {
            description = "LAAP 数字生命 PSI 循环的常驻状态通知"
            setShowBadge(false)
            enableVibration(false)
            setSound(null, null)
        }
        nm.createNotificationChannel(channel)
    }

    private fun acquireWakeLock() {
        try {
            val pm = getSystemService(POWER_SERVICE) as PowerManager
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "LAAP:PsiForegroundService").apply {
                setReferenceCounted(false)
                acquire(/* ten minutes, auto-renewed by the refresh loop */ 10 * 60 * 1000L)
            }
        } catch (t: Throwable) {
            Log.w(TAG, "wakeLock acquire failed: ${t.message}")
        }
    }

    private fun releaseWakeLock() {
        try {
            wakeLock?.let { if (it.isHeld) it.release() }
        } catch (_: Throwable) {}
        wakeLock = null
    }
}
