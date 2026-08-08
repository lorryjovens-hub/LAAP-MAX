//
//  ArisEngineClient.swift
//  LAAP Mobile
//
//  Aris Engine HTTP/WebSocket 客户端
//  对应 LAAP 桌面端: self_model_bridge/aris_engine.py
//
//  This file is part of LAAP Mobile, licensed under GPL v3.
//

import Foundation

public actor ArisEngineClient {
    public static let shared = ArisEngineClient()

    public var baseURL: URL = URL(string: "http://127.0.0.1:9876")!
    public var isLocal: Bool = false

    private init() {}

    public func configure(baseURL: URL, isLocal: Bool = false) {
        self.baseURL = baseURL
        self.isLocal = isLocal
    }

    public func cycle(input: String, source: String = "mobile") async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent("/cycle")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = ["input": input, "source": source]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }

    public func getState() async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent("/state")
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }

    public func getVitals() async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent("/vitals")
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }

    public func observe(llmText: String) async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent("/observe")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["llm_text": llmText])

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }
}
