//
//  NCPRuntime.swift
//  LAAP Mobile
//
//  LAAP Liquid NCP 移动端运行时（iOS / Swift）
//  对应 LAAP 桌面端: laap/liquid/neurons.py 中的 NCPCircuit
//
//  本文件实现：
//    1. NCPModel  —— 从 Bundle 中加载 ncp_model.json 权重
//    2. NCPRuntime —— 提供 forward(h, x, dt) -> new_h 推理接口
//                  —— 使用 Accelerate 框架（vDSP）做矩阵运算加速
//                  —— 提供 getCommandActivations() -> [Double]
//
//  NCP 拓扑（C. elegans 19 神经元布线）：
//    sensory(4) → inter(6) → command(4, 含循环) → motor(5)
//  每个神经元是一个 1 维 CfCCell：
//    r = σ(-W_τ · dt)
//    h̃ = tanh(W_h · x + W_hh · h + b_h)
//    h_new = r · h + (1 - r) · h̃
//
//  This file is part of LAAP Mobile, licensed under GPL v3.
//

import Foundation
import Accelerate

// MARK: - NCPModel

/// NCP 模型权重容器，从 JSON 加载。
/// 与 laap/liquid/export_ncp_model.py 导出的 JSON 结构一一对应。
public final class NCPModel {

    // 拓扑常量
    public let inputDim: Int
    public let nTotal: Int
    public let nSensory: Int
    public let nInter: Int
    public let nCommand: Int
    public let nMotor: Int

    // 突触权重矩阵（二维 Double 数组，行优先）
    public let wInputSensory:   [[Double]]   // (nSensory, inputDim) = (4, 8)
    public let wSensoryInter:   [[Double]]   // (nInter, nSensory)   = (6, 4)
    public let wInterCommand:   [[Double]]   // (nCommand, nInter)   = (4, 6)
    public let wCommandCommand: [[Double]]   // (nCommand, nCommand) = (4, 4)
    public let wCommandMotor:   [[Double]]   // (nMotor, nCommand)   = (5, 4)

    // 每个神经元的偏置（19 维）
    public let bNeurons: [Double]

    // 19 个 CfCCell 的内部权重
    public let cells: [CfCCellWeights]

    public struct CfCCellWeights {
        public let wTau: [Double]      // (1,)
        public let wH: [[Double]]      // (1, 1)
        public let wHh: [[Double]]     // (1, 1)
        public let bH: [Double]        // (1,)
    }

    /// 从 JSON 字典构造模型。
    public init?(dict: [String: Any]) {
        guard
            let inputDim = dict["input_dim"] as? Int,
            let nTotal = dict["n_total"] as? Int,
            let nSensory = dict["n_sensory"] as? Int,
            let nInter = dict["n_inter"] as? Int,
            let nCommand = dict["n_command"] as? Int,
            let nMotor = dict["n_motor"] as? Int,
            let wInputSensory = dict["w_input_sensory"] as? [[Double]],
            let wSensoryInter = dict["w_sensory_inter"] as? [[Double]],
            let wInterCommand = dict["w_inter_command"] as? [[Double]],
            let wCommandCommand = dict["w_command_command"] as? [[Double]],
            let wCommandMotor = dict["w_command_motor"] as? [[Double]],
            let bNeurons = dict["b_neurons"] as? [Double],
            let cellsRaw = dict["cells"] as? [[String: Any]]
        else {
            return nil
        }

        self.inputDim = inputDim
        self.nTotal = nTotal
        self.nSensory = nSensory
        self.nInter = nInter
        self.nCommand = nCommand
        self.nMotor = nMotor
        self.wInputSensory = wInputSensory
        self.wSensoryInter = wSensoryInter
        self.wInterCommand = wInterCommand
        self.wCommandCommand = wCommandCommand
        self.wCommandMotor = wCommandMotor
        self.bNeurons = bNeurons

        var cells: [CfCCellWeights] = []
        cells.reserveCapacity(cellsRaw.count)
        for c in cellsRaw {
            guard
                let wTau = c["w_tau"] as? [Double],
                let wH = c["w_h"] as? [[Double]],
                let wHh = c["w_hh"] as? [[Double]],
                let bH = c["b_h"] as? [Double]
            else {
                return nil
            }
            cells.append(CfCCellWeights(wTau: wTau, wH: wH, wHh: wHh, bH: bH))
        }
        self.cells = cells

        // 基本校验
        guard cells.count == nTotal,
              bNeurons.count == nTotal,
              wInputSensory.count == nSensory,
              wSensoryInter.count == nInter,
              wInterCommand.count == nCommand,
              wCommandCommand.count == nCommand,
              wCommandMotor.count == nMotor
        else {
            return nil
        }
    }

    /// 从 Bundle 加载 ncp_model.json。
    /// 调用方需将 ncp_model.json 添加到 Xcode 项目的 Bundle Resources。
    public static func loadFromBundle(name: String = "ncp_model") -> NCPModel? {
        guard let url = Bundle.main.url(forResource: name, withExtension: "json") else {
            NSLog("[WARN] NCPModel: Bundle 中未找到 \(name).json")
            return nil
        }
        do {
            let data = try Data(contentsOf: url)
            let obj = try JSONSerialization.jsonObject(with: data, options: [])
            guard let dict = obj as? [String: Any] else {
                NSLog("[WARN] NCPModel: JSON 顶层结构非 dict")
                return nil
            }
            guard let model = NCPModel(dict: dict) else {
                NSLog("[WARN] NCPModel: JSON 字段缺失或类型不符")
                return nil
            }
            NSLog("[OK] NCPModel: 已加载 \(name).json（19 神经元，input_dim=\(model.inputDim)）")
            return model
        } catch {
            NSLog("[WARN] NCPModel: 加载失败: \(error)")
            return nil
        }
    }
}

// MARK: - NCPRuntime

/// NCP 推理运行时。基于 Accelerate（vDSP）加速矩阵运算。
/// 算法等价于 laap/liquid/neurons.py 的 NCPCircuit.forward。
public final class NCPRuntime {

    private let model: NCPModel

    // 神经元索引区间（与桌面端 NCPCircuit.SENSORY_IDX 等一致）
    private let sensoryRange: Range<Int>
    private let interRange: Range<Int>
    private let commandRange: Range<Int>
    private let motorRange: Range<Int>

    // 最近一次 forward 的命令神经元激活值（tanh 压缩后，4 维）
    private var commandActivations: [Double]

    /// 暴露给外部的拓扑常量（只读）。
    public var nMotor: Int { model.nMotor }
    public var nTotal: Int { model.nTotal }
    public var nCommand: Int { model.nCommand }

    public init(model: NCPModel) {
        self.model = model
        let nS = model.nSensory
        let nI = model.nInter
        let nC = model.nCommand
        let nM = model.nMotor
        self.sensoryRange = 0..<(nS)
        self.interRange = nS..<(nS + nI)
        self.commandRange = (nS + nI)..<(nS + nI + nC)
        self.motorRange = (nS + nI + nC)..<(nS + nI + nC + nM)
        self.commandActivations = [Double](repeating: 0.0, count: nC)
    }

    /// 默认全零隐状态（19 维）。
    public func defaultState() -> [Double] {
        return [Double](repeating: 0.0, count: model.nTotal)
    }

    /// 单步前向推理，返回新的 19 维隐状态。
    ///
    /// - Parameters:
    ///   - h: 19 维隐状态
    ///   - x: inputDim 维外部输入
    ///   - dt: 任意正实数步长
    /// - Returns: 新的 19 维隐状态
    public func forward(h: [Double], x: [Double], dt: Double) -> [Double] {
        precondition(h.count == model.nTotal, "h 维度应为 \(model.nTotal)")
        precondition(x.count == model.inputDim, "x 维度应为 \(model.inputDim)")
        precondition(dt >= 0, "dt 必须非负")

        if dt == 0 {
            return h
        }

        var newH = h

        // ── 1. 感觉神经元：sensory_in = W_input_sensory @ x ──
        let sensoryIn = matVec(self.model.wInputSensory, x)  // (4,)
        for i in 0..<model.nSensory {
            let idx = sensoryRange.lowerBound + i
            let xi = [sensoryIn[i] + model.bNeurons[idx]]
            let hi = [h[idx]]
            newH[idx] = cfcForward(cellIdx: idx, h: hi, x: xi, dt: dt)[0]
        }

        // ── 2. 中间神经元：inter_in = W_sensory_inter @ sensory_out ──
        let sensoryOut = Array(newH[sensoryRange])
        let interIn = matVec(self.model.wSensoryInter, sensoryOut)  // (6,)
        for i in 0..<model.nInter {
            let idx = interRange.lowerBound + i
            let xi = [interIn[i] + model.bNeurons[idx]]
            let hi = [h[idx]]
            newH[idx] = cfcForward(cellIdx: idx, h: hi, x: xi, dt: dt)[0]
        }

        // ── 3. 命令神经元：command_in = W_inter_command @ inter_out
        //                       + W_command_command @ h_command_old（用旧值避免循环依赖）──
        let interOut = Array(newH[interRange])
        let commandFeedback = matVec(self.model.wCommandCommand, Array(h[commandRange]))
        let commandIn = matVec(self.model.wInterCommand, interOut)  // (4,)
        for i in 0..<model.nCommand {
            let idx = commandRange.lowerBound + i
            let xi = [commandIn[i] + commandFeedback[i] + model.bNeurons[idx]]
            let hi = [h[idx]]
            newH[idx] = cfcForward(cellIdx: idx, h: hi, x: xi, dt: dt)[0]
        }

        // 记录命令神经元激活值（tanh 压缩）
        var cmdAct = [Double](repeating: 0.0, count: model.nCommand)
        vvtanh(&cmdAct, Array(newH[commandRange]), [Int32(model.nCommand)])
        self.commandActivations = cmdAct

        // ── 4. 运动神经元：motor_in = W_command_motor @ command_out ──
        let commandOut = Array(newH[commandRange])
        let motorIn = matVec(self.model.wCommandMotor, commandOut)  // (5,)
        for i in 0..<model.nMotor {
            let idx = motorRange.lowerBound + i
            let xi = [motorIn[i] + model.bNeurons[idx]]
            let hi = [h[idx]]
            newH[idx] = cfcForward(cellIdx: idx, h: hi, x: xi, dt: dt)[0]
        }

        // 隐状态裁剪到 [-1e3, 1e3]（与桌面端 _clip_h 一致）
        for i in 0..<newH.count {
            if newH[i] > 1e3 { newH[i] = 1e3 }
            else if newH[i] < -1e3 { newH[i] = -1e3 }
        }
        return newH
    }

    /// 返回最近一次 forward 后命令神经元的激活值（tanh 压缩后，4 维）。
    public func getCommandActivations() -> [Double] {
        return commandActivations
    }

    /// 计算命令神经元的置信度：激活值 L2 范数 / nCommand。
    ///
    /// 用于判断移动端是否需要唤醒桌面主节点做深度推理。
    /// 与 Android NCPRuntime.computeConfidence() 实现一致。
    public func computeConfidence() -> Double {
        var sum = 0.0
        for v in commandActivations {
            sum += v * v
        }
        return sqrt(sum) / Double(model.nCommand)
    }

    // MARK: - 内部：CfCCell 前向

    /// 单个 CfCCell 前向（input_dim=1, hidden_dim=1）。
    ///   r = σ(-W_τ · dt)
    ///   h̃ = tanh(W_h · x + W_hh · h + b_h)
    ///   h_new = r · h + (1 - r) · h̃
    private func cfcForward(cellIdx: Int, h: [Double], x: [Double], dt: Double) -> [Double] {
        let cell = model.cells[cellIdx]
        // W_τ 是 [Double]（长度 1）
        let wTau = cell.wTau[0]
        // σ(-W_τ · dt) —— 数值稳定的 sigmoid
        let arg = -wTau * dt
        let r = sigmoidScalar(arg)

        // h̃ = tanh(W_h[0][0] · x[0] + W_hh[0][0] · h[0] + b_h[0])
        let wH = cell.wH[0][0]
        let wHh = cell.wHh[0][0]
        let bH = cell.bH[0]
        let hTilde = tanhScalar(wH * x[0] + wHh * h[0] + bH)

        let newH = r * h[0] + (1.0 - r) * hTilde
        return [newH]
    }

    // MARK: - 内部：数学工具

    /// 矩阵 × 向量：用 Accelerate vDSP 加速。
    /// m 是行优先二维数组（rows × cols），v 长度为 cols，返回长度 rows。
    private func matVec(_ m: [[Double]], _ v: [Double]) -> [Double] {
        let rows = m.count
        guard rows > 0 else { return [] }
        let cols = m[0].count
        var out = [Double](repeating: 0.0, count: rows)

        // 展平矩阵为行优先一维数组
        var flat = [Double](repeating: 0.0, count: rows * cols)
        for i in 0..<rows {
            for j in 0..<cols {
                flat[i * cols + j] = m[i][j]
            }
        }
        // vDSP_mmulD: out = flat (rows×cols) × v (cols×1)
        var vCopy = v
        flat.withUnsafeMutableBufferPointer { flatPtr in
            vCopy.withUnsafeMutableBufferPointer { vPtr in
                out.withUnsafeMutableBufferPointer { outPtr in
                    vDSP_mmulD(
                        flatPtr.baseAddress, 1,
                        vPtr.baseAddress, 1,
                        outPtr.baseAddress, 1,
                        vDSP_Length(rows), 1, vDSP_Length(cols)
                    )
                }
            }
        }
        return out
    }

    /// 数值稳定的标量 sigmoid，输出裁剪到 [1e-6, 1-1e-6]（与桌面端一致）。
    private func sigmoidScalar(_ x: Double) -> Double {
        let clamped = max(-50.0, min(50.0, x))
        let s: Double
        if clamped >= 0 {
            s = 1.0 / (1.0 + exp(-clamped))
        } else {
            let e = exp(clamped)
            s = e / (1.0 + e)
        }
        return max(1e-6, min(1.0 - 1e-6, s))
    }

    /// 标量 tanh（裁剪到 [-50, 50] 防溢出）。
    private func tanhScalar(_ x: Double) -> Double {
        let clamped = max(-50.0, min(50.0, x))
        return tanh(clamped)
    }
}
