//
//  PSILoop.swift
//  LAAP Mobile
//
//  LAAP PSI 认知循环原生实现
//  对应 LAAP 桌面端: laap/agi/psi_loop.py
//
//  PSI 四阶段：感知(Perceive) → 选择(Select) → 行动(Act) → 学习(Learn)
//
//  This file is part of LAAP Mobile, licensed under GPL v3.
//

import Foundation
import Combine

public enum PsiNeed: String, Codable, CaseIterable {
    case competence, autonomy, relatedness, certainty, growth
}

public enum PsiCyclePhase: String, Codable {
    case idle, perceiving, selecting, acting, learning
}

public struct PsiImpulse: Codable {
    public let need: PsiNeed
    public let action: String
    public let target: String
    public let intensity: Double
    public let reason: String
    public let timestamp: Date

    public init(need: PsiNeed, action: String, target: String, intensity: Double, reason: String) {
        self.need = need
        self.action = action
        self.target = target
        self.intensity = intensity
        self.reason = reason
        self.timestamp = Date()
    }
}

public struct PsiLearningSnapshot: Codable {
    public let cycleId: Int64
    public let needBefore: NeedState
    public let needAfter: NeedState
    public let impulse: PsiImpulse
    public let satisfactionDelta: Double
    public let emotionBefore: EmotionalValence
    public let emotionAfter: EmotionalValence
}

@MainActor
public final class PSILoop: ObservableObject {
    public static let shared = PSILoop()

    private let bus = CognitiveBus.shared
    private let speciesLibrary = CognitiveSpeciesLibrary.shared
    private let metacognition = Metacognition.shared

    private var timer: Timer?
    private let queue = DispatchQueue(label: "laap.psiloop", qos: .userInitiated)

    @Published public private(set) var isRunning: Bool = false

    /// Tick interval in seconds. Default 1.0.
    public var tickInterval: TimeInterval = 1.0

    /// Drive weights per need.
    public var driveWeights: [PsiNeed: Double] = Dictionary(uniqueKeysWithValues: PsiNeed.allCases.map { ($0, 1.0) })

    /// LAAP Liquid NCP 模型（lazy 加载，从 Bundle 读取 ncp_model.json）。
    /// 加载失败时为 nil，runLiquidInference 将回退到零向量。
    public lazy var ncpModel: NCPModel? = { NCPModel.loadFromBundle() }()

    /// LAAP Liquid NCP 运行时（基于 ncpModel 创建，懒初始化）。
    public lazy var ncpRuntime: NCPRuntime? = {
        guard let model = ncpModel else { return nil }
        return NCPRuntime(model: model)
    }()

    /// NCP 隐状态（19 维），跨 tick 持续演化。
    private var ncpHidden: [Double] = []

    private var cycleCount: Int64 = 0

    public var lastImpulse: PsiImpulse? { metacognition.lastImpulse }

    private init() {}

    public func start() {
        guard !isRunning else { return }
        isRunning = true
        bus.publish(topic: "psi.lifecycle", payload: ["state": "started"])

        timer = Timer.scheduledTimer(withTimeInterval: tickInterval, repeats: true) { [weak self] _ in
            self?.queue.async { [weak self] in
                Task { @MainActor [weak self] in
                    await self?.tick()
                }
            }
        }
    }

    public func stop() {
        isRunning = false
        timer?.invalidate()
        timer = nil
        bus.publish(topic: "psi.lifecycle", payload: ["state": "stopped"])
    }

    public func tick() async {
        cycleCount += 1
        let cycleId = cycleCount

        setCycleState(.perceiving)
        let stateBefore = bus.state
        let needBefore = stateBefore.needs
        let emotionBefore = stateBefore.emotionalValence

        // ── LAAP Liquid NCP 推理：将当前注意力焦点 + 需求状态编码为 8 维输入，
        //    经 NCP 回路得到 5 维运动神经元响应（移动端轻量推理）──
        let perceptInput: [Double] = [
            needBefore.competence,
            needBefore.autonomy,
            needBefore.relatedness,
            needBefore.certainty,
            needBefore.growth,
            Double(stateBefore.attentionFocus.rawValue.count) / 8.0,
            stateBefore.selfPresenceLevel,
            min(1.0, Double(cycleCount) / 100.0)
        ]
        let motorResponse = runLiquidInference(perceptInput: perceptInput)
        // motorResponse 长度 = 5（运动神经元数量），用于驱动后续选择阶段
        bus.publish(topic: "lnn.mobile.inference", payload: [
            "phase": "perceive",
            "motor_dim": String(motorResponse.count),
            "motor_max": String(format: "%.4f", motorResponse.max() ?? 0.0),
            "cycle": String(cycleId)
        ])

        let curiosityIndex = computeCuriosityIndex(needBefore)
        let trustIndex = (needBefore.relatedness + needBefore.certainty) / 2.0

        bus.updatePsiMetrics { metrics in
            metrics.cycleState = PsiCyclePhase.perceiving.rawValue
            metrics.curiosityIndex = curiosityIndex
            metrics.trustIndex = trustIndex
            metrics.competenceAssessment = needBefore.competence
            metrics.cycleCount = cycleId
        }

        setCycleState(.selecting)
        let (dominantNeed, driveStrength) = selectDominantDrive(needBefore)
        let impulse = generateImpulse(dominantNeed, driveStrength: driveStrength, state: stateBefore)

        bus.updatePsiMetrics { metrics in
            metrics.cycleState = PsiCyclePhase.selecting.rawValue
            metrics.dominantDrive = dominantNeed.rawValue
            metrics.lastImpulse = impulse.action
        }
        metacognition.recordImpulse(impulse)

        setCycleState(.acting)
        publishImpulse(impulse)

        if let matched = speciesLibrary.search(query: impulse.action, type: .skill).first {
            speciesLibrary.updateUsage(id: matched.id, success: true, qualityScore: 0.8)
            bus.publish(topic: "psi.species.match", payload: [
                "species_id": matched.id,
                "action": impulse.action,
                "quality": String(format: "%.2f", matched.qualityScore)
            ])
        }

        setCycleState(.learning)
        let needAfter = applyImpulseToNeeds(needBefore, impulse: impulse)
        let emotionAfter = regulateEmotion(before: emotionBefore, impulse: impulse, needs: needAfter)
        let satisfactionDelta = computeSatisfactionDelta(before: needBefore, after: needAfter)

        bus.updateNeeds { needs in
            needs.competence = needAfter.competence
            needs.autonomy = needAfter.autonomy
            needs.relatedness = needAfter.relatedness
            needs.certainty = needAfter.certainty
            needs.growth = needAfter.growth
        }

        let snapshot = PsiLearningSnapshot(
            cycleId: cycleId,
            needBefore: needBefore,
            needAfter: needAfter,
            impulse: impulse,
            satisfactionDelta: satisfactionDelta,
            emotionBefore: emotionBefore,
            emotionAfter: emotionAfter
        )
        metacognition.learn(snapshot)

        bus.updatePsiMetrics { metrics in
            metrics.cycleState = PsiCyclePhase.learning.rawValue
            metrics.curiosityIndex = computeCuriosityIndex(needAfter)
            metrics.trustIndex = (needAfter.relatedness + needAfter.certainty) / 2.0
            metrics.competenceAssessment = needAfter.competence
            metrics.cycleCount = cycleId
        }

        metacognition.adaptLoop(psiLoop: self, snapshot: snapshot)
    }

    private func setCycleState(_ phase: PsiCyclePhase) {
        bus.updatePsiMetrics { $0.cycleState = phase.rawValue }
    }

    private func computeCuriosityIndex(_ needs: NeedState) -> Double {
        let deficits = [
            1.0 - needs.competence,
            1.0 - needs.autonomy,
            1.0 - needs.relatedness,
            1.0 - needs.certainty,
            1.0 - needs.growth
        ]
        let mean = deficits.reduce(0, +) / Double(deficits.count)
        let variance = deficits.map { ($0 - mean) * ($0 - mean) }.reduce(0, +) / Double(deficits.count)
        return min(1.0, mean + variance * 2.0)
    }

    private func selectDominantDrive(_ needs: NeedState) -> (PsiNeed, Double) {
        let drives: [PsiNeed: Double] = [
            .competence: (1.0 - needs.competence) * (driveWeights[.competence] ?? 1.0),
            .autonomy: (1.0 - needs.autonomy) * (driveWeights[.autonomy] ?? 1.0),
            .relatedness: (1.0 - needs.relatedness) * (driveWeights[.relatedness] ?? 1.0),
            .certainty: (1.0 - needs.certainty) * (driveWeights[.certainty] ?? 1.0),
            .growth: (1.0 - needs.growth) * (driveWeights[.growth] ?? 1.0)
        ]
        return drives.max { $0.value < $1.value } ?? (.competence, 0.0)
    }

    private func generateImpulse(_ need: PsiNeed, driveStrength: Double, state: CognitiveState) -> PsiImpulse {
        switch need {
        case .competence:
            return PsiImpulse(need: need, action: "skill_practice", target: "nearest_hard_task", intensity: driveStrength, reason: "competence deficit: seek mastery")
        case .autonomy:
            return PsiImpulse(need: need, action: "explore_options", target: "environment", intensity: driveStrength, reason: "autonomy deficit: expand choice space")
        case .relatedness:
            return PsiImpulse(need: need, action: "reach_out", target: "user", intensity: driveStrength, reason: "relatedness deficit: connect with user")
        case .certainty:
            return PsiImpulse(need: need, action: "verify_model", target: "current_context", intensity: driveStrength, reason: "certainty deficit: reduce ambiguity")
        case .growth:
            return PsiImpulse(need: need, action: "learn_new", target: "novel_perception", intensity: driveStrength, reason: "growth deficit: acquire new patterns")
        }
    }

    private func publishImpulse(_ impulse: PsiImpulse) {
        bus.publish(topic: "psi.impulse", payload: [
            "need": impulse.need.rawValue,
            "action": impulse.action,
            "target": impulse.target,
            "intensity": String(format: "%.3f", impulse.intensity),
            "reason": impulse.reason
        ])
    }

    private func applyImpulseToNeeds(_ needs: NeedState, impulse: PsiImpulse) -> NeedState {
        var next = needs
        let delta = 0.03 * impulse.intensity
        let noise = Double.random(in: -0.01...0.01)
        switch impulse.need {
        case .competence:
            next.competence = clamp(next.competence + delta + noise)
        case .autonomy:
            next.autonomy = clamp(next.autonomy + delta * 0.8 + noise)
        case .relatedness:
            next.relatedness = clamp(next.relatedness + delta + noise)
        case .certainty:
            next.certainty = clamp(next.certainty + delta * 0.9 + noise)
        case .growth:
            next.growth = clamp(next.growth + delta * 0.7 + noise)
        }
        next.competence = clamp(next.competence - 0.005)
        next.autonomy = clamp(next.autonomy - 0.005)
        next.relatedness = clamp(next.relatedness - 0.005)
        next.certainty = clamp(next.certainty - 0.005)
        next.growth = clamp(next.growth - 0.005)
        return next
    }

    private func regulateEmotion(before: EmotionalValence, impulse: PsiImpulse, needs: NeedState) -> EmotionalValence {
        if impulse.intensity > 0.8 { return .curious }
        if needs.competence < 0.3 || needs.certainty < 0.3 { return .confused }
        if before == .curious && impulse.need == .relatedness { return .positive_mild }
        return before
    }

    private func computeSatisfactionDelta(before: NeedState, after: NeedState) -> Double {
        let beforeSum = before.competence + before.autonomy + before.relatedness + before.certainty + before.growth
        let afterSum = after.competence + after.autonomy + after.relatedness + after.certainty + after.growth
        return afterSum - beforeSum
    }

    private func clamp(_ value: Double) -> Double {
        max(0.0, min(1.0, value))
    }

    // MARK: - LAAP Liquid NCP 推理

    /// 调用 LAAP Liquid NCP 进行单步推理，返回运动神经元响应（5 维）。
    ///
    /// 流程：
    ///   1. 若 NCP 运行时未初始化（Bundle 无 ncp_model.json），返回零向量并发布降级事件
    ///   2. 首次调用时初始化 19 维隐状态为零向量
    ///   3. 调用 NCPRuntime.forward 推进一个时间步（dt = tickInterval）
    ///   4. 返回新隐状态的运动神经元切片（5 维）
    ///   5. 发布 lnn.mobile.tick 事件到 CognitiveBus
    ///
    /// - Parameter perceptInput: 8 维感知输入（焦点编码）
    /// - Returns: 5 维运动神经元响应；运行时不可用时返回 5 个 0.0
    @discardableResult
    public func runLiquidInference(perceptInput: [Double]) -> [Double] {
        let dt = tickInterval
        guard let runtime = ncpRuntime else {
            // 降级：NCP 模型未加载，返回零向量并发布降级事件
            bus.publish(topic: "lnn.mobile.degraded", payload: [
                "reason": "ncp_model_unavailable",
                "fallback": "zero_vector"
            ])
            return [Double](repeating: 0.0, count: 5)
        }

        if ncpHidden.isEmpty {
            ncpHidden = runtime.defaultState()
        }

        let newH = runtime.forward(h: ncpHidden, x: perceptInput, dt: dt)
        ncpHidden = newH

        // 运动神经元响应 = newH[motorRange]（最后 5 维）
        let motorStart = newH.count - runtime.nMotor
        let motorResponse = Array(newH[motorStart..<newH.count])

        // 发布推理事件
        let cmdAct = runtime.getCommandActivations()
        bus.publish(topic: "lnn.mobile.tick", payload: [
            "dt": String(format: "%.4f", dt),
            "motor_max": String(format: "%.4f", motorResponse.max() ?? 0.0),
            "cmd_sum": String(format: "%.4f", cmdAct.reduce(0, +)),
            "hidden_norm": String(format: "%.4f", sqrt(newH.map { $0 * $0 }.reduce(0, +)))
        ])
        return motorResponse
    }
}
