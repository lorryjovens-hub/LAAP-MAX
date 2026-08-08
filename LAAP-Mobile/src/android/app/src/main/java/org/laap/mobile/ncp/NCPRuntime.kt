/*
 * NCPRuntime.kt
 *
 * LAAP Liquid NCP 移动端运行时（Android / Kotlin）
 * 对应 LAAP 桌面端: laap/liquid/neurons.py 中的 NCPCircuit
 *
 * 本文件实现：
 *   1. NCPModel  —— 从 assets 中加载 ncp_model.json 权重
 *   2. NCPRuntime —— 提供 forward(h, x, dt) -> new_h 推理接口
 *                —— 提供 getCommandActivations() -> DoubleArray
 *   3. 深度推理唤醒桌面逻辑：当 NCP 命令神经元置信度 < 0.4 时，
 *      调用 ArisEngineClient.cycle() 向桌面主节点请求深度推理
 *
 * NCP 拓扑（C. elegans 19 神经元布线）：
 *   sensory(4) → inter(6) → command(4, 含循环) → motor(5)
 * 每个神经元是一个 1 维 CfCCell：
 *   r = σ(-W_τ · dt)
 *   h̃ = tanh(W_h · x + W_hh · h + b_h)
 *   h_new = r · h + (1 - r) · h̃
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.ncp

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import org.laap.mobile.laap.ArisEngineClient
import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min
import kotlin.math.tanh

/**
 * 单个 CfCCell 的权重（input_dim=1, hidden_dim=1）。
 */
data class CfCCellWeights(
    val wTau: DoubleArray,   // (1,)
    val wH: Array<DoubleArray>,   // (1, 1)
    val wHh: Array<DoubleArray>,  // (1, 1)
    val bH: DoubleArray      // (1,)
)

/**
 * NCP 模型权重容器，从 assets/ncp_model.json 加载。
 * 与 laap/liquid/export_ncp_model.py 导出的 JSON 结构一一对应。
 */
class NCPModel(
    val inputDim: Int,
    val nTotal: Int,
    val nSensory: Int,
    val nInter: Int,
    val nCommand: Int,
    val nMotor: Int,
    val wInputSensory: Array<DoubleArray>,    // (nSensory, inputDim)
    val wSensoryInter: Array<DoubleArray>,    // (nInter, nSensory)
    val wInterCommand: Array<DoubleArray>,    // (nCommand, nInter)
    val wCommandCommand: Array<DoubleArray>,  // (nCommand, nCommand)
    val wCommandMotor: Array<DoubleArray>,    // (nMotor, nCommand)
    val bNeurons: DoubleArray,                // (nTotal,)
    val cells: List<CfCCellWeights>           // 长度 = nTotal
) {
    companion object {
        private const val TAG = "NCPModel"

        /**
         * 从 assets 加载 ncp_model.json。
         * 调用方需将 ncp_model.json 放置在 src/main/assets/ 目录下。
         */
        fun loadFromAssets(context: Context, name: String = "ncp_model.json"): NCPModel? {
            return try {
                val jsonStr = context.assets.open(name).bufferedReader().use { it.readText() }
                val obj = JSONObject(jsonStr)
                fromJson(obj)
            } catch (e: Exception) {
                Log.w(TAG, "[WARN] 加载 $name 失败: ${e.message}")
                null
            }
        }

        /**
         * 从 JSONObject 构造 NCPModel。
         */
        fun fromJson(obj: JSONObject): NCPModel? {
            return try {
                val inputDim = obj.getInt("input_dim")
                val nTotal = obj.getInt("n_total")
                val nSensory = obj.getInt("n_sensory")
                val nInter = obj.getInt("n_inter")
                val nCommand = obj.getInt("n_command")
                val nMotor = obj.getInt("n_motor")

                val wInputSensory = obj.getJSONArray("w_input_sensory").toMatrix()
                val wSensoryInter = obj.getJSONArray("w_sensory_inter").toMatrix()
                val wInterCommand = obj.getJSONArray("w_inter_command").toMatrix()
                val wCommandCommand = obj.getJSONArray("w_command_command").toMatrix()
                val wCommandMotor = obj.getJSONArray("w_command_motor").toMatrix()
                val bNeurons = obj.getJSONArray("b_neurons").toDoubleArray()

                val cellsArr = obj.getJSONArray("cells")
                val cells = ArrayList<CfCCellWeights>(cellsArr.length())
                for (i in 0 until cellsArr.length()) {
                    val c = cellsArr.getJSONObject(i)
                    cells.add(
                        CfCCellWeights(
                            wTau = c.getJSONArray("w_tau").toDoubleArray(),
                            wH = c.getJSONArray("w_h").toMatrix(),
                            wHh = c.getJSONArray("w_hh").toMatrix(),
                            bH = c.getJSONArray("b_h").toDoubleArray()
                        )
                    )
                }

                // 基本校验
                require(cells.size == nTotal) { "cells 数量 ${cells.size} != n_total $nTotal" }
                require(bNeurons.size == nTotal) { "bNeurons 长度 ${bNeurons.size} != n_total $nTotal" }
                require(wInputSensory.size == nSensory) { "wInputSensory 行数错误" }

                Log.i(TAG, "[OK] NCPModel 已加载（19 神经元，input_dim=$inputDim）")
                NCPModel(
                    inputDim, nTotal, nSensory, nInter, nCommand, nMotor,
                    wInputSensory, wSensoryInter, wInterCommand,
                    wCommandCommand, wCommandMotor, bNeurons, cells
                )
            } catch (e: Exception) {
                Log.w(TAG, "[WARN] JSON 解析失败: ${e.message}")
                null
            }
        }

        private fun JSONArray.toMatrix(): Array<DoubleArray> {
            val rows = this.length()
            val out = Array(rows) { DoubleArray(0) }
            for (i in 0 until rows) {
                val row = this.getJSONArray(i)
                out[i] = DoubleArray(row.length()) { j -> row.getDouble(j) }
            }
            return out
        }

        private fun JSONArray.toDoubleArray(): DoubleArray {
            return DoubleArray(this.length()) { i -> this.getDouble(i) }
        }
    }
}

/**
 * NCP 推理运行时。算法等价于 laap/liquid/neurons.py 的 NCPCircuit.forward。
 *
 * 使用 Kotlin 数组操作做矩阵运算（19 神经元规模较小，无需 BLAS）。
 * 在 Pixel 设备上单次前向 < 0.1ms。
 */
class NCPRuntime(private val model: NCPModel) {

    // 暴露给外部的拓扑常量（只读）
    val nMotor: Int get() = model.nMotor
    val nTotal: Int get() = model.nTotal
    val nCommand: Int get() = model.nCommand
    val inputDim: Int get() = model.inputDim

    // 神经元索引区间
    private val sensoryRange: IntRange = 0 until model.nSensory
    private val interRange: IntRange = model.nSensory until (model.nSensory + model.nInter)
    private val commandRange: IntRange =
        (model.nSensory + model.nInter) until (model.nSensory + model.nInter + model.nCommand)
    private val motorRange: IntRange =
        (model.nSensory + model.nInter + model.nCommand) until model.nTotal

    // 最近一次 forward 的命令神经元激活值（tanh 压缩后，4 维）
    private var commandActivations: DoubleArray = DoubleArray(model.nCommand)

    /** 默认全零隐状态（19 维）。 */
    fun defaultState(): DoubleArray = DoubleArray(model.nTotal)

    /**
     * 单步前向推理，返回新的 19 维隐状态。
     *
     * @param h  19 维隐状态
     * @param x  inputDim 维外部输入
     * @param dt 任意正实数步长
     * @return 新的 19 维隐状态
     */
    fun forward(h: DoubleArray, x: DoubleArray, dt: Double): DoubleArray {
        require(h.size == model.nTotal) { "h 维度应为 ${model.nTotal}" }
        require(x.size == model.inputDim) { "x 维度应为 ${model.inputDim}" }
        require(dt >= 0) { "dt 必须非负" }

        if (dt == 0.0) return h.copyOf()

        val newH = h.copyOf()

        // ── 1. 感觉神经元：sensory_in = W_input_sensory @ x ──
        val sensoryIn = matVec(model.wInputSensory, x)  // (4,)
        for (i in 0 until model.nSensory) {
            val idx = sensoryRange.first + i
            val xi = doubleArrayOf(sensoryIn[i] + model.bNeurons[idx])
            val hi = doubleArrayOf(h[idx])
            newH[idx] = cfcForward(cellIdx = idx, h = hi, x = xi, dt = dt)[0]
        }

        // ── 2. 中间神经元：inter_in = W_sensory_inter @ sensory_out ──
        val sensoryOut = newH.sliceArray(sensoryRange)
        val interIn = matVec(model.wSensoryInter, sensoryOut)  // (6,)
        for (i in 0 until model.nInter) {
            val idx = interRange.first + i
            val xi = doubleArrayOf(interIn[i] + model.bNeurons[idx])
            val hi = doubleArrayOf(h[idx])
            newH[idx] = cfcForward(cellIdx = idx, h = hi, x = xi, dt = dt)[0]
        }

        // ── 3. 命令神经元：command_in = W_inter_command @ inter_out
        //                       + W_command_command @ h_command_old（用旧值避免循环依赖）──
        val interOut = newH.sliceArray(interRange)
        val commandFeedback = matVec(model.wCommandCommand, h.sliceArray(commandRange))
        val commandIn = matVec(model.wInterCommand, interOut)  // (4,)
        for (i in 0 until model.nCommand) {
            val idx = commandRange.first + i
            val xi = doubleArrayOf(commandIn[i] + commandFeedback[i] + model.bNeurons[idx])
            val hi = doubleArrayOf(h[idx])
            newH[idx] = cfcForward(cellIdx = idx, h = hi, x = xi, dt = dt)[0]
        }

        // 记录命令神经元激活值（tanh 压缩到 [-1, 1]）
        for (i in 0 until model.nCommand) {
            commandActivations[i] = tanhClip(newH[commandRange.first + i])
        }

        // ── 4. 运动神经元：motor_in = W_command_motor @ command_out ──
        val commandOut = newH.sliceArray(commandRange)
        val motorIn = matVec(model.wCommandMotor, commandOut)  // (5,)
        for (i in 0 until model.nMotor) {
            val idx = motorRange.first + i
            val xi = doubleArrayOf(motorIn[i] + model.bNeurons[idx])
            val hi = doubleArrayOf(h[idx])
            newH[idx] = cfcForward(cellIdx = idx, h = hi, x = xi, dt = dt)[0]
        }

        // 隐状态裁剪到 [-1e3, 1e3]（与桌面端 _clip_h 一致）
        for (i in newH.indices) {
            if (newH[i] > 1e3) newH[i] = 1e3
            else if (newH[i] < -1e3) newH[i] = -1e3
        }
        return newH
    }

    /** 返回最近一次 forward 后命令神经元的激活值（tanh 压缩后，4 维）。 */
    fun getCommandActivations(): DoubleArray = commandActivations.copyOf()

    /**
     * 计算命令神经元的置信度：激活向量的 L2 范数 / nCommand。
     * 用于判断移动端是否需要唤醒桌面主节点做深度推理。
     */
    fun computeConfidence(): Double {
        var sum = 0.0
        for (v in commandActivations) sum += v * v
        return kotlin.math.sqrt(sum) / model.nCommand
    }

    // MARK: - 内部：CfCCell 前向

    /** 单个 CfCCell 前向（input_dim=1, hidden_dim=1）。 */
    private fun cfcForward(cellIdx: Int, h: DoubleArray, x: DoubleArray, dt: Double): DoubleArray {
        val cell = model.cells[cellIdx]
        val wTau = cell.wTau[0]
        // r = σ(-W_τ · dt)
        val r = sigmoidScalar(-wTau * dt)
        // h̃ = tanh(W_h[0][0] · x[0] + W_hh[0][0] · h[0] + b_h[0])
        val wH = cell.wH[0][0]
        val wHh = cell.wHh[0][0]
        val bH = cell.bH[0]
        val hTilde = tanhClip(wH * x[0] + wHh * h[0] + bH)
        val newH = r * h[0] + (1.0 - r) * hTilde
        return doubleArrayOf(newH)
    }

    // MARK: - 内部：数学工具

    /** 矩阵 × 向量：m (rows×cols) × v (cols) → out (rows) */
    private fun matVec(m: Array<DoubleArray>, v: DoubleArray): DoubleArray {
        val rows = m.size
        val out = DoubleArray(rows)
        for (i in 0 until rows) {
            val row = m[i]
            var s = 0.0
            for (j in row.indices) {
                s += row[j] * v[j]
            }
            out[i] = s
        }
        return out
    }

    /** 数值稳定的标量 sigmoid，输出裁剪到 [1e-6, 1-1e-6]。 */
    private fun sigmoidScalar(x: Double): Double {
        val clamped = max(-50.0, min(50.0, x))
        val s = if (clamped >= 0) {
            1.0 / (1.0 + exp(-clamped))
        } else {
            val e = exp(clamped)
            e / (1.0 + e)
        }
        return max(1e-6, min(1.0 - 1e-6, s))
    }

    /** 标量 tanh（裁剪到 [-50, 50] 防溢出）。 */
    private fun tanhClip(x: Double): Double {
        val clamped = max(-50.0, min(50.0, x))
        return tanh(clamped)
    }
}

/**
 * 深度推理唤醒器：当移动端 NCP 推理置信度低于阈值时，
 * 调用桌面端 ArisEngine 做深度推理。
 *
 * 设计意图：
 *   - 移动端 NCP 是轻量推理（19 神经元，< 0.1ms）
 *   - 当感知信号复杂度高（命令神经元激活弱，置信度 < 0.4）时，
 *     移动端能力不足，唤醒桌面主节点做完整 PSI + AGI 推理
 *   - 桌面不可达时降级返回移动端自身的浅推理结果
 */
class NCPDeepInferenceWakeup(
    private val runtime: NCPRuntime,
    private val arisClient: ArisEngineClient = ArisEngineClient.getInstance(),
    private val confidenceThreshold: Double = 0.4
) {
    companion object {
        private const val TAG = "NCPDeepInference"
    }

    /**
     * 执行一轮推理，必要时唤醒桌面。
     *
     * @param h 当前 NCP 隐状态（19 维，会被原地更新）
     * @param x 感知输入（inputDim 维）
     * @param dt 时间步长
     * @return 推理结果（motor 响应 + 是否唤醒桌面 + 桌面返回的深度结果）
     */
    suspend fun inferWithWakeup(
        h: DoubleArray,
        x: DoubleArray,
        dt: Double
    ): DeepInferenceResult = withContext(Dispatchers.Default) {
        // 1. 移动端本地 NCP 推理
        val newH = runtime.forward(h, x, dt)
        // 拷贝回 h（原地更新）
        for (i in h.indices) h[i] = newH[i]

        val motor = newH.copyOfRange(newH.size - runtime.nMotor, newH.size)
        val confidence = runtime.computeConfidence()

        // 2. 置信度低 → 唤醒桌面
        var desktopResult: JSONObject? = null
        var desktopWakeupTriggered = false
        var desktopError: String? = null

        if (confidence < confidenceThreshold) {
            desktopWakeupTriggered = true
            try {
                val inputText = buildString {
                    append("{\"motor\":[")
                    motor.forEachIndexed { i, v ->
                        append("%.4f".format(v))
                        if (i < motor.size - 1) append(",")
                    }
                    append("],\"confidence\":")
                    append("%.4f".format(confidence))
                    append(",\"cmd_act\":[")
                    val cmd = runtime.getCommandActivations()
                    cmd.forEachIndexed { i, v ->
                        append("%.4f".format(v))
                        if (i < cmd.size - 1) append(",")
                    }
                    append("]}")
                }
                desktopResult = arisClient.cycle(inputText, source = "mobile_ncp")
                Log.i(TAG, "[OK] 桌面深度推理已唤醒，置信度=${"%.4f".format(confidence)}")
            } catch (e: Exception) {
                desktopError = e.message ?: "unknown"
                Log.w(TAG, "[WARN] 桌面唤醒失败，降级使用移动端浅推理: ${e.message}")
            }
        } else {
            Log.d(TAG, "[INFO] 移动端置信度 $confidence ≥ $confidenceThreshold，无需唤醒桌面")
        }

        DeepInferenceResult(
            motorResponse = motor,
            confidence = confidence,
            desktopWakeupTriggered = desktopWakeupTriggered,
            desktopResult = desktopResult,
            desktopError = desktopError
        )
    }
}

/**
 * 深度推理结果。
 */
data class DeepInferenceResult(
    /** 移动端 NCP 运动神经元响应（5 维）。 */
    val motorResponse: DoubleArray,
    /** 命令神经元置信度 [0, 1]。 */
    val confidence: Double,
    /** 是否触发了桌面唤醒。 */
    val desktopWakeupTriggered: Boolean,
    /** 桌面返回的深度推理结果（唤醒成功时）。 */
    val desktopResult: JSONObject?,
    /** 桌面唤醒失败的错误信息（失败时）。 */
    val desktopError: String?
)
