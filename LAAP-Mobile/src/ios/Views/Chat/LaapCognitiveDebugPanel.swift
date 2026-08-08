//
//  LaapCognitiveDebugPanel.swift
//  LAAP Mobile
//
//  iOS 首个端到端验证面板：移动感知 → CognitiveBus → UI 状态
//
//  This file is part of LAAP Mobile, licensed under GPL v3.
//

import SwiftUI

struct LaapCognitiveDebugPanel: View {
    @ObservedObject var vm: AIChatViewModel
    @State private var isExpanded = true

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("LAAP 认知状态")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(Color(red: 0.0, green: 0.83, blue: 0.67))
                Spacer()
                Button(action: { isExpanded.toggle() }) {
                    Image(systemName: isExpanded ? "chevron.down" : "chevron.up")
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)

            if isExpanded {
                VStack(alignment: .leading, spacing: 6) {
                    let psi = vm.cognitiveState.psiMetrics
                    Text("PSI 循环状态: \(psi.cycleState) | 主导驱动: \(psi.dominantDrive)")
                        .font(.system(size: 11))
                        .foregroundColor(Color(red: 0.0, green: 0.83, blue: 0.67))
                    Text(String(
                        format: "好奇心指数=%.2f  信任感指标=%.2f  胜任感评估=%.2f",
                        psi.curiosityIndex,
                        psi.trustIndex,
                        psi.competenceAssessment
                    ))
                    .font(.system(size: 10))
                    .foregroundColor(Color(red: 0.0, green: 0.9, blue: 1.0))
                    Text("Attention: \(vm.cognitiveState.attentionFocus.rawValue) | Emotion: \(vm.cognitiveState.emotionalValence.rawValue) | Presence: %.2f".format(psi.selfPresenceLevel))
                        .font(.system(size: 11))
                        .foregroundColor(.primary)
                    Text(String(
                        format: "Competence=%.2f Autonomy=%.2f Relatedness=%.2f Certainty=%.2f Growth=%.2f",
                        vm.cognitiveState.needs.competence,
                        vm.cognitiveState.needs.autonomy,
                        vm.cognitiveState.needs.relatedness,
                        vm.cognitiveState.needs.certainty,
                        vm.cognitiveState.needs.growth
                    ))
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
                    if !psi.lastImpulse.isEmpty {
                        Text("Last impulse: \(psi.lastImpulse)")
                            .font(.system(size: 10))
                            .foregroundColor(.orange)
                    }

                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 6) {
                        perceptionButton("Camera", type: "camera", description: "User shared a photo of a workspace", confidence: 0.85)
                        perceptionButton("Health", type: "health", description: "Steps today: 7234", confidence: 0.9)
                        perceptionButton("Notify", type: "notification", description: "Meeting reminder from calendar", confidence: 0.95)
                        perceptionButton("GPS", type: "gps", description: "", confidence: 0.9)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.bottom, 10)
            }
        }
        .background(Color(UIColor.secondarySystemBackground))
        .cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.secondary.opacity(0.2), lineWidth: 1))
        .padding(.horizontal, 12)
        .padding(.top, 4)
    }

    private func perceptionButton(_ title: String, type: String, description: String, confidence: Double) -> some View {
        Button(action: {
            vm.triggerPerception(type: type, description: description, confidence: confidence)
        }) {
            Text(title)
                .font(.system(size: 12, weight: .medium))
                .lineLimit(1)
                .minimumScaleFactor(0.8)
                .foregroundColor(.primary)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 6)
                .background(Color(UIColor.tertiarySystemBackground))
                .cornerRadius(8)
        }
    }
}
