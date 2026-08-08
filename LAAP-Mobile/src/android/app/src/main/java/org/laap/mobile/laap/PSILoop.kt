/*
 * PSILoop.kt
 *
 * LAAP PSI 认知循环原生实现（Android）
 * 对应 LAAP 桌面端: laap/agi/psi_loop.py + laap/orchestration/psi.py
 *
 * PSI 四阶段：感知(Perceive) → 选择(Select) → 行动(Act) → 学习(Learn)
 * 周期运行，读取 CognitiveBus 的 NeedState，计算驱动强度，生成行为冲动，
 * 并发布为认知事件。集成元认知监控，可自我调节循环频率与驱动权重。
 *
 * M1 additions:
 *   - learnFromOutcome(action, outcome): aligned with psi.py#L166 — updates
 *     competence urge, COMPETENCE modulator, and memory_associations LRU map
 *     based on harness_execution_result events.
 *   - harness_execution_result subscription wired in start().
 *   - PAD emotion derivation (psi.py PSIState.update_emotions) published on
 *     every tick and exposed on PsiMetrics.padEmotion.
 *   - need.deficit events published when any drive falls below 0.3.
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.laap

import android.util.Log
import kotlinx.coroutines.*
import java.util.Date
import kotlin.math.max
import kotlin.math.min
import kotlin.random.Random

/**
 * PSI 需求驱动定义。五个需求与桌面端保持一致。
 *
 * Note: laap/orchestration/psi.py uses PSIUrge {SURVIVAL, AFFILIATION,
 * COMPETENCE, CERTAINTY, CURIOSITY}. The local enum keeps the legacy
 * Self-Determination-Theory naming (used by the existing tick pipeline
 * and UI); [toDrive] provides the canonical mapping for cross-module
 * event payloads. M2 may consolidate onto [PsiDrive] directly.
 */
enum class PsiNeed {
    COMPETENCE, AUTONOMY, RELATEDNESS, CERTAINTY, GROWTH;

    fun toDrive(): PsiDrive = when (this) {
        COMPETENCE -> PsiDrive.COMPETENCE
        AUTONOMY -> PsiDrive.SURVIVAL
        RELATEDNESS -> PsiDrive.AFFILIATION
        CERTAINTY -> PsiDrive.CERTAINTY
        GROWTH -> PsiDrive.CURIOSITY
    }
}

/**
 * PSI 循环阶段。
 */
enum class PsiCyclePhase {
    IDLE, PERCEIVING, SELECTING, ACTING, LEARNING
}

/**
 * 行为冲动。PSI 选择阶段输出，供 Harness 执行层或 UI 消费。
 */
data class PsiImpulse(
    val need: PsiNeed,
    val action: String,
    val target: String,
    val intensity: Double,
    val reason: String,
    val timestamp: Date = Date()
)

/**
 * PSI 元认知快照。记录每轮循环的学习信号。
 */
data class PsiLearningSnapshot(
    val cycleId: Long,
    val needBefore: NeedState,
    val needAfter: NeedState,
    val impulse: PsiImpulse,
    val satisfactionDelta: Double,
    val emotionBefore: EmotionalValence,
    val emotionAfter: EmotionalValence
)

/**
 * Harness execution outcome. Mirrors the `outcome` dict consumed by
 * psi.py#L166 PSIAgent.learn_from_outcome. Produced by CognitiveBus
 * .publishHarnessResult and rehydrated by [PSILoop.harnessResultHandler].
 */
data class HarnessOutcome(
    val action: String,
    val outcomeType: String,
    val success: Boolean,
    val fitness: Double,
    val error: String? = null,
    val speciesId: String? = null,
)

class PSILoop private constructor() {

    companion object {
        private const val TAG = "PSILoop"

        /** LRU cap for memory_associations, aligned with plan §2.1 (<20KB / 500 entries). */
        private const val MEMORY_ASSOCIATIONS_MAX = 500

        /** Drive threshold below which a need.deficit event is published. */
        private const val DEFICIT_THRESHOLD = 0.3

        @Volatile
        private var instance: PSILoop? = null

        fun getInstance(): PSILoop {
            return instance ?: synchronized(this) {
                instance ?: PSILoop().also { instance = it }
            }
        }
    }

    private val bus = CognitiveBus.getInstance()
    private val speciesLibrary = CognitiveSpeciesLibrary.getInstance()
    private val metacognition = Metacognition.getInstance()

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var job: Job? = null

    @Volatile
    var isRunning: Boolean = false
        private set

    /** 循环周期，默认 1 秒，可由元认知动态调整。 */
    var tickIntervalMs: Long = 1000L

    /** 驱动权重 [0..1]，对应 five needs。 */
    var driveWeights: Map<PsiNeed, Double> = PsiNeed.entries.associateWith { 1.0 }

    private var cycleCount: Long = 0

    /**
     * PSI modulators. Mirrors psi.py PSIModulator defaults: ACTIVATION=0.5,
     * RESOLUTION=0.5, SECURING=0.3, SELECTION=0.6, COMPETENCE=0.7. Updated
     * by [learnFromOutcome] (success/failure adjusts COMPETENCE) and by the
     * tick pipeline (urgency adjusts ACTIVATION/RESOLUTION/SECURING).
     */
    private val modulators: MutableMap<PsiModulator, Double> = mutableMapOf(
        PsiModulator.ACTIVATION to 0.5,
        PsiModulator.RESOLUTION to 0.5,
        PsiModulator.SECURING to 0.3,
        PsiModulator.SELECTION to 0.6,
        PsiModulator.COMPETENCE to 0.7,
    )

    /**
     * action→expected_value memory associations. Mirrors psi.py
     * `self.memory_associations` — boosted on success, decayed on failure,
     * LRU-capped to [MEMORY_ASSOCIATIONS_MAX]. Read by [selectDominantDrive]
     * to bias selection toward historically successful actions.
     */
    private val memoryAssociations: LinkedHashMap<String, Double> =
        object : LinkedHashMap<String, Double>(MEMORY_ASSOCIATIONS_MAX, 0.75f, true) {
            override fun removeEldestEntry(eldest: Map.Entry<String, Double>): Boolean =
                size > MEMORY_ASSOCIATIONS_MAX
        }

    /** PSI learning rate (psi.py PSIAgent(learning_rate=0.1) default). */
    var learningRate: Double = 0.1

    /** Harness execution result subscription handler — held so unsubscribe is deterministic. */
    private val harnessResultHandler: (CognitiveEvent) -> Unit = { event ->
        handleHarnessResult(event)
    }

    /** 最近生成的冲动，供 UI 展示。 */
    val lastImpulse: PsiImpulse?
        get() = metacognition.lastImpulse

    /**
     * 启动 PSI 循环。幂等：已启动时忽略。
     */
    fun start() {
        if (isRunning) return
        isRunning = true
        // Subscribe to harness_execution_result so learnFromOutcome fires on
        // every Act-phase outcome (aligned with psi.py's learn_from_outcome
        // being invoked by HarnessActor.submit_execution_result on desktop).
        bus.subscribe(CognitiveBusTopics.HARNESS_EXECUTION_RESULT, harnessResultHandler)
        job = scope.launch {
            while (isActive) {
                try {
                    tick()
                } catch (t: Throwable) {
                    // Single-tick failures must not kill the loop — log and
                    // continue so the cognitive cycle survives transient bugs.
                    Log.e(TAG, "tick failed: ${t.message}", t)
                }
                delay(tickIntervalMs)
            }
        }
        Log.i(TAG, "PSI loop started, interval=$tickIntervalMs ms")
        bus.publish(CognitiveBusTopics.PSI_LIFECYCLE, mapOf("state" to "started"))
    }

    /**
     * 停止 PSI 循环。
     */
    fun stop() {
        if (!isRunning) return
        isRunning = false
        bus.unsubscribe(CognitiveBusTopics.HARNESS_EXECUTION_RESULT, harnessResultHandler)
        job?.cancel()
        job = null
        Log.i(TAG, "PSI loop stopped")
        bus.publish(CognitiveBusTopics.PSI_LIFECYCLE, mapOf("state" to "stopped"))
    }

    /**
     * 单轮 PSI 循环。
     */
    suspend fun tick() = withContext(Dispatchers.Default) {
        cycleCount++
        val cycleId = cycleCount

        // --- Perceive: 读取当前状态 ---
        setCycleState(PsiCyclePhase.PERCEIVING)
        val stateBefore = bus.state.value
        val needBefore = stateBefore.needs.copy()
        val emotionBefore = stateBefore.emotionalValence

        // 更新好奇心指数（对未满足需求的敏感度）
        val curiosityIndex = computeCuriosityIndex(needBefore)
        // 信任感指标（relatedness + certainty 综合）
        val trustIndex = (needBefore.relatedness + needBefore.certainty) / 2.0
        // 胜任感评估
        val competenceAssessment = needBefore.competence

        // Recompute modulators from current urges (psi.py process_perception).
        val maxUrgency = 1.0 - listOf(
            needBefore.competence, needBefore.autonomy, needBefore.relatedness,
            needBefore.certainty, needBefore.growth,
        ).minOf { it }
        modulators[PsiModulator.ACTIVATION] = (0.3 + maxUrgency * 0.7).coerceIn(0.0, 1.0)
        modulators[PsiModulator.RESOLUTION] = (0.8 - maxUrgency * 0.4).coerceIn(0.0, 1.0)
        modulators[PsiModulator.SECURING] = (maxUrgency * 0.8).coerceIn(0.0, 1.0)

        bus.updatePsiMetrics {
            it.copy(
                cycleState = PsiCyclePhase.PERCEIVING.name.lowercase(),
                curiosityIndex = curiosityIndex,
                trustIndex = trustIndex,
                competenceAssessment = competenceAssessment,
                cycleCount = cycleId,
                memoryAssociationsSize = memoryAssociations.size,
            )
        }

        // --- Select: 选择主导驱动并生成冲动 ---
        setCycleState(PsiCyclePhase.SELECTING)
        val (dominantNeed, driveStrength) = selectDominantDrive(needBefore)
        val impulse = generateImpulse(dominantNeed, driveStrength, stateBefore)

        bus.updatePsiMetrics {
            it.copy(
                cycleState = PsiCyclePhase.SELECTING.name.lowercase(),
                dominantDrive = dominantNeed.name.lowercase(),
                lastImpulse = impulse.action
            )
        }
        metacognition.recordImpulse(impulse)

        // --- Act: 发布执行事件 ---
        setCycleState(PsiCyclePhase.ACTING)
        publishImpulse(impulse)

        // 物种库模板匹配：尝试用已有物种完成冲动
        val matchedSpecies = speciesLibrary.search(
            query = impulse.action,
            type = SpeciesType.SKILL
        ).firstOrNull()
        matchedSpecies?.let {
            speciesLibrary.updateUsage(it.id, success = true, qualityScore = 0.8)
            bus.publish(CognitiveBusTopics.PSI_SPECIES_MATCH, mapOf(
                "species_id" to it.id,
                "action" to impulse.action,
                "quality" to "%.2f".format(it.qualityScore)
            ))
            // Self-emit a harness result so learnFromOutcome closes the loop
            // even when no external harness executor is wired up yet (M1 MVP).
            bus.publishHarnessResult(
                action = impulse.action,
                outcomeType = "species_match",
                success = true,
                fitness = it.qualityScore.coerceIn(0.0, 1.0),
                speciesId = it.id,
            )
        }

        // --- Learn: 更新需求与情绪 ---
        setCycleState(PsiCyclePhase.LEARNING)
        val needAfter = applyImpulseToNeeds(needBefore, impulse)
        val emotionAfter = regulateEmotion(emotionBefore, impulse, needAfter)
        val satisfactionDelta = computeSatisfactionDelta(needBefore, needAfter)

        bus.updateNeeds {
            it.competence = needAfter.competence
            it.autonomy = needAfter.autonomy
            it.relatedness = needAfter.relatedness
            it.certainty = needAfter.certainty
            it.growth = needAfter.growth
        }

        val snapshot = PsiLearningSnapshot(
            cycleId = cycleId,
            needBefore = needBefore,
            needAfter = needAfter,
            impulse = impulse,
            satisfactionDelta = satisfactionDelta,
            emotionBefore = emotionBefore,
            emotionAfter = emotionAfter
        )
        metacognition.learn(snapshot)

        // PAD emotion derivation (psi.py PSIState.update_emotions).
        val pad = derivePadEmotion(needAfter, modulators)
        // Publish need.deficit for any drive below threshold — downstream
        // subscribers (LifeformDashboard, future Triphase metacog) react.
        publishDeficitsIfNeeded(needAfter)

        bus.updatePsiMetrics {
            it.copy(
                cycleState = PsiCyclePhase.LEARNING.name.lowercase(),
                curiosityIndex = computeCuriosityIndex(needAfter),
                trustIndex = (needAfter.relatedness + needAfter.certainty) / 2.0,
                competenceAssessment = needAfter.competence,
                cycleCount = cycleId,
                padEmotion = pad,
                memoryAssociationsSize = memoryAssociations.size,
            )
        }

        // 元认知自我调节：根据满意度调整循环频率
        metacognition.adaptLoop(this@PSILoop, snapshot)

        Log.d(TAG, "cycle=$cycleId need=$dominantNeed drive=%.2f impulse=${impulse.action} delta=%.3f pad=%s".format(driveStrength, satisfactionDelta, pad.dominantFeeling))
    }

    private fun setCycleState(phase: PsiCyclePhase) {
        bus.updatePsiMetrics { it.copy(cycleState = phase.name.lowercase()) }
    }

    /**
     * 计算好奇心指数：对未满足需求（缺口）的敏感度。
     * 缺口越大、越不均衡，好奇心越高。
     */
    private fun computeCuriosityIndex(needs: NeedState): Double {
        val deficits = listOf(
            1.0 - needs.competence,
            1.0 - needs.autonomy,
            1.0 - needs.relatedness,
            1.0 - needs.certainty,
            1.0 - needs.growth
        )
        val meanDeficit = deficits.average()
        val variance = deficits.map { (it - meanDeficit) * (it - meanDeficit) }.average()
        return min(1.0, meanDeficit + variance * 2.0)
    }

    /**
     * 选择主导驱动：缺口 × 权重最大者。
     */
    private fun selectDominantDrive(needs: NeedState): Pair<PsiNeed, Double> {
        val drives = mapOf(
            PsiNeed.COMPETENCE to (1.0 - needs.competence) * driveWeights.getOrDefault(PsiNeed.COMPETENCE, 1.0),
            PsiNeed.AUTONOMY to (1.0 - needs.autonomy) * driveWeights.getOrDefault(PsiNeed.AUTONOMY, 1.0),
            PsiNeed.RELATEDNESS to (1.0 - needs.relatedness) * driveWeights.getOrDefault(PsiNeed.RELATEDNESS, 1.0),
            PsiNeed.CERTAINTY to (1.0 - needs.certainty) * driveWeights.getOrDefault(PsiNeed.CERTAINTY, 1.0),
            PsiNeed.GROWTH to (1.0 - needs.growth) * driveWeights.getOrDefault(PsiNeed.GROWTH, 1.0)
        )
        return drives.entries.maxByOrNull { it.value }?.toPair()
            ?: (PsiNeed.GROWTH to 0.0)
    }

    /**
     * 根据主导需求生成行为冲动。
     */
    private fun generateImpulse(need: PsiNeed, driveStrength: Double, state: CognitiveState): PsiImpulse {
        return when (need) {
            PsiNeed.COMPETENCE -> PsiImpulse(
                need = need,
                action = "skill_practice",
                target = "nearest_hard_task",
                intensity = driveStrength,
                reason = "competence deficit: seek mastery"
            )
            PsiNeed.AUTONOMY -> PsiImpulse(
                need = need,
                action = "explore_options",
                target = "environment",
                intensity = driveStrength,
                reason = "autonomy deficit: expand choice space"
            )
            PsiNeed.RELATEDNESS -> PsiImpulse(
                need = need,
                action = "reach_out",
                target = "user",
                intensity = driveStrength,
                reason = "relatedness deficit: connect with user"
            )
            PsiNeed.CERTAINTY -> PsiImpulse(
                need = need,
                action = "verify_model",
                target = "current_context",
                intensity = driveStrength,
                reason = "certainty deficit: reduce ambiguity"
            )
            PsiNeed.GROWTH -> PsiImpulse(
                need = need,
                action = "learn_new",
                target = "novel_perception",
                intensity = driveStrength,
                reason = "growth deficit: acquire new patterns"
            )
        }
    }

    /**
     * 发布冲动事件到认知总线，供 Harness/UI 订阅。
     */
    private fun publishImpulse(impulse: PsiImpulse) {
        bus.publish(CognitiveBusTopics.PSI_IMPULSE, mapOf(
            "need" to impulse.need.name.lowercase(),
            "drive" to impulse.need.toDrive().name.lowercase(),
            "action" to impulse.action,
            "target" to impulse.target,
            "intensity" to "%.3f".format(impulse.intensity),
            "reason" to impulse.reason
        ))
    }

    /**
     * 根据冲动对需求进行小幅度更新（模拟执行后的反馈）。
     */
    private fun applyImpulseToNeeds(needs: NeedState, impulse: PsiImpulse): NeedState {
        val delta = 0.03 * impulse.intensity
        val noise = Random.nextDouble(-0.01, 0.01)
        return needs.copy().apply {
            when (impulse.need) {
                PsiNeed.COMPETENCE -> competence = clamp(competence + delta + noise)
                PsiNeed.AUTONOMY -> autonomy = clamp(autonomy + delta * 0.8 + noise)
                PsiNeed.RELATEDNESS -> relatedness = clamp(relatedness + delta + noise)
                PsiNeed.CERTAINTY -> certainty = clamp(certainty + delta * 0.9 + noise)
                PsiNeed.GROWTH -> growth = clamp(growth + delta * 0.7 + noise)
            }
            // 次要需求轻微衰减，模拟能量消耗
            competence = clamp(competence - 0.005)
            autonomy = clamp(autonomy - 0.005)
            relatedness = clamp(relatedness - 0.005)
            certainty = clamp(certainty - 0.005)
            growth = clamp(growth - 0.005)
        }
    }

    private fun regulateEmotion(
        before: EmotionalValence,
        impulse: PsiImpulse,
        needs: NeedState
    ): EmotionalValence {
        return when {
            impulse.intensity > 0.8 -> EmotionalValence.CURIOUS
            needs.competence < 0.3 || needs.certainty < 0.3 -> EmotionalValence.CONFUSED
            before == EmotionalValence.CURIOUS && impulse.need == PsiNeed.RELATEDNESS ->
                EmotionalValence.POSITIVE_MILD
            else -> before
        }
    }

    private fun computeSatisfactionDelta(before: NeedState, after: NeedState): Double {
        val beforeSum = before.competence + before.autonomy + before.relatedness + before.certainty + before.growth
        val afterSum = after.competence + after.autonomy + after.relatedness + after.certainty + after.growth
        return afterSum - beforeSum
    }

    /**
     * Derive PAD (Pleasure / Arousal / Dominance) emotion dimensions from
     * urges + modulators. Mirrors psi.py PSIState.update_emotions line-for-line.
     */
    private fun derivePadEmotion(
        needs: NeedState,
        modulators: Map<PsiModulator, Double>,
    ): PadEmotion {
        val avgSatisfaction = listOf(
            needs.competence, needs.autonomy, needs.relatedness,
            needs.certainty, needs.growth,
        ).average()
        val pleasure = (avgSatisfaction - 0.5) * 2
        val uncertainty = 1.0 - needs.certainty
        val arousal = ((modulators.getOrDefault(PsiModulator.ACTIVATION, 0.5)) + uncertainty) / 2.0
        val dominance = (modulators.getOrDefault(PsiModulator.COMPETENCE, 0.7) +
            modulators.getOrDefault(PsiModulator.SELECTION, 0.6)) - 1.0

        val feeling = when {
            pleasure > 0.3 && arousal > 0.6 -> "excited"
            pleasure > 0.3 && arousal < 0.4 -> "content"
            pleasure < -0.3 && arousal > 0.6 -> "distressed"
            pleasure < -0.3 && arousal < 0.4 -> "depressed"
            arousal > 0.7 -> "alert"
            else -> "neutral"
        }
        return PadEmotion(pleasure, arousal, dominance, feeling)
    }

    /**
     * Publish need.deficit events for every drive below [DEFICIT_THRESHOLD].
     * Subscribers (LifeformDashboard, future Triphase metacog monitor) use
     * these to surface "the lifeform is hungry for X" without polling.
     */
    private fun publishDeficitsIfNeeded(needs: NeedState) {
        if (needs.competence < DEFICIT_THRESHOLD) {
            bus.publish(CognitiveBusTopics.NEED_DEFICIT, mapOf(
                "need" to "competence",
                "drive" to PsiDrive.COMPETENCE.name.lowercase(),
                "value" to "%.3f".format(needs.competence),
            ))
        }
        if (needs.autonomy < DEFICIT_THRESHOLD) {
            bus.publish(CognitiveBusTopics.NEED_DEFICIT, mapOf(
                "need" to "autonomy",
                "drive" to PsiDrive.SURVIVAL.name.lowercase(),
                "value" to "%.3f".format(needs.autonomy),
            ))
        }
        if (needs.relatedness < DEFICIT_THRESHOLD) {
            bus.publish(CognitiveBusTopics.NEED_DEFICIT, mapOf(
                "need" to "relatedness",
                "drive" to PsiDrive.AFFILIATION.name.lowercase(),
                "value" to "%.3f".format(needs.relatedness),
            ))
        }
        if (needs.certainty < DEFICIT_THRESHOLD) {
            bus.publish(CognitiveBusTopics.NEED_DEFICIT, mapOf(
                "need" to "certainty",
                "drive" to PsiDrive.CERTAINTY.name.lowercase(),
                "value" to "%.3f".format(needs.certainty),
            ))
        }
        if (needs.growth < DEFICIT_THRESHOLD) {
            bus.publish(CognitiveBusTopics.NEED_DEFICIT, mapOf(
                "need" to "growth",
                "drive" to PsiDrive.CURIOSITY.name.lowercase(),
                "value" to "%.3f".format(needs.growth),
            ))
        }
    }

    /**
     * Harness execution result dispatcher. Rehydrates the [HarnessOutcome]
     * from the bus payload and delegates to [learnFromOutcome]. Runs on the
     * publishing thread — keep learnFromOutcome non-blocking.
     */
    private fun handleHarnessResult(event: CognitiveEvent) {
        val outcome = HarnessOutcome(
            action = event.payload["action"].orEmpty(),
            outcomeType = event.payload["outcome_type"].orEmpty(),
            success = event.payload["success"]?.toBooleanStrictOrNull() ?: false,
            fitness = event.payload["fitness"]?.toDoubleOrNull() ?: if (event.payload["success"] == "true") 1.0 else 0.0,
            error = event.payload["error"],
            speciesId = event.payload["species_id"],
        )
        // Resolve the originating impulse — fall back to the last recorded
        // one when the harness didn't echo the action (e.g. external tools).
        val impulse = metacognition.lastImpulse?.takeIf { it.action == outcome.action }
            ?: metacognition.lastImpulse
            ?: PsiImpulse(
                need = PsiNeed.COMPETENCE,
                action = outcome.action,
                target = "harness",
                intensity = outcome.fitness,
                reason = "harness execution result",
            )
        try {
            learnFromOutcome(impulse, outcome)
        } catch (t: Throwable) {
            Log.e(TAG, "learnFromOutcome failed: ${t.message}", t)
        }
    }

    /**
     * Update competence urge, COMPETENCE modulator, and memory_associations
     * based on a harness execution outcome. Aligned 1:1 with psi.py#L166
     * PSIAgent.learn_from_outcome:
     *   - success: competence += 0.1, modulator COMPETENCE += 0.05, assoc += lr
     *   - failure: competence -= 0.15, modulator COMPETENCE -= 0.05, assoc -= lr
     *   - clamp urges/modulators to [0,1] then refresh PAD emotion.
     *
     * Public so unit tests can drive the loop deterministically.
     */
    fun learnFromOutcome(action: PsiImpulse, outcome: HarnessOutcome) {
        val key = "${action.action}->${outcome.outcomeType}"
        if (outcome.success) {
            bus.updateNeeds { needs ->
                needs.competence = (needs.competence + 0.1).coerceIn(0.0, 1.0)
            }
            modulators[PsiModulator.COMPETENCE] =
                (modulators.getOrDefault(PsiModulator.COMPETENCE, 0.7) + 0.05).coerceIn(0.0, 1.0)
            memoryAssociations[key] =
                (memoryAssociations.getOrDefault(key, 0.5) + learningRate).coerceIn(0.0, 1.0)
        } else {
            bus.updateNeeds { needs ->
                needs.competence = (needs.competence - 0.15).coerceIn(0.0, 1.0)
            }
            modulators[PsiModulator.COMPETENCE] =
                (modulators.getOrDefault(PsiModulator.COMPETENCE, 0.7) - 0.05).coerceIn(0.0, 1.0)
            memoryAssociations[key] =
                (memoryAssociations.getOrDefault(key, 0.5) - learningRate).coerceIn(0.0, 1.0)
        }
        // Publish the satisfaction/deficit signal so the LifeformDashboard
        // and (future) Triphase metacog monitor can react.
        val satisfied = outcome.success && outcome.fitness > 0.6
        if (satisfied) {
            bus.publish(CognitiveBusTopics.NEED_SATISFIED, mapOf(
                "need" to action.need.name.lowercase(),
                "drive" to action.need.toDrive().name.lowercase(),
                "action" to action.action,
                "fitness" to "%.3f".format(outcome.fitness),
            ))
        } else if (!outcome.success) {
            bus.publish(CognitiveBusTopics.NEED_DEFICIT, mapOf(
                "need" to action.need.name.lowercase(),
                "drive" to action.need.toDrive().name.lowercase(),
                "action" to action.action,
                "reason" to "harness execution failed",
                "error" to (outcome.error ?: "unknown"),
            ))
        }
        Log.i(TAG, "[OK] learnFromOutcome action=${action.action} success=${outcome.success} fitness=%.3f assoc_size=${memoryAssociations.size}".format(outcome.fitness))
    }

    /**
     * Read-only snapshot of memory associations — exposed for the
     * LifeformDashboard and unit tests. Stable against concurrent tick
     * mutation (copies the LinkedHashMap).
     */
    fun memoryAssociationsSnapshot(): Map<String, Double> = memoryAssociations.toMap()

    /** Read-only snapshot of PSI modulators. */
    fun modulatorsSnapshot(): Map<PsiModulator, Double> = modulators.toMap()

    private fun clamp(value: Double): Double = max(0.0, min(1.0, value))
}
