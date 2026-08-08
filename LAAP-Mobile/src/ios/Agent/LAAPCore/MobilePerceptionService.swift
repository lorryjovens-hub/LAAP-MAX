//
//  MobilePerceptionService.swift
//  LAAP Mobile
//
//  移动感知事件采集与发布
//
//  This file is part of LAAP Mobile, licensed under GPL v3.
//

import Foundation
import CoreLocation

@MainActor
public final class MobilePerceptionService: NSObject, ObservableObject {
    public static let shared = MobilePerceptionService()

    private let locationManager = CLLocationManager()

    private override init() {
        super.init()
        locationManager.delegate = self
    }

    public func start() {
        locationManager.requestWhenInUseAuthorization()
    }

    public func perceiveCamera(description: String, confidence: Double = 0.8) {
        CognitiveBus.shared.perceive(type: "camera", description: description, confidence: confidence)
    }

    public func perceiveHealth(description: String, confidence: Double = 0.9) {
        CognitiveBus.shared.perceive(type: "health", description: description, confidence: confidence)
    }

    public func perceiveNotification(title: String, body: String) {
        CognitiveBus.shared.perceive(
            type: "notification",
            description: "[\(title)] \(body)",
            confidence: 0.95
        )
    }

    public func perceiveCalendar(event: String) {
        CognitiveBus.shared.perceive(type: "calendar", description: event, confidence: 0.95)
    }

    public func perceiveClipboard(content: String) {
        CognitiveBus.shared.perceive(type: "clipboard", description: content, confidence: 0.7)
    }

    public func requestLocationUpdate() {
        locationManager.requestLocation()
    }
}

extension MobilePerceptionService: CLLocationManagerDelegate {
    nonisolated public func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let loc = locations.last else { return }
        let desc = "lat:\(loc.coordinate.latitude), lon:\(loc.coordinate.longitude), alt:\(loc.altitude)"
        Task { @MainActor in
            CognitiveBus.shared.perceive(type: "gps", description: desc, confidence: 0.9)
        }
    }

    nonisolated public func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        Task { @MainActor in
            CognitiveBus.shared.publish(topic: "qre.perception.error", payload: ["type": "gps", "error": error.localizedDescription])
        }
    }
}
