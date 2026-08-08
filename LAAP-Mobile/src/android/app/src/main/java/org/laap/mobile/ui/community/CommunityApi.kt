package org.laap.mobile.ui.community

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

/**
 * Thinnest possible client for the LAAP Community Server (desktop).
 *
 * The server runs on the user's desktop at `http://<desktop-ip>:8790` and
 * exposes a JSON catalog of published web apps / websites / games. This
 * client stays dependency-light — plain OkHttp + [org.json] — so the phone
 * can browse, open (play) and publish without any extra server logic.
 */
object CommunityApi {

    data class CommunityApp(
        val id: String,
        val name: String,
        val description: String,
        val type: String,            // "web" | "website" | "game"
        val author: String,
        val url: String,             // absolute or server-relative
        val downloads: Int,
        val createdAt: Long,
    )

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    /** Resolve a (possibly server-relative) app URL against the server root. */
    fun absoluteUrl(serverRoot: String, url: String): String {
        if (url.startsWith("http://") || url.startsWith("https://")) return url
        return serverRoot.trimEnd('/') + "/" + url.trimStart('/')
    }

    /** GET /api/apps → list of published apps. */
    suspend fun listApps(serverRoot: String): Result<List<CommunityApp>> = withContext(Dispatchers.IO) {
        runCatching {
            val req = Request.Builder()
                .url(serverRoot.trimEnd('/') + "/api/apps")
                .get()
                .build()
            client.newCall(req).execute().use { resp ->
                if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code}")
                val text = resp.body?.string() ?: "[]"
                val arr = JSONArray(text)
                buildList {
                    for (i in 0 until arr.length()) {
                        val o = arr.getJSONObject(i)
                        add(
                            CommunityApp(
                                id = o.optString("id"),
                                name = o.optString("name", "未命名"),
                                description = o.optString("description"),
                                type = o.optString("type", "web"),
                                author = o.optString("author", "anonymous"),
                                url = o.optString("url", "/app/${o.optString("id")}/"),
                                downloads = o.optInt("downloads", 0),
                                createdAt = o.optLong("createdAt", 0L),
                            )
                        )
                    }
                }
            }
        }
    }

    /** POST /api/apps with an external-link app (no file upload). */
    suspend fun publishLink(
        serverRoot: String,
        name: String,
        description: String,
        type: String,
        author: String,
        url: String,
    ): Result<Unit> = withContext(Dispatchers.IO) {
        runCatching {
            val body = JSONObject()
                .put("name", name)
                .put("description", description)
                .put("type", type)
                .put("author", author)
                .put("url", url)
                .toString()
            val req = Request.Builder()
                .url(serverRoot.trimEnd('/') + "/api/apps")
                .post(body.toRequestBody("application/json; charset=utf-8".toMediaType()))
                .build()
            client.newCall(req).execute().use { resp ->
                if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code}: ${resp.body?.string()}")
            }
        }
    }

    /**
     * POST /api/apps with a multipart zip containing the built web app.
     * The zip is uploaded as `file`; the server extracts it under /app/<id>/.
     */
    suspend fun publishZip(
        serverRoot: String,
        zipFile: File,
        name: String,
        description: String,
        type: String,
        author: String,
    ): Result<Unit> = withContext(Dispatchers.IO) {
        runCatching {
            val typeField = MultipartBody.Part.createFormData("type", type)
            val nameField = MultipartBody.Part.createFormData("name", name)
            val descField = MultipartBody.Part.createFormData("description", description)
            val authorField = MultipartBody.Part.createFormData("author", author)
            val filePart = MultipartBody.Part.createFormData(
                "file",
                zipFile.name,
                zipFile.asRequestBody("application/zip".toMediaType()),
            )
            val body = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addPart(nameField)
                .addPart(descField)
                .addPart(typeField)
                .addPart(authorField)
                .addPart(filePart)
                .build()
            val req = Request.Builder()
                .url(serverRoot.trimEnd('/') + "/api/apps")
                .post(body)
                .build()
            client.newCall(req).execute().use { resp ->
                if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code}: ${resp.body?.string()}")
            }
        }
    }
}

private fun String.toRequestBody(mediaType: okhttp3.MediaType) =
    okhttp3.RequestBody.create(mediaType, this)