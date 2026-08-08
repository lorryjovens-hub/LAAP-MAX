/*
 * MobilePerceptionService.kt
 *
 * 移动感知事件采集与发布（Android）
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.laap

import android.content.Context
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Looper

class MobilePerceptionService private constructor(context: Context) {

    companion object {
        @Volatile
        private var instance: MobilePerceptionService? = null

        fun getInstance(context: Context): MobilePerceptionService {
            return instance ?: synchronized(this) {
                instance ?: MobilePerceptionService(context.applicationContext).also { instance = it }
            }
        }
    }

    private val bus = CognitiveBus.getInstance()
    private val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager

    private val locationListener = object : LocationListener {
        override fun onLocationChanged(location: Location) {
            val desc = "lat:${location.latitude}, lon:${location.longitude}, alt:${location.altitude}"
            bus.perceive("gps", desc, confidence = 0.9)
        }

        @Deprecated("Deprecated in Java")
        override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
        override fun onProviderEnabled(provider: String) {}
        override fun onProviderDisabled(provider: String) {}
    }

    fun start() {
        // Initialize passive listeners (actual permissions handled by callers).
    }

    fun perceiveCamera(description: String, confidence: Double = 0.8) {
        bus.perceive("camera", description, confidence = confidence)
    }

    fun perceiveHealth(description: String, confidence: Double = 0.9) {
        bus.perceive("health", description, confidence = confidence)
    }

    fun perceiveNotification(title: String, body: String) {
        bus.perceive("notification", "[$title] $body", confidence = 0.95)
    }

    fun perceiveCalendar(event: String) {
        bus.perceive("calendar", event, confidence = 0.95)
    }

    fun perceiveClipboard(content: String) {
        bus.perceive("clipboard", content, confidence = 0.7)
    }

    fun requestLocationUpdate() {
        try {
            locationManager.requestSingleUpdate(
                LocationManager.GPS_PROVIDER,
                locationListener,
                Looper.getMainLooper()
            )
        } catch (e: SecurityException) {
            bus.publish("qre.perception.error", mapOf("type" to "gps", "error" to e.message.orEmpty()))
        }
    }
}
