//
//  CognitiveSpeciesLibrary.swift
//  LAAP Mobile
//
//  LAAP 认知物种库原生实现
//  对应 LAAP 桌面端: harness/laap_coding/core/cognitive_species_library.py
//
//  This file is part of LAAP Mobile, licensed under GPL v3.
//

import Foundation

public enum SpeciesType: String, Codable {
    case component, skill, ability
}

public enum SpeciesOrigin: String, Codable {
    case compiled, imported, evolved
}

public struct Species: Identifiable, Codable {
    public let id: String
    public var name: String
    public var type: SpeciesType
    public var origin: SpeciesOrigin
    public var template: String
    public var props: [String: String]
    public var dependencies: [String]
    public var successRate: Double
    public var usageCount: Int
    public var qualityScore: Double
    public var tags: [String]
    public var domain: [String]
    public var createdAt: Date
    public var lastUsed: Date

    public init(
        id: String,
        name: String,
        type: SpeciesType,
        origin: SpeciesOrigin,
        template: String,
        props: [String: String] = [:],
        dependencies: [String] = [],
        tags: [String] = [],
        domain: [String] = []
    ) {
        self.id = id
        self.name = name
        self.type = type
        self.origin = origin
        self.template = template
        self.props = props
        self.dependencies = dependencies
        self.successRate = 1.0
        self.usageCount = 0
        self.qualityScore = 0.0
        self.tags = tags
        self.domain = domain
        self.createdAt = Date()
        self.lastUsed = Date()
    }
}

@MainActor
public final class CognitiveSpeciesLibrary: ObservableObject {
    public static let shared = CognitiveSpeciesLibrary()

    @Published public private(set) var species: [String: Species] = [:]

    private init() {}

    public func register(_ species: Species) {
        self.species[species.id] = species
    }

    public func get(id: String) -> Species? {
        species[id]
    }

    public func listAll() -> [Species] {
        Array(species.values)
    }

    public func search(query: String, type: SpeciesType? = nil) -> [Species] {
        let q = query.lowercased()
        return species.values.filter { sp in
            if let type = type, sp.type != type { return false }
            let haystack = "\(sp.name) \(sp.tags.joined(separator: " ")) \(sp.domain.joined(separator: " "))".lowercased()
            return haystack.contains(q)
        }
    }

    public func updateUsage(id: String, success: Bool, qualityScore: Double? = nil) {
        guard var sp = species[id] else { return }
        sp.usageCount += 1
        sp.lastUsed = Date()
        if let quality = qualityScore {
            sp.qualityScore = (sp.qualityScore * Double(sp.usageCount - 1) + quality) / Double(sp.usageCount)
        }
        if success {
            sp.successRate = min(1.0, (sp.successRate * Double(sp.usageCount - 1) + 1.0) / Double(sp.usageCount))
        }
        species[id] = sp
    }
}
