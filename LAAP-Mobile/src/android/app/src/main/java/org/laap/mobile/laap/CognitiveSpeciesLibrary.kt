/*
 * CognitiveSpeciesLibrary.kt
 *
 * LAAP 认知物种库原生实现（Android）
 * 对应 LAAP 桌面端: harness/laap_coding/core/cognitive_species_library.py
 *
 * M1: Room-backed persistence (AppDatabase v12). The library keeps its
 * in-memory mutableMapOf cache for hot-path reads (PSI tick search) but
 * now persists every register/updateUsage through [SpeciesDao]. On first
 * init the cache hydrates from Room so species survive process restarts.
 * FTS4-powered search() falls back to linear LIKE when the query is
 * empty or unparsable as an FTS4 expression.
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.laap

import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.laap.mobile.data.db.AppDatabase
import org.laap.mobile.data.db.laap.SpeciesDao
import org.laap.mobile.data.db.laap.SpeciesEntity
import org.json.JSONObject
import java.util.Date

enum class SpeciesType {
    COMPONENT, SKILL, ABILITY
}

enum class SpeciesOrigin {
    COMPILED, IMPORTED, EVOLVED
}

data class Species(
    val id: String,
    val name: String,
    val type: SpeciesType,
    val origin: SpeciesOrigin,
    val template: String,
    val props: Map<String, String> = emptyMap(),
    val dependencies: List<String> = emptyList(),
    val tags: List<String> = emptyList(),
    val domain: List<String> = emptyList(),
    var successRate: Double = 1.0,
    var usageCount: Int = 0,
    var qualityScore: Double = 0.0,
    val createdAt: Date = Date(),
    var lastUsed: Date = Date()
)

class CognitiveSpeciesLibrary private constructor() {

    companion object {
        private const val TAG = "SpeciesLibrary"

        @Volatile
        private var instance: CognitiveSpeciesLibrary? = null

        fun getInstance(): CognitiveSpeciesLibrary {
            return instance ?: synchronized(this) {
                instance ?: CognitiveSpeciesLibrary().also { instance = it }
            }
        }

        /**
         * Bind the library to a Room-backed DAO. Must be called once on
         * app startup (LaapApp.onCreate) before any register/search call.
         * Triggers a one-shot background hydrate from the species table
         * so pre-existing entries are visible without a blocking read.
         *
         * Idempotent — calling twice replaces the DAO reference but does
         * NOT re-hydrate; the cache is presumed authoritative by then.
         */
        fun init(context: Context) {
            getInstance().doInit(AppDatabase.getInstance(context).speciesDao())
        }

        // ── mapping helpers (entity ↔ domain object) ───────────────────
        private fun Species.toEntity(): SpeciesEntity = SpeciesEntity(
            id = id,
            name = name,
            type = type.name,
            origin = origin.name,
            template = template,
            propsJson = props.toJson(),
            dependenciesCsv = dependencies.joinToString(","),
            tagsCsv = tags.joinToString(","),
            domainCsv = domain.joinToString(","),
            successRate = successRate,
            usageCount = usageCount,
            qualityScore = qualityScore,
            createdAt = createdAt.time,
            lastUsed = lastUsed.time,
        )

        private fun SpeciesEntity.toDomain(): Species = Species(
            id = id,
            name = name,
            type = runCatching { SpeciesType.valueOf(type) }.getOrDefault(SpeciesType.SKILL),
            origin = runCatching { SpeciesOrigin.valueOf(origin) }.getOrDefault(SpeciesOrigin.IMPORTED),
            template = template,
            props = propsJson.toProps(),
            dependencies = dependenciesCsv.splitCsv(),
            tags = tagsCsv.splitCsv(),
            domain = domainCsv.splitCsv(),
            successRate = successRate,
            usageCount = usageCount,
            qualityScore = qualityScore,
            createdAt = Date(createdAt),
            lastUsed = Date(lastUsed),
        )

        private fun Map<String, String>.toJson(): String =
            try {
                JSONObject().also { o -> forEach { (k, v) -> o.put(k, v) } }.toString()
            } catch (_: Throwable) { "{}" }

        private fun String.toProps(): Map<String, String> =
            if (isBlank()) emptyMap()
            else try {
                val o = JSONObject(this)
                buildMap { for (key in o.keys()) put(key, o.getString(key)) }
            } catch (_: Throwable) { emptyMap() }

        private fun String.splitCsv(): List<String> =
            if (isBlank()) emptyList() else split(',').map { it.trim() }.filter { it.isNotEmpty() }

        /**
         * Escape a user-supplied query so it can be safely concatenated
         * into an FTS4 MATCH expression. Wraps every whitespace-separated
         * token in double quotes and appends a `*` prefix-wildcard so
         * partial-token matches work (e.g. `reac` → `"reac"*). Returns
         * empty string when the input has no usable tokens — the caller
         * then falls back to the linear LIKE query.
         */
        internal fun escapeFts(input: String): String {
            val tokens = input.trim().split(Regex("\\s+"))
                .filter { it.isNotBlank() }
                .map { token ->
                    val cleaned = token.replace("\"", "")
                    if (cleaned.isBlank()) null else "\"$cleaned\"*"
                }
                .filterNotNull()
            return tokens.joinToString(" AND ")
        }
    }

    private val species = mutableMapOf<String, Species>()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    @Volatile
    private var dao: SpeciesDao? = null

    @Volatile
    private var hydrated: Boolean = false

    private fun doInit(dao: SpeciesDao) {
        this.dao = dao
        // Hydrate in the background — register()/updateUsage() will
        // still work synchronously against the in-memory cache while
        // the hydrate is in flight, and any species registered during
        // the hydrate window will be upserted (REPLACE strategy) so
        // the eventual hydrate does not clobber them.
        scope.launch {
            try {
                val rows = dao.getAll()
                synchronized(species) {
                    for (row in rows) {
                        // Don't overwrite a row that was registered after
                        // the hydrate query started — its in-memory copy
                        // is fresher than the on-disk one.
                        if (!species.containsKey(row.id)) {
                            species[row.id] = row.toDomain()
                        }
                    }
                }
                hydrated = true
                Log.i(TAG, "[OK] hydrated ${rows.size} species from Room")
            } catch (t: Throwable) {
                Log.e(TAG, "hydrate failed: ${t.message}", t)
            }
        }
    }

    fun register(species: Species) {
        synchronized(this.species) {
            this.species[species.id] = species
        }
        // Persist async — fire-and-forget. The in-memory cache is the
        // source of truth for the current process; Room is the recovery
        // store for the next launch.
        scope.launch {
            try {
                dao?.upsert(species.toEntity())
            } catch (t: Throwable) {
                Log.w(TAG, "register persist failed: ${t.message}")
            }
        }
    }

    fun get(id: String): Species? = synchronized(species) { species[id] }

    fun listAll(): List<Species> = synchronized(species) { species.values.toList() }

    /**
     * Search by query string + optional type filter. Tries FTS4 first
     * ( Room-backed, O(log N) ), falls back to linear LIKE when:
     *   - DAO isn't bound (pre-init / unit tests)
     *   - query is empty
     *   - FTS4 query syntax errors out
     * Always applies the [type] filter as a post-filter so callers
     * passing SpeciesType.SKILL only get SKILL rows back regardless of
     * which path served the query.
     */
    fun search(query: String, type: SpeciesType? = null): List<Species> {
        val q = query.trim()
        // Fast path: empty query → return everything (filtered by type).
        if (q.isEmpty()) {
            return listAll().filter { type == null || it.type == type }
        }
        // DAO-bound path: prefer FTS4.
        val daoRef = dao
        if (daoRef != null && hydrated) {
            val ftsQuery = escapeFts(q)
            if (ftsQuery.isNotEmpty()) {
                try {
                    val rows = runBlocking { daoRef.searchFts(ftsQuery) }
                    val results = rows.map { it.toDomain() }.filter { type == null || it.type == type }
                    if (results.isNotEmpty()) return results
                    // FTS returned nothing — fall through to linear scan
                    // so partial-token misses still surface hits.
                } catch (t: Throwable) {
                    Log.w(TAG, "FTS search failed, falling back to linear: ${t.message}")
                }
            }
            try {
                val rows = runBlocking { daoRef.searchLinear(q) }
                return rows.map { it.toDomain() }.filter { type == null || it.type == type }
            } catch (t: Throwable) {
                Log.w(TAG, "linear search failed, falling back to memory: ${t.message}")
            }
        }
        // Pre-init fallback: scan the in-memory cache directly. This
        // matches the original pre-MVP behaviour so unit tests that
        // never call init() keep working.
        val lower = q.lowercase()
        return synchronized(species) {
            species.values.filter { sp ->
                (type == null || sp.type == type) &&
                    ("${sp.name} ${sp.tags.joinToString(" ")} ${sp.domain.joinToString(" ")}".lowercase().contains(lower))
            }
        }
    }

    fun updateUsage(id: String, success: Boolean, qualityScore: Double? = null) {
        val sp = synchronized(species) { species[id] } ?: return
        sp.usageCount += 1
        sp.lastUsed = Date()
        qualityScore?.let {
            sp.qualityScore = (sp.qualityScore * (sp.usageCount - 1) + it) / sp.usageCount
        }
        if (success) {
            sp.successRate = minOf(1.0, (sp.successRate * (sp.usageCount - 1) + 1.0) / sp.usageCount)
        }
        // Persist the updated row async.
        scope.launch {
            try {
                dao?.upsert(sp.toEntity())
            } catch (t: Throwable) {
                Log.w(TAG, "updateUsage persist failed: ${t.message}")
            }
        }
    }
}
