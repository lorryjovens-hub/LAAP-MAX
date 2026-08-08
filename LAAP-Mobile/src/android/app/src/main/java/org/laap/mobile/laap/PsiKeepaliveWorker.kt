/*
 * PsiKeepaliveWorker.kt
 *
 * Secondary keepalive for [PsiForegroundService]. WorkManager periodic
 * worker (15-min minimum interval) that re-starts the foreground service
 * if START_STICKY failed (OEM ROM kill, low-memory pressure, etc.).
 *
 * Rationale (integration plan §2.1): "WorkManager 周期任务（15min）作为
 * 二级保活——前台服务被杀后 WorkManager 唤醒重建". The worker is cheap
 * (no IO, no network) so it survives Doze and fires on the maintenance
 * window. Battery budget is ~1ms per invocation.
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.laap

import android.content.Context
import android.util.Log
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.util.concurrent.TimeUnit

class PsiKeepaliveWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {

    companion object {
        private const val TAG = "PsiKeepaliveWorker"
        private const val WORK_NAME = "laap_psi_keepalive"

        /**
         * Enqueue (or replace) the periodic keepalive. Called once on
         * PsiForegroundService.onCreate. Uses KEEP so an existing
         * schedule is preserved across service restarts — calling this
         * multiple times is safe and cheap.
         *
         * Constraints:
         *   - setRequiresBatteryNotLow(true): PSI is a background
         *     "lifeform", not worth draining the user's last 15%.
         *   - NOT setRequiresCharging: PSI is light enough to run on
         *     battery; the charging constraint would be too aggressive
         *     for a 15-min heartbeat.
         */
        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiresBatteryNotLow(true)
                .build()
            val request = PeriodicWorkRequestBuilder<PsiKeepaliveWorker>(
                15, TimeUnit.MINUTES,
            )
                .setConstraints(constraints)
                .build()
            try {
                WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                    WORK_NAME,
                    ExistingPeriodicWorkPolicy.KEEP,
                    request,
                )
                Log.i(TAG, "[OK] periodic keepalive scheduled (15min)")
            } catch (t: Throwable) {
                Log.w(TAG, "schedule failed: ${t.message}")
            }
        }

        /** Cancel the periodic keepalive — called when the user explicitly
         *  stops the lifeform from the settings/notification action. */
        fun cancel(context: Context) {
            try {
                WorkManager.getInstance(context).cancelUniqueWork(WORK_NAME)
            } catch (_: Throwable) {}
        }
    }

    override suspend fun doWork(): Result {
        // Re-launch the foreground service. If it's already running the
        // service's onCreate is a no-op (idempotent PSILoop.start + the
        // system collapses duplicate startForegroundService calls).
        if (!PsiForegroundService.isServiceRunning()) {
            Log.i(TAG, "[OK] keepalive tick — restarting PsiForegroundService")
            PsiForegroundService.startService(applicationContext)
        }
        return Result.success()
    }
}
