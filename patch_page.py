from pathlib import Path
f = Path(r"D:/ai-website-cloner-template-master/src/app/demo-multiplayer/page.tsx")
c = f.read_text(encoding="utf-8")

# 1. imports
if 'TRACKS' not in c:
    c = c.replace(
        'import { useMultiplayerSync } from "./MultiplayerSync";',
        'import * as THREE from "three";\nimport { useMultiplayerSync } from "./MultiplayerSync";',
        1
    )
    c = c.replace(
        'import { getAudioManager } from "@/lib/audio/AudioManager";',
        'import { getAudioManager } from "@/lib/audio/AudioManager";\nimport { TRACKS } from "@/lib/racing/tracks";',
        1
    )

# 2. CameraMode type
if 'CameraMode' not in c:
    c = c.replace(
        'type RacePhase = "menu" | "lobby" | "countdown" | "racing" | "finished";',
        'type RacePhase = "menu" | "lobby" | "countdown" | "racing" | "finished";\ntype CameraMode = "chase" | "first" | "orbit";',
        1
    )

# 3. CAMERA_MODE_LABEL
if 'CAMERA_MODE_LABEL' not in c:
    c = c.replace(
        'const PLAYER_COLORS',
        'const CAMERA_MODE_LABEL: Record<CameraMode, string> = {\n  chase: "追尾视角",\n  first: "第一人称",\n  orbit: "轨道视角",\n};\n\nconst PLAYER_COLORS',
        1
    )

# 4. cameraMode + telemetry + trackData state
if 'cameraMode' not in c:
    c = c.replace(
        '  const [remoteGhost, setRemoteGhost] = useState<any[] | null>(null);\n\n  const localVehicleRef = useRef(null);',
        '  const [remoteGhost, setRemoteGhost] = useState<any[] | null>(null);\n\n  // 视角与速度遥测\n  const [cameraMode, setCameraMode] = useState<CameraMode>("chase");\n  const [telemetry, setTelemetry] = useState({ speed: 0, rpm: 0, gear: 1 });\n\n  const localVehicleRef = useRef(null);',
        1
    )

if 'trackData' not in c:
    c = c.replace(
        '  const audioManager = useMemo(() => getAudioManager(), []);\n\n  // === 多人同步 ===',
        '  const audioManager = useMemo(() => getAudioManager(), []);\n\n  // 赛道数据（用于 spawnPoint 和 spawnHeading）\n  const trackData = useMemo(() => TRACKS.lagunaSeca, []);\n\n  // === 多人同步 ===',
        1
    )

# 5. handleToggleCamera
if 'handleToggleCamera' not in c:
    c = c.replace(
        '  // === 模拟圈完成',
        '  // === 切换视角 ===\n  const handleToggleCamera = () => {\n    setCameraMode((prev) => (prev === "chase" ? "first" : prev === "first" ? "orbit" : "chase"));\n  };\n\n  // === 模拟圈完成',
        1
    )

# 6. Scene3D props
if 'onSpeedUpdate' not in c:
    c = c.replace(
        '          physicsEnabled={racePhase === "racing" || racePhase === "countdown"}\n          racePhase={SCENE_PHASE_MAP[racePhase]}\n          audioEnabled={true}',
        '          physicsEnabled={racePhase === "racing" || racePhase === "countdown"}\n          racePhase={SCENE_PHASE_MAP[racePhase]}\n          spawnPoint={trackData.spawnPoint}\n          spawnHeading={trackData.spawnHeading}\n          cameraMode={cameraMode}\n          onCameraModeChange={(m) => setCameraMode(m as CameraMode)}\n          onSpeedUpdate={(speed, rpm, gear) => setTelemetry({ speed, rpm, gear })}\n          audioEnabled={true}',
        1
    )

f.write_text(c, encoding="utf-8")
print("OK: page.tsx patched, len =", len(c))
print("has cameraMode:", 'cameraMode' in c)
print("has trackData:", 'trackData' in c)
print("has onSpeedUpdate:", 'onSpeedUpdate' in c)
print("has handleToggleCamera:", 'handleToggleCamera' in c)
