//
//  CognitiveBus.swift
//  LAAP Mobile
//
//  LAAP 认知总线原生实现
//  对应 LAAP 桌面端: laap/agi/cognitive_bus.py
//
//  This file is part of LAAP Mobile, licensed under GPL v3.
//

import Foundation
import Combine

// MARK: - Core Types

public enum AttentionFocus: String, Codable {
    case user, task, self_ref, environment, memory, planning, learning, idle
}

public enum EmotionalValence: String, Codable {
    case positive_high, positive_mild, neutral
    case negative_mild, negative_high
    case curious, confused
}

public struct NeedState: Codable {
    public var competence: Double = 0.7
    public var autonomy: Double = 0.5
    public var relatedness: Double = 0.5
    public var certainty: Double = 0.5
    public var growth: Double = 0.5

    public init() {}

    public func strongestNeed() -> (String, Double) {
        let deficits = [
            "competence": 1.0 - competence,
            "autonomy": 1.0 - autonomy,
            "relatedness": 1.0 - relatedness,
            "certainty": 1.0 - certainty,
            "growth": 1.0 - growth
        ]
        return deficits.max { $0.value < $1.value } ?? ("competence", 0.0)
    }
}

public struct PsiMetrics: Codable {
    public var cycleState: String = "idle"
    public var curiosityIndex: Double = 0.5
    public var trustIndex: Double = 0.5
    public var competenceAssessment: Double = 0.7
    public var selfPresenceLevel: Double = 0.5
    public var cycleCount: Int64 = 0
    public var dominantDrive: String = "none"
    public var lastImpulse: String = ""

    public init() {}
}

public struct CognitiveState: Codable {
    public var needs = NeedState()
    public var emotionalValence: EmotionalValence = .neutral
    public var attentionFocus: AttentionFocus = .idle
    public var selfPresenceLevel: Double = 0.5
    public var psiMetrics = PsiMetrics()
    public var timestamp: Date = Date()

    public init() {}
}

public struct CognitiveEvent: Codable {
    public let topic: String
    public let payload: [String: String]
    public let timestamp: Date

    public init(topic: String, payload: [String: String] = [:]) {
        self.topic = topic
        self.payload = payload
        self.timestamp = Date()
    }
}

// MARK: - CognitiveBus

@MainActor
public final class CognitiveBus: ObservableObject {
    public static let shared = CognitiveBus()

    @Published public private(set) var state = CognitiveState()

    private var subscribers: [String: [(CognitiveEvent) -> Void]] = [:]
    private let queue = DispatchQueue(label: "laap.cognitivebus", qos: .userInitiated)

    private init() {}

    /// Publish an event to all subscribers of `topic`.
    public func publish(topic: String, payload: [String: String] = [:]) {
        let event = CognitiveEvent(topic: topic, payload: payload)
        queue.async { [weak self] in
            guard let self = self else { return }
            let handlers = self.subscribers[topic] ?? []
            DispatchQueue.main.async {
                handlers.forEach { $0(event) }
                self.applyEvent(event)
            }
        }
    }

    /// Subscribe to events on a topic.
    public func subscribe(topic: String, handler: @escaping (CognitiveEvent) -> Void) {
        queue.async { [weak self] in
            self?.subscribers[topic, default: []].append(handler)
        }
    }

    /// Update needs directly (used by PSI loop).
    public func updateNeeds(_ updater: (inout NeedState) -> Void) {
        queue.async { [weak self] in
            guard let self = self else { return }
            var needs = self.state.needs
            updater(&needs)
            DispatchQueue.main.async {
                self.state.needs = needs
                self.state.timestamp = Date()
            }
        }
    }

    /// Update PSI metrics directly (used by PSI loop).
    public func updatePsiMetrics(_ updater: (inout PsiMetrics) -> Void) {
        queue.async { [weak self] in
            guard let self = self else { return }
            var metrics = self.state.psiMetrics
            updater(&metrics)
            DispatchQueue.main.async {
                self.state.psiMetrics = metrics
                self.state.timestamp = Date()
            }
        }
    }

    /// Mobile perception events feed into the bus.
    public func perceive(type: String, description: String, location: String? = nil, confidence: Double = 0.5) {
        var payload: [String: String] = [
            "type": type,
            "description": description,
            "confidence": String(format: "%.3f", confidence)
        ]
        if let location = location {
            payload["location"] = location
        }
        publish(topic: "qre.perception.mobile", payload: payload)
    }

    private func applyEvent(_ event: CognitiveEvent) {
        switch event.topic {
        case "qre.perception.mobile":
            state.attentionFocus = .environment
            state.emotionalValence = .curious
            state.needs.growth = min(1.0, state.needs.growth + 0.05)
        case "qre.perception.user":
            state.attentionFocus = .user
            state.needs.relatedness = min(1.0, state.needs.relatedness + 0.03)
        case "emotion.negative_mild":
            state.emotionalValence = .negative_mild
        case "emotion.curious":
            state.emotionalValence = .curious
        default:
            break
        }
        state.timestamp = Date()
    }
}
