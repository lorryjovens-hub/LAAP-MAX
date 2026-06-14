# LAAP Virtual Character Engine - Full Architecture Plan

Version: 1.0.0
Date: 2026-06-12
Tech Stack: Python + Rust + Three.js + ESP32

---

## Chapter 1: System Overview

### 1.1 Vision

Build a living virtual character engine - a digital lifeform that can:
- See (camera/screenshot perception)
- Hear (ASR voice input)
- Speak (TTS voice output)
- Feel (14 emotions with decay)
- Remember (L0-L4 memory hierarchy)
- Act (51 tools: GUI/browser/file/code)
- Evolve (4-zone safe evolution)
- Express (3D model with morphs + VMD motion)

### 1.2 Three Client Architecture

```
+------------------------------------------------------------+
|              LAAP Digital Lifeform Core                    |
|  (LifeformAgent + EmotionSystem + 51 Tools + Memory)      |
+---------------------------+-------------------------------
                            |
            +---------------+---------------+
            |               |               |
    +-------+----+   +-----+------+   +-----+-------+
    | Tauri      |   | Web        |   | ESP32      |
    | Desktop    |   | Browser    |   | Hardware   |
    | Rust+React |   | Three.js   |   | C+++WiFi   |
    +------------+   +-----------+   +-----------+
```

### 1.3 Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | LAAP Python (LifeformAgent) |
| LLM | DeepSeek-v4-flash / OpenAI |
| TTS | xiaozhi Edge TTS / GPT-SoVITS |
| ASR | xiaozhi SenseVoice / Whisper |
| 3D Desktop | mmdpy + PyOpenGL + GLFW |
| 3D Web | Three.js + MMDLoader |
| Desktop App | Tauri (Rust + React) |
| Hardware | ESP32-S3 + INMP441 + MAX98357 |
| IPC | WebSocket + MQTT + mp.Queue |
| GUI Control | pyautogui (11 tools) |
| Browser | Playwright (14 tools) |

---

## Chapter 2: Data Flow

### 2.1 Text Chat

```
User -> Tauri/Web -> WebSocket -> AvatarBridge
  -> LifeformAgent.chat(text)
    -> DigitalLifeform.perceive(text)
      -> EmotionSystem.trigger()
      -> PhysiologyEngine.tick()
      -> WorkingMemory.store()
    -> LLM.chat_stream() -> tokens -> frontend
    -> Tool execution (if needed)
    -> Memory consolidation (L0->L1->L2)
  -> Return result
  -> AvatarBridge: emotion -> 3D morph
  -> TTS -> audio output
```

### 2.2 Voice Chat

```
User speaks -> ESP32 mic -> Opus stream
  -> xiaozhi ASR -> text
  -> Same as text chat flow
  -> Response -> TTS -> Opus -> speaker
```

---

## Chapter 3: Digital Lifeform Core

### 3.1 LifeformAgent

Extends LifelikeAgent with full lifeform integration:
- chat() injects personality/emotion/vitals into system prompt
- reflect() returns complete state report
- _sync_emotion_to_avatar() drives 3D expression

### 3.2 Emotion System (14 emotions)

Three-layer architecture:
L1: Instant emotions (0-30s decay)
L2: Mood (minutes-hours drift)
L3: Affective memory (50 events)

Emotion triggers:
- user_praise -> joy(40%) gratitude(30%) pride(20%)
- user_criticism -> sadness(30%) shame(25%) anxiety(15%)
- tool_success -> joy(30%) pride(20%)
- tool_failure -> sadness(30%) anger(15%)
- novelty -> curiosity(40%) surprise(30%)
- interaction -> curiosity(15%) joy(10%)

### 3.3 Physiology Engine

Vital signs updated every heartbeat tick:
- energy: 0-1, costs 0.02 per tool call
- focus: 0-1, decays 0.01 per turn
- mood: 0-1, affected by emotions
- curiosity: 0-1, increases with novelty
- stress: 0-1, accumulates on failures

### 3.4 Memory System (L0-L4)

| Level | Name | Capacity | Persistence |
|-------|------|----------|-------------|
| L0 | Working Memory | 20 items | RAM |
| L1 | Episodic Memory | unlimited | SQLite |
| L2 | Semantic Memory | unlimited | JSON |
| L3 | Muscle Memory | 100+ | JSON |
| L4 | Vector Memory | unlimited | Vector DB |

---

## Chapter 4: 3D Rendering

### 4.1 Desktop (mmdpy + GLFW)

mmdpy library (27 files, 162KB):
- PMX/PMD model loading + rendering
- VMD motion file playback
- Bone IK system with physics
- Facial morph targets
- OpenGL 3.3+ with GLFW window

### 4.2 Web (Three.js + MMDLoader)

Three.js 0.160.0 with MMD extension:
- PMX model loading in browser
- Morph target animation
- Skeletal animation
- WebGL 2.0 acceleration
- Shadow maps + PBR lighting

### 4.3 Emotion to Morph Mapping

```
joy      -> smile(0.8) blink(0.2)
sadness  -> sorrow(0.8) brow_down(0.5)
anger    -> anger(0.8) brow_up(0.4)
surprise -> surprise(0.8) mouth_open(0.6)
fear     -> fear(0.7)
disgust  -> disgust(0.6)
neutral  -> (idle breathing + auto blink)
```

---

## Chapter 5: Tauri Desktop Client

### 5.1 Technology Choice

Tauri advantages over Electron:
- Install size: 3-10MB vs 150-300MB
- RAM: 50-100MB vs 200-500MB
- Startup: <1s vs 2-5s
- Language: Rust + TypeScript

### 5.2 Project Structure

```
laap-tauri/
  src-tauri/
    Cargo.toml
    src/main.rs
    src/commands.rs
    src/websocket.rs
    src/tray.rs
  src/
    App.tsx
    components/
      Avatar3D.tsx
      ChatPanel.tsx
      StatusBar.tsx
      EmotionDisplay.tsx
      ModelUploader.tsx
    hooks/
      useWebSocket.ts
    styles/theme.css
  package.json
```

### 5.3 Layout

```
+--------------------------------------------------------------+
| Title Bar: LAAP Virtual Character            [Settings][X]  |
+----------------------------+-------------------------------+
| Left: 3D Avatar Panel     | Right: Chat Panel             |
|  Three.js Scene           |  User messages                |
|  PMX Model                |  Agent streaming response     |
|  Emotion morph animation  |  Tool call logs               |
|  Idle breathing + blink   |  Screenshot preview           |
+----------------------------+-------------------------------+
| Status: joy(73%) Energy:80% Focus:60% Mood:90%            |
+--------------------------------------------------------------+
| [Type a message...                          ] [Send] [Mic] |
+--------------------------------------------------------------+
```

### 5.4 Rust Backend Commands

```rust
#[tauri::command]
async fn connect_to_laap(url: String) -> Result<String, String>

#[tauri::command]
async fn start_laap_backend() -> Result<(), String>

#[tauri::command]
async fn capture_screen() -> Result<String, String>

#[tauri::command]
async fn open_file_dialog() -> Result<String, String>

#[tauri::command]
async fn minimize_to_tray() -> Result<(), String>
```

---

## Chapter 6: Web Browser Client

### 6.1 Current Status

| Feature | Implementation | Status |
|---------|---------------|--------|
| Three.js scene | Index.html | Done |
| MMD model loading | MMDLoader | Done |
| Emotion morphs | JS morph control | Done |
| Chat panel | HTML+CSS | Done |
| Token streaming | WebSocket events | Done |
| Tool call display | Formatted messages | Done |
| Screenshot | Base64 image embed | Done |
| VMD animation | Pending | To-do |
| Lipsync | Pending | To-do |
| Model upload | File dialog | Done |

---

## Chapter 7: ESP32 Hardware

### 7.1 Hardware Bill of Materials

| Component | Model | Cost |
|-----------|-------|------|
| MCU | ESP32-S3-DevKitC-1 | $8 |
| Microphone | INMP441 I2S MEMS | $2 |
| Amplifier | MAX98357 I2S Class-D | $3 |
| Speaker | 3W 4ohm 40mm | $2 |
| Display | 1.3in OLED SH1106 I2C | $4 |
| LEDs | WS2812B x8 | $2 |
| Buttons | Tactile switch x3 | $1 |
| Battery | 18650 + holder | $5 |
| Total | | ~$27 |

### 7.2 Firmware Architecture

```
ESP32 Firmware (Arduino/C++)

setup():
  - WiFi.begin(ssid, pass)
  - MQTT.connect(broker)
  - I2S.begin(mic)
  - I2S.begin(speaker)
  - OLED.begin()
  - LED.setup()

loop():
  - Read mic -> encode Opus -> MQTT publish
  - MQTT subscribe -> decode Opus -> play speaker
  - Check VAD -> wake word detection
  - Update OLED display
  - Update LED strip
  - Read buttons -> handle actions
  - Deep sleep when idle (>30s no activity)
```

---

## Chapter 8: Voice Pipeline

### 8.1 TTS Pipeline

```
Agent response text
  -> TTS selection:
    Edge TTS (online, high quality)
    GPT-SoVITS (local, custom timbre)
    Piper-TTS (offline, 100ms latency)
  -> Opus encode (24kHz, 48kbps)
  -> MQTT topic: laap/server/tts/audio
  -> Client: 
    Desktop -> system audio output
    Web -> Web Audio API
    ESP32 -> I2S DAC -> MAX98357 -> speaker
```

### 8.2 ASR Pipeline

```
ESP32 mic -> INMP441 (I2S, 16kHz, 16bit)
  -> Opus encode (16kHz, 32kbps)
  -> MQTT topic: laap/esp32/asr/audio
  -> xiaozhi ASR engine:
    SenseVoice (local, high accuracy CN)
    Whisper.cpp (local, multilingual)
    Deepgram (online, <300ms)
  -> Text -> LifeformAgent.chat()
```

### 8.3 Lipsync

```python
class LipSyncEngine:
    def compute_mouth(self, audio_chunk):
        samples = np.frombuffer(audio_chunk, dtype=np.int16)
        rms = np.sqrt(np.mean(samples.astype(float)**2))
        mouth = np.clip(rms / 5000, 0, 1)
        return smooth(self.prev, mouth, 0.3)

    # mouth 0.0 -> closed
    # mouth 0.3 -> normal speech
    # mouth 0.7 -> loud/excited
```

---

## Chapter 9: Development Roadmap

### Phase 1: Core Integration (Week 1-2)

- [x] LAAP DigitalLifeform core
- [x] Emotion system (14 emotions)
- [x] 51 tools (GUI/browser/file)
- [x] 3D rendering (mmdpy + Three.js)
- [x] AvatarBridge IPC
- [ ] Fix Web avatar_server.py port issue
- [ ] Tauri project scaffold

### Phase 2: Voice + Hardware (Week 3-5)

- [ ] xiaozhi TTS integration -> VoiceBridge
- [ ] xiaozhi ASR integration -> AudioBridge
- [ ] LipSync engine
- [ ] ESP32 firmware v1
- [ ] MQTT bridge service

### Phase 3: Full Clients (Week 6-9)

- [ ] Tauri desktop client v1
- [ ] Three.js VMD motion playback
- [ ] Model upload + switch UI
- [ ] Web client responsive design

### Phase 4: Production (Week 10+)

- [ ] Performance optimization
- [ ] Installer packaging (Tauri bundle)
- [ ] Auto-update system
- [ ] User documentation + API reference

---

## Chapter 10: WebSocket Protocol

### Client -> Server

```
{"type":"chat","text":"Hello"}
{"type":"command","cmd":"screenshot"}
{"type":"load_model","path":"model.pmx"}
{"type":"audio_stream","data":"<base64>"}
```

### Server -> Client

```
{"type":"token","text":"Hello"}
{"type":"response","text":"Hello world!"}
{"type":"emotion","name":"joy","intensity":0.7}
{"type":"vitals","energy":0.85,"focus":0.72}
{"type":"tool_call","name":"web_fetch"}
{"type":"screenshot","data_base64":"<png>"}
{"type":"morph","name":"smile","value":0.8}
{"type":"system","text":"Ready"}
{"type":"error","message":"Error details"}
```

---

## Summary

The LAAP Virtual Character Engine integrates three complete subsystems:

1. **Digital Lifeform** (LAAP) - Cognition, emotion, memory, tools
2. **3D Rendering** (mmdpy/Three.js) - PMX model with morphs + VMD
3. **Voice + Hardware** (xiaozhi/ESP32) - TTS, ASR, sensors, IOT

All connected through AvatarBridge IPC bus supporting WebSocket,
multiprocessing Queue, and MQTT protocols. Three client types
serve different use cases: Tauri for desktop power, Web for zero-install
access, ESP32 for portable hardware interaction.
