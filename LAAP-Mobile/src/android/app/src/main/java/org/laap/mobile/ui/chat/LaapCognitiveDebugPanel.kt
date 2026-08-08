/*
 * LaapCognitiveDebugPanel.kt
 *
 * LAAP 首个端到端验证面板：移动感知 → CognitiveBus → UI 状态
 *
 * This file is part of LAAP Mobile, licensed under GPL v3.
 */

package org.laap.mobile.ui.chat

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import org.laap.mobile.laap.CognitiveState
import org.laap.mobile.laap.PsiForegroundService

@Composable
fun LaapCognitiveDebugPanel(
    viewModel: ChatViewModel,
    modifier: Modifier = Modifier,
) {
    val cognitiveState by viewModel.cognitiveState.collectAsState()
    var isExpanded by rememberSaveable { mutableStateOf(true) }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(8.dp),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF1A1A2E)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "LAAP 认知状态",
                    color = Color(0xFF00D4AA),
                    style = MaterialTheme.typography.titleSmall
                )
                IconButton(onClick = { isExpanded = !isExpanded }) {
                    Icon(
                        imageVector = if (isExpanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = if (isExpanded) "折叠" else "展开",
                        tint = Color(0xFF00D4AA)
                    )
                }
            }
            AnimatedVisibility(visible = isExpanded) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    CognitiveStateText(cognitiveState)
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Button(
                            onClick = { viewModel.triggerPerception("camera", "User shared a photo of a workspace", 0.85) },
                            modifier = Modifier.weight(1f)
                        ) { Text("Camera", maxLines = 1) }
                        Button(
                            onClick = { viewModel.triggerPerception("health", "Steps today: 7234", 0.9) },
                            modifier = Modifier.weight(1f)
                        ) { Text("Health", maxLines = 1) }
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Button(
                            onClick = { viewModel.triggerPerception("notification", "Meeting reminder from calendar", 0.95) },
                            modifier = Modifier.weight(1f)
                        ) { Text("Notify", maxLines = 1) }
                        Button(
                            onClick = { viewModel.triggerPerception("gps", "", confidence = 0.9) },
                            modifier = Modifier.weight(1f)
                        ) { Text("GPS", maxLines = 1) }
                    }
                }
            }
        }
    }
}

@Composable
private fun CognitiveStateText(state: CognitiveState) {
    val needs = state.needs
    val psi = state.psiMetrics
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            text = "PSI 循环状态: ${psi.cycleState} | 主导驱动: ${psi.dominantDrive}",
            color = Color(0xFF00D4AA),
            style = MaterialTheme.typography.bodySmall
        )
        Text(
            text = "好奇心指数=%.2f  信任感指标=%.2f  胜任感评估=%.2f".format(
                psi.curiosityIndex, psi.trustIndex, psi.competenceAssessment
            ),
            color = Color(0xFF00E5FF),
            style = MaterialTheme.typography.bodySmall
        )
        Text(
            text = "Attention: ${state.attentionFocus.name} | Emotion: ${state.emotionalValence.name} | Presence: %.2f".format(psi.selfPresenceLevel),
            color = Color.White,
            style = MaterialTheme.typography.bodySmall
        )
        Text(
            text = "Competence=%.2f Autonomy=%.2f Relatedness=%.2f Certainty=%.2f Growth=%.2f".format(
                needs.competence, needs.autonomy, needs.relatedness, needs.certainty, needs.growth
            ),
            color = Color(0xFFB0B0B0),
            style = MaterialTheme.typography.bodySmall
        )
        if (psi.lastImpulse.isNotBlank()) {
            Text(
                text = "Last impulse: ${psi.lastImpulse}",
                color = Color(0xFFFFD700),
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

/**
 * LifeformDashboard — M1 deliverable (integration plan §436/§510/§661).
 *
 * Extends the legacy [LaapCognitiveDebugPanel] into a full "数字生命仪表盘"
 * surfacing the 5 PSI indicators the plan requires:
 *   1. PSI 循环状态 (cycleState + dominantDrive)
 *   2. 好奇心指数 (curiosityIndex)
 *   3. 信任感指标 (trustIndex)
 *   4. 胜任感评估 (competenceAssessment)
 *   5. 自我存在感 (selfPresenceLevel)
 *
 * Plus the M1 additions: PAD emotion (pleasure/arousal/dominance), cycle
 * count, memory-association size, last harness outcome, and the PSI
 * foreground-service alive badge — so the user can tell at a glance
 * whether the lifeform is actually ticking in the background.
 *
 * Same dark theme as the legacy panel so the two compose cleanly when
 * shown together during the M1→M2 transition.
 */
@Composable
fun LifeformDashboard(
    viewModel: ChatViewModel,
    modifier: Modifier = Modifier,
) {
    val cognitiveState by viewModel.cognitiveState.collectAsState()
    var isExpanded by rememberSaveable { mutableStateOf(true) }
    val psi = cognitiveState.psiMetrics
    val serviceAlive = PsiForegroundService.isServiceRunning()

    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(8.dp),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF1A1A2E)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = "数字生命仪表盘",
                        color = Color(0xFF00D4AA),
                        style = MaterialTheme.typography.titleSmall
                    )
                    // PSI foreground-service alive badge.
                    Text(
                        text = if (serviceAlive) "● alive" else "○ idle",
                        color = if (serviceAlive) Color(0xFF00E676) else Color(0xFFB0B0B0),
                        style = MaterialTheme.typography.labelSmall
                    )
                }
                IconButton(onClick = { isExpanded = !isExpanded }) {
                    Icon(
                        imageVector = if (isExpanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = if (isExpanded) "折叠" else "展开",
                        tint = Color(0xFF00D4AA)
                    )
                }
            }
            AnimatedVisibility(visible = isExpanded) {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    // ── 5 指标 (plan §510) ────────────────────────────────
                    IndicatorRow("PSI 循环", psi.cycleState, Color(0xFF00D4AA))
                    IndicatorRow("主导驱动", psi.dominantDrive, Color(0xFF00D4AA))
                    IndicatorRow("好奇心指数", "%.3f".format(psi.curiosityIndex), Color(0xFF00E5FF))
                    IndicatorRow("信任感指标", "%.3f".format(psi.trustIndex), Color(0xFF00E5FF))
                    IndicatorRow("胜任感评估", "%.3f".format(psi.competenceAssessment), Color(0xFF00E5FF))
                    IndicatorRow("自我存在感", "%.3f".format(psi.selfPresenceLevel), Color(0xFF00E5FF))

                    // ── PAD emotion (psi.py PSIState.update_emotions) ────
                    val pad = psi.padEmotion
                    Text(
                        text = "PAD  P=%.2f  A=%.2f  D=%.2f  → %s".format(
                            pad.pleasure, pad.arousal, pad.dominance, pad.dominantFeeling
                        ),
                        color = Color(0xFFE1BEE7),
                        style = MaterialTheme.typography.bodySmall
                    )

                    // ── Cycle count + memory + last outcome ──────────────
                    val outcomeStr = when (psi.lastOutcomeSuccess) {
                        null -> "—"
                        true -> "success"
                        false -> "failed"
                    }
                    Text(
                        text = "cycle=%d  mem=%d  last_outcome=%s".format(
                            psi.cycleCount, psi.memoryAssociationsSize, outcomeStr
                        ),
                        color = Color(0xFFB0B0B0),
                        style = MaterialTheme.typography.bodySmall
                    )

                    // ── 5 needs (legacy, kept for continuity) ────────────
                    val needs = cognitiveState.needs
                    Text(
                        text = "Competence=%.2f Autonomy=%.2f Relatedness=%.2f Certainty=%.2f Growth=%.2f".format(
                            needs.competence, needs.autonomy, needs.relatedness, needs.certainty, needs.growth
                        ),
                        color = Color(0xFFB0B0B0),
                        style = MaterialTheme.typography.bodySmall
                    )
                    if (psi.lastImpulse.isNotBlank()) {
                        Text(
                            text = "Last impulse: ${psi.lastImpulse}",
                            color = Color(0xFFFFD700),
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun IndicatorRow(label: String, value: String, valueColor: Color) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            color = Color(0xFFB0B0B0),
            style = MaterialTheme.typography.bodySmall
        )
        Text(
            text = value,
            color = valueColor,
            style = MaterialTheme.typography.bodySmall
        )
    }
}
