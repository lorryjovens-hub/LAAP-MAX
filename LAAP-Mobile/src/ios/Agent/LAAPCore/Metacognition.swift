//
//  Metacognition.swift
//  LAAP Mobile
//
//  LAAP 元认知监控原生实现
//  对应 LAAP 桌面端: laap/agi/metacognition.py
//
//  This file is part of LAAP Mobile, licensed under GPL v3.
//

import Foundation

public struct MetacognitionConfig: Codable {
    public var minTickInterval: TimeInterval = 0.5
    public var maxTickInterval: TimeInterval = 5.0
    public var satisfactionWindowSize: Int = 10
    public var lowSatisfactionThreshold: Double = -0.05
    public var highSatisfactionThreshold: Double = 0.05
    public var emotionRegulationThreshold: Double = 0.2

    public init() {}
}

@MainActor
public final class Metacognition: ObservableObject {
    public static let shared = Metacognition()

    private let bus = CognitiveBus.shared

    public var config = MetacognitionConfig()

    private var satisfactionHistory: [Double] = []
    private var impulseHistory: [PsiImpulse] = []

    @Published public private(set) var lastImpulse: PsiImpulse?
    private var regulationCount: Int64 = 0

    private init() {}

    public func recordImpulse(_ impulse: PsiImpulse) {
        lastImpulse = impulse
        impulseHistory.append(impulse)
        if impulseHistory.count > config.satisfactionWindowSize {
            impulseHistory.removeFirst()
        }
    }

    public func learn(_ snapshot: PsiLearningSnapshot) {
        satisfactionHistory.append(snapshot.satisfactionDelta)
        if satisfactionHistory.count > config.satisfactionWindowSize {
            satisfactionHistory.removeFirst()
        }

        let avg = satisfactionHistory.reduce(0, +) / Double(satisfactionHistory.count)

        if avg < config.emotionRegulationThreshold {
            regulateEmotion(snapshot)
        }

        if snapshot.satisfactionDelta > config.highSatisfactionThreshold {
            bus.publish(topic: "emotion.positive_mild", payload: [
                "cycle_id": String(snapshot.cycleId),
                "delta": String(format: "%.3f", snapshot.satisfactionDelta)
            ])
        }
    }

    public func adaptLoop(psiLoop: PSILoop, snapshot: PsiLearningSnapshot) {
        let avg = satisfactionHistory.reduce(0, +) / Double(max(satisfactionHistory.count, 1))

        let newInterval: TimeInterval
        if avg < config.lowSatisfactionThreshold {
            newInterval = max(config.minTickInterval, psiLoop.tickInterval - 0.2)
        } else if avg > config.highSatisfactionThreshold {
            newInterval = min(config.maxTickInterval, psiLoop.tickInterval + 0.2)
        } else {
            newInterval = psiLoop.tickInterval
        }

        if newInterval != psiLoop.tickInterval {
            psiLoop.tickInterval = newInterval
            // Restart timer to pick up new interval.
            if psiLoop.isRunning {
                psiLoop.stop()
                psiLoop.start()
            }
            bus.publish(topic: "psi.metacognition.interval", payload: [
                "interval_ms": String(format: "%.0f", newInterval * 1000)
            ])
        }

        var weights = psiLoop.driveWeights
        let need = snapshot.impulse.need
        if snapshot.satisfactionDelta < config.lowSatisfactionThreshold {
            weights[need] = min(2.0, (weights[need] ?? 1.0) * 1.1)
            regulationCount += 1
            bus.publish(topic: "psi.metacognition.weight", payload: [
                "need": need.rawValue,
                "weight": String(format: "%.3f", weights[need] ?? 1.0)
            ])
        }
        psiLoop.driveWeights = weights
    }

    private func regulateEmotion(_ snapshot: PsiLearningSnapshot) {
        regulationCount += 1
        let need = snapshot.impulse.need
        bus.publish(topic: "emotion.negative_mild", payload: [
            "cycle_id": String(snapshot.cycleId),
            "need": need.rawValue,
            "reason": "long-term low satisfaction triggers regulation"
        ])
    }

    public func summary() -> [String: String] {
        let avg = satisfactionHistory.isEmpty ? 0.0 : satisfactionHistory.reduce(0, +) / Double(satisfactionHistory.count)
        return [
            "avg_satisfaction": String(format: "%.3f", avg),
            "regulation_count": String(regulationCount),
            "impulse_history_size": String(impulseHistory.count),
            "last_impulse": lastImpulse?.action ?? "none",
            "last_impulse_reason": lastImpulse?.reason ?? ""
        ]
    }
}
