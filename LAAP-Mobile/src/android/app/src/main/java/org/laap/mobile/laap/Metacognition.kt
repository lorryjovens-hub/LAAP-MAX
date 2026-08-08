/*
 * Metacognition.kt
 *
 * LAAP 元认知监控原生实现（Android）
 * 对应 LAAP 桌面端: laap/agi/metacognition.py
 *
 * 职责：
 *   1. 监控 PSI 循环的性能与需求满足率
 *   2. 记录行为冲动与学习快照
 *   3. 根据满意度动态调整循环频率与驱动权重
 *   4. 检测长期未满足的需求并触发情绪调节事件
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.laap

import android.util.Log
import java.util.Date
import kotlin.math.max
import kotlin.math.min

/**
 * 元认知配置。可通过 UI 或远程配置动态调整。
 */
data class MetacognitionConfig(
    val minTickIntervalMs: Long = 500L,
    val maxTickIntervalMs: Long = 5000L,
    val satisfactionWindowSize: Int = 10,
    val lowSatisfactionThreshold: Double = -0.05,
    val highSatisfactionThreshold: Double = 0.05,
    val emotionRegulationThreshold: Double = 0.2
)

class Metacognition private constructor() {

    companion object {
        private const val TAG = "Metacognition"

        @Volatile
        private var instance: Metacognition? = null

        fun getInstance(): Metacognition {
            return instance ?: synchronized(this) {
                instance ?: Metacognition().also { instance = it }
            }
        }
    }

    private val bus = CognitiveBus.getInstance()

    var config: MetacognitionConfig = MetacognitionConfig()

    private val satisfactionHistory = ArrayDeque<Double>()
    private val impulseHistory = ArrayDeque<PsiImpulse>()

    @Volatile
    var lastImpulse: PsiImpulse? = null
        private set

    private var regulationCount: Long = 0

    /**
     * 记录一轮循环生成的冲动。
     */
    fun recordImpulse(impulse: PsiImpulse) {
        lastImpulse = impulse
        impulseHistory.addLast(impulse)
        if (impulseHistory.size > config.satisfactionWindowSize) {
            impulseHistory.removeFirst()
        }
    }

    /**
     * 学习：记录快照、更新满意度历史、触发情绪调节。
     */
    fun learn(snapshot: PsiLearningSnapshot) {
        satisfactionHistory.addLast(snapshot.satisfactionDelta)
        if (satisfactionHistory.size > config.satisfactionWindowSize) {
            satisfactionHistory.removeFirst()
        }

        val avgSatisfaction = satisfactionHistory.average()

        // 长期满意度低 → 发布情绪调节事件
        if (avgSatisfaction < config.emotionRegulationThreshold) {
            regulateEmotion(snapshot)
        }

        // 情绪显著正向 → 发布积极情绪事件
        if (snapshot.satisfactionDelta > config.highSatisfactionThreshold) {
            bus.publish("emotion.positive_mild", mapOf(
                "cycle_id" to snapshot.cycleId.toString(),
                "delta" to "%.3f".format(snapshot.satisfactionDelta)
            ))
        }

        Log.v(TAG, "learn cycle=${snapshot.cycleId} delta=${snapshot.satisfactionDelta} avg=${avgSatisfaction}")
    }

    /**
     * 自我调节：根据学习历史调整 PSI 循环频率与驱动权重。
     */
    fun adaptLoop(psiLoop: PSILoop, snapshot: PsiLearningSnapshot) {
        val avgSatisfaction = satisfactionHistory.average()

        // 调整循环频率：满意度低时加速探索，满意度高时减慢节能
        val newInterval = when {
            avgSatisfaction < config.lowSatisfactionThreshold ->
                max(config.minTickIntervalMs, psiLoop.tickIntervalMs - 200L)
            avgSatisfaction > config.highSatisfactionThreshold ->
                min(config.maxTickIntervalMs, psiLoop.tickIntervalMs + 200L)
            else -> psiLoop.tickIntervalMs
        }
        if (newInterval != psiLoop.tickIntervalMs) {
            psiLoop.tickIntervalMs = newInterval
            bus.publish("psi.metacognition.interval", mapOf(
                "interval_ms" to newInterval.toString()
            ))
        }

        // 调整驱动权重：持续低满足的需求获得权重加成
        val weights = psiLoop.driveWeights.toMutableMap()
        val need = snapshot.impulse.need
        if (snapshot.satisfactionDelta < config.lowSatisfactionThreshold) {
            weights[need] = min(2.0, weights.getOrDefault(need, 1.0) * 1.1)
            regulationCount++
            bus.publish("psi.metacognition.weight", mapOf(
                "need" to need.name.lowercase(),
                "weight" to "%.3f".format(weights[need])
            ))
        }
        psiLoop.driveWeights = weights
    }

    /**
     * 情绪调节：当某需求长期未满足时，提升其权重并发布调节事件。
     */
    private fun regulateEmotion(snapshot: PsiLearningSnapshot) {
        regulationCount++
        val need = snapshot.impulse.need
        bus.publish("emotion.negative_mild", mapOf(
            "cycle_id" to snapshot.cycleId.toString(),
            "need" to need.name.lowercase(),
            "reason" to "long-term low satisfaction triggers regulation"
        ))
        Log.w(TAG, "regulateEmotion cycle=${snapshot.cycleId} need=$need")
    }

    /**
     * 获取元认知摘要，供 UI 展示。
     */
    fun summary(): Map<String, String> {
        val avg = if (satisfactionHistory.isEmpty()) 0.0 else satisfactionHistory.average()
        return mapOf(
            "avg_satisfaction" to "%.3f".format(avg),
            "regulation_count" to regulationCount.toString(),
            "impulse_history_size" to impulseHistory.size.toString(),
            "last_impulse" to (lastImpulse?.action ?: "none"),
            "last_impulse_reason" to (lastImpulse?.reason ?: "")
        )
    }
}
