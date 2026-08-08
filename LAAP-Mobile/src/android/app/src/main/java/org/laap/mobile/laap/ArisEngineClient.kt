/*
 * ArisEngineClient.kt
 *
 * Aris Engine HTTP 客户端（Android）
 * 对应 LAAP 桌面端: self_model_bridge/aris_engine.py
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.laap

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class ArisEngineClient private constructor() {

    companion object {
        @Volatile
        private var instance: ArisEngineClient? = null

        fun getInstance(): ArisEngineClient {
            return instance ?: synchronized(this) {
                instance ?: ArisEngineClient().also { instance = it }
            }
        }
    }

    var baseUrl: String = "http://127.0.0.1:9876"
    var isLocal: Boolean = false

    private val client = OkHttpClient()
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    suspend fun cycle(input: String, source: String = "mobile"): JSONObject = withContext(Dispatchers.IO) {
        val body = JSONObject().apply {
            put("input", input)
            put("source", source)
        }.toString().toRequestBody(jsonMediaType)

        val request = Request.Builder()
            .url("$baseUrl/cycle")
            .post(body)
            .build()

        client.newCall(request).execute().use { response ->
            JSONObject(response.body?.string() ?: "{}")
        }
    }

    suspend fun getState(): JSONObject = withContext(Dispatchers.IO) {
        val request = Request.Builder().url("$baseUrl/state").build()
        client.newCall(request).execute().use { response ->
            JSONObject(response.body?.string() ?: "{}")
        }
    }

    suspend fun getVitals(): JSONObject = withContext(Dispatchers.IO) {
        val request = Request.Builder().url("$baseUrl/vitals").build()
        client.newCall(request).execute().use { response ->
            JSONObject(response.body?.string() ?: "{}")
        }
    }

    suspend fun observe(llmText: String): JSONObject = withContext(Dispatchers.IO) {
        val body = JSONObject().put("llm_text", llmText).toString().toRequestBody(jsonMediaType)
        val request = Request.Builder()
            .url("$baseUrl/observe")
            .post(body)
            .build()
        client.newCall(request).execute().use { response ->
            JSONObject(response.body?.string() ?: "{}")
        }
    }
}
