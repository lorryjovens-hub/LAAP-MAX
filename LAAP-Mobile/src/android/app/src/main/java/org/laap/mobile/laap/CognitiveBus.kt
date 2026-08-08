/*
 * CognitiveBus.kt
 *
 * LAAP 认知总线原生实现（Android）
 * 对应 LAAP 桌面端: laap/orchestration/cognitive_bus.py
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.laap

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.Date

enum class AttentionFocus {
    USER, TASK, SELF, ENVIRONMENT, MEMORY, PLANNING, LEARNING, IDLE
}

enum class EmotionalValence {
    POSITIVE_HIGH, POSITIVE_MILD, NEUTRAL,
    NEGATIVE_MILD, NEGATIVE_HIGH, CURIOUS, CONFUSED
}

/**
 * PSI homeostatic drives. Mirrors laap/orchestration/psi.py PSIUrge — the
 * five canonical urges that drive PSI behaviour. The legacy [PsiNeed] enum
 * (kept in PSILoop.kt for back-compat with the existing tick pipeline)
 * maps onto these via [PsiNeed.toDrive].
 */
enum class PsiDrive {
    SURVIVAL, AFFILIATION, COMPETENCE, CERTAINTY, CURIOSITY
}

/**
 * PSI cognitive modulators. Mirrors laap/orchestration/psi.py PSIModulator.
 */
enum class PsiModulator {
    ACTIVATION, RESOLUTION, SECURING, SELECTION, COMPETENCE
}

/**
 * PAD (Pleasure / Arousal / Dominance) emotional dimensional state.
 * Mirrors PSIState.{pleasure, arousal, dominance, dominant_feeling} in
 * psi.py — derived from urges + modulators by [PSILoop.updatePadEmotion].
 */
data class PadEmotion(
    val pleasure: Double = 0.0,
    val arousal: Double = 0.0,
    val dominance: Double = 0.0,
    val dominantFeeling: String = "neutral",
)

data class NeedState(
    var competence: Double = 0.7,
    var autonomy: Double = 0.5,
    var relatedness: Double = 0.5,
    var certainty: Double = 0.5,
    var growth: Double = 0.5
) {
    fun strongestNeed(): Pair<String, Double> {
        return mapOf(
            "competence" to (1.0 - competence),
            "autonomy" to (1.0 - autonomy),
            "relatedness" to (1.0 - relatedness),
            "certainty" to (1.0 - certainty),
            "growth" to (1.0 - growth)
        ).maxBy { it.value }.toPair()
    }

    /** Clamps every field into [0,1] — used after delta updates. */
    fun clampAll() {
        competence = competence.coerceIn(0.0, 1.0)
        autonomy = autonomy.coerceIn(0.0, 1.0)
        relatedness = relatedness.coerceIn(0.0, 1.0)
        certainty = certainty.coerceIn(0.0, 1.0)
        growth = growth.coerceIn(0.0, 1.0)
    }
}

data class PsiMetrics(
    val cycleState: String = "idle",      // e.g. idle, perceiving, selecting, acting, learning
    val curiosityIndex: Double = 0.5,      // 好奇心指数
    val trustIndex: Double = 0.5,          // 信任感指标
    val competenceAssessment: Double = 0.7, // 胜任感评估
    val selfPresenceLevel: Double = 0.5,
    val cycleCount: Long = 0,
    val dominantDrive: String = "none",
    val lastImpulse: String = "",
    val padEmotion: PadEmotion = PadEmotion(),
    val lastOutcomeSuccess: Boolean? = null,
    val memoryAssociationsSize: Int = 0,
)

data class CognitiveState(
    val needs: NeedState = NeedState(),
    var emotionalValence: EmotionalValence = EmotionalValence.NEUTRAL,
    var attentionFocus: AttentionFocus = AttentionFocus.IDLE,
    var selfPresenceLevel: Double = 0.5,
    var psiMetrics: PsiMetrics = PsiMetrics(),
    var timestamp: Date = Date()
)

data class CognitiveEvent(
    val topic: String,
    val payload: Map<String, String> = emptyMap(),
    val timestamp: Date = Date()
)

/**
 * Canonical CognitiveBus topic registry. Aligns with:
 *   - memory 第 3 条: qre_* / v12_kernel / need_* / emotion_* / harness_execution_result
 *   - memory 第 17 条: triphase.{domain}.{action}
 *   - integration plan §2.3 CognitiveBusTopics (17 triphase.* topics).
 *
 * Keep this object as the SINGLE source of truth — every publish/subscribe
 * call site should reference these constants rather than string literals
 * so topic drift is caught at compile time.
 */
object CognitiveBusTopics {
    // ── qre.* — perception (memory #3 qre_*) ────────────────────────────
    const val PERCEPTION_MOBILE = "qre.perception.mobile"
    const val PERCEPTION_USER = "qre.perception.user"
    const val PERCEPTION_ERROR = "qre.perception.error"

    // ── psi.* — PSI loop lifecycle & metacognition ──────────────────────
    const val PSI_LIFECYCLE = "psi.lifecycle"
    const val PSI_IMPULSE = "psi.impulse"
    const val PSI_SPECIES_MATCH = "psi.species.match"
    const val PSI_METACOGNITION_INTERVAL = "psi.metacognition.interval"
    const val PSI_METACOGNITION_WEIGHT = "psi.metacognition.weight"

    // ── need.* — homeostatic drive deficit signals (memory #3 need_*) ───
    const val NEED_DEFICIT = "need.deficit"
    const val NEED_SATISFIED = "need.satisfied"

    // ── emotion.* — affective events (memory #3 emotion_*) ──────────────
    const val EMOTION_VALENCE = "emotion.valence"
    const val EMOTION_POSITIVE_MILD = "emotion.positive_mild"
    const val EMOTION_NEGATIVE_MILD = "emotion.negative_mild"
    const val EMOTION_CURIOUS = "emotion.curious"

    // ── harness_execution_result — PSI→Harness feedback channel (memory #3) ─
    const val HARNESS_EXECUTION_RESULT = "harness_execution_result"

    // ── v12_kernel — kernel-level orchestration token (memory #3) ───────
    const val V12_KERNEL = "v12_kernel"

    // ── triphase.* — 17 module-aligned topics (memory #17, plan §2.3) ───
    // Each constant maps 1:1 to a file in the proposed org.laap.mobile
    // .laap.triphase subpackage (plan §2.3 module tree). Domain matches
    // the triphase_engine source module name; action is the primary verb
    // the M2 Kotlin port will emit/consume on that topic.
    const val TRIPHASE_CORE_INTERFERENCE     = "triphase.core.interference"     // Trit/PhaseState/Affinity
    const val TRIPHASE_PHASESTATE_ROTATE     = "triphase.phasestate.rotate"     // PhaseState.kt
    const val TRIPHASE_AFFINITY_RESONATE     = "triphase.affinity.resonate"     // Affinity.kt
    const val TRIPHASE_MEMORY_STORE          = "triphase.memory.store"          // ComplexResonantMemory
    const val TRIPHASE_MEMORY_RETRIEVE       = "triphase.memory.retrieve"
    const val TRIPHASE_MEMORY_CONSOLIDATE    = "triphase.memory.consolidate"
    const val TRIPHASE_HYPOTHESIS_DIVERGE    = "triphase.hypothesis.diverge"    // HypothesisEcosystem
    const val TRIPHASE_HYPOTHESIS_COMPETE    = "triphase.hypothesis.compete"
    const val TRIPHASE_METACOGNITION_ASSESS  = "triphase.metacognition.assess"  // MetacognitiveMonitor
    const val TRIPHASE_REFLECTION_INVERT     = "triphase.reflection.invert"     // SpirReflection
    const val TRIPHASE_CODEGRAPH_VERIFY      = "triphase.codegraph.verify"      // TriphaseCodeGraph
    const val TRIPHASE_CAUSAL_INFER          = "triphase.causal.infer"          // CausalTensorEngine
    const val TRIPHASE_PIPELINE_ROUTE        = "triphase.pipeline.route"        // TokenPipeline (PGTP)
    const val TRIPHASE_KDA_UPDATE            = "triphase.kda.update"            // KdaWorkingMemory
    const val TRIPHASE_KDA_RETRIEVE          = "triphase.kda.retrieve"
    const val TRIPHASE_ATTNRES_RETRIEVE      = "triphase.attnres.retrieve"      // AttnResRetrieval
    const val TRIPHASE_LATENTMOE_ROUTE       = "triphase.latentmoe.route"       // LatentMoeRouter
    const val TRIPHASE_GROUNDING_VERIFY      = "triphase.grounding.verify"      // GroundingPcg
    const val TRIPHASE_SELFHEAL_ANOMALY      = "triphase.selfheal.anomaly"      // SelfHealEngine
    const val TRIPHASE_RSI_PROPOSAL          = "triphase.rsi.proposal"          // TriphaseRsiEngine
    const val TRIPHASE_RSI_DEPLOY            = "triphase.rsi.deploy"
    const val TRIPHASE_INVARIANT_AUDIT       = "triphase.invariant.audit"       // TriphaseInvariantCore

    /** All 17+ triphase.* topics as an immutable set, for diagnostics. */
    val TRIPHASE_TOPICS: Set<String> = setOf(
        TRIPHASE_CORE_INTERFERENCE, TRIPHASE_PHASESTATE_ROTATE, TRIPHASE_AFFINITY_RESONATE,
        TRIPHASE_MEMORY_STORE, TRIPHASE_MEMORY_RETRIEVE, TRIPHASE_MEMORY_CONSOLIDATE,
        TRIPHASE_HYPOTHESIS_DIVERGE, TRIPHASE_HYPOTHESIS_COMPETE,
        TRIPHASE_METACOGNITION_ASSESS, TRIPHASE_REFLECTION_INVERT,
        TRIPHASE_CODEGRAPH_VERIFY, TRIPHASE_CAUSAL_INFER, TRIPHASE_PIPELINE_ROUTE,
        TRIPHASE_KDA_UPDATE, TRIPHASE_KDA_RETRIEVE, TRIPHASE_ATTNRES_RETRIEVE,
        TRIPHASE_LATENTMOE_ROUTE, TRIPHASE_GROUNDING_VERIFY,
        TRIPHASE_SELFHEAL_ANOMALY, TRIPHASE_RSI_PROPOSAL, TRIPHASE_RSI_DEPLOY,
        TRIPHASE_INVARIANT_AUDIT,
    )
}

class CognitiveBus private constructor() {

    companion object {
        @Volatile
        private var instance: CognitiveBus? = null

        fun getInstance(): CognitiveBus {
            return instance ?: synchronized(this) {
                instance ?: CognitiveBus().also { instance = it }
            }
        }
    }

    private val _state = MutableStateFlow(CognitiveState())
    val state: StateFlow<CognitiveState> = _state.asStateFlow()

    private val subscribers = mutableMapOf<String, MutableList<(CognitiveEvent) -> Unit>>()

    fun publish(topic: String, payload: Map<String, String> = emptyMap()) {
        val event = CognitiveEvent(topic, payload)
        subscribers[topic]?.forEach { handler ->
            try {
                handler(event)
            } catch (_: Throwable) {
                // Subscriber errors must not break the bus — keep dispatching.
            }
        }
        applyEvent(event)
    }

    fun subscribe(topic: String, handler: (CognitiveEvent) -> Unit) {
        subscribers.getOrPut(topic) { mutableListOf() }.add(handler)
    }

    /** Remove every handler the caller registered for [topic]. */
    fun unsubscribe(topic: String, handler: (CognitiveEvent) -> Unit) {
        subscribers[topic]?.removeAll { it === handler }
    }

    fun updateNeeds(updater: (NeedState) -> Unit) {
        val current = _state.value
        val newNeeds = current.needs.copy()
        updater(newNeeds)
        newNeeds.clampAll()
        _state.value = current.copy(needs = newNeeds, timestamp = Date())
    }

    fun updatePsiMetrics(updater: (PsiMetrics) -> Unit) {
        val current = _state.value
        val newMetrics = current.psiMetrics.copy()
        updater(newMetrics)
        _state.value = current.copy(psiMetrics = newMetrics, timestamp = Date())
    }

    fun perceive(type: String, description: String, location: String? = null, confidence: Double = 0.5) {
        val payload = mutableMapOf(
            "type" to type,
            "description" to description,
            "confidence" to "%.3f".format(confidence)
        )
        location?.let { payload["location"] = it }
        publish(CognitiveBusTopics.PERCEPTION_MOBILE, payload)
    }

    /**
     * Publish a harness execution result. PSI learns from this via
     * [PSILoop.learnFromOutcome] (aligned with psi.py#L166). The payload
     * schema is part of the public event contract — keep field names
     * stable across releases.
     */
    fun publishHarnessResult(
        action: String,
        outcomeType: String,
        success: Boolean,
        fitness: Double = if (success) 1.0 else 0.0,
        error: String? = null,
        speciesId: String? = null,
    ) {
        val payload = mutableMapOf(
            "action" to action,
            "outcome_type" to outcomeType,
            "success" to success.toString(),
            "fitness" to "%.3f".format(fitness),
        )
        error?.let { payload["error"] = it }
        speciesId?.let { payload["species_id"] = it }
        publish(CognitiveBusTopics.HARNESS_EXECUTION_RESULT, payload)
    }

    /** Publish a v12_kernel orchestration token (memory #3). */
    fun publishV12KernelToken(stage: String, payload: Map<String, String> = emptyMap()) {
        val merged = mutableMapOf("stage" to stage)
        merged.putAll(payload)
        publish(CognitiveBusTopics.V12_KERNEL, merged)
    }

    private fun applyEvent(event: CognitiveEvent) {
        val current = _state.value
        val next = when (event.topic) {
            CognitiveBusTopics.PERCEPTION_MOBILE -> current.copy(
                attentionFocus = AttentionFocus.ENVIRONMENT,
                emotionalValence = EmotionalValence.CURIOUS,
                needs = current.needs.copy(growth = (current.needs.growth + 0.05).coerceAtMost(1.0))
            )
            CognitiveBusTopics.PERCEPTION_USER -> current.copy(
                attentionFocus = AttentionFocus.USER,
                needs = current.needs.copy(relatedness = (current.needs.relatedness + 0.03).coerceAtMost(1.0))
            )
            CognitiveBusTopics.EMOTION_NEGATIVE_MILD ->
                current.copy(emotionalValence = EmotionalValence.NEGATIVE_MILD)
            CognitiveBusTopics.EMOTION_CURIOUS ->
                current.copy(emotionalValence = EmotionalValence.CURIOUS)
            CognitiveBusTopics.HARNESS_EXECUTION_RESULT -> {
                // Reflect the success flag on PsiMetrics so UI can render
                // the latest outcome without subscribing to the raw event.
                val success = event.payload["success"]?.toBooleanStrictOrNull()
                current.copy(
                    psiMetrics = current.psiMetrics.copy(lastOutcomeSuccess = success),
                    attentionFocus = AttentionFocus.TASK,
                )
            }
            CognitiveBusTopics.NEED_DEFICIT -> {
                val need = event.payload["need"].orEmpty()
                val drive = event.payload["drive"]?.toDoubleOrNull() ?: 0.0
                // Surface the deficit on attentionFocus when severe — drives
                // PSI's selection phase on the next tick.
                if (drive > 0.7) current.copy(attentionFocus = AttentionFocus.SELF) else current
            }
            CognitiveBusTopics.PSI_LIFECYCLE -> {
                // Pure lifecycle signal — no state mutation beyond timestamp.
                current
            }
            else -> current
        }
        _state.value = next.copy(timestamp = Date())
    }
}
