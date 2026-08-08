# LAAP-Mobile iOS 构建与打包指南

> 本指南适用于在 **macOS** 上把 LAAP-Mobile 源码打包成 `.ipa` 或上传到 App Store Connect / TestFlight。Windows 无法完成 iOS 签名与归档，因此必须在 macOS 上操作。

---

## 一、环境要求

| 项目 | 最低要求 | 说明 |
|---|---|---|
| 操作系统 | macOS 14 (Sonoma) | 推荐 macOS 15+ |
| Xcode | Xcode 16+ | 工程 `LastUpgradeVersion = 2620`，对应 Xcode 16 |
| 命令行工具 | `xcodebuild`、`xcrun` | 安装 Xcode 后通常已包含 |
| 账号 | Apple Developer（个人/公司/企业） | 用于签名、生成 Provisioning Profile |
| 可选 | Transporter.app | 上传 App Store Connect 推荐方式 |
| 可选 | git-lfs | 如果仓库把大资源文件放在 LFS 中 |

### 1.1 检查 Xcode 版本

```bash
xcodebuild -version
# 应输出类似：Xcode 16.0 Build version 16A242d
```

### 1.2 确认命令行工具路径

```bash
xcode-select -p
# 应指向 /Applications/Xcode.app/Contents/Developer
```

如果指向 `/Library/Developer/CommandLineTools`，请切换：

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

---

## 二、首次准备

### 2.1 拉取源码

```bash
git clone https://github.com/lorryjovens-hub/LAAP-Mobile.git
cd LAAP-Mobile
```

### 2.2 安装依赖（可选）

本项目为纯 Swift/Xcode 工程，无 CocoaPods / Swift Package Manager 外部依赖。如果有 git-lfs 资源：

```bash
git lfs pull
```

### 2.3 确认 bundle ID

已统一为 LAAP 品牌：

- 主 App: `org.laap.mobile`
- Share Extension: `org.laap.mobile.ShareExtension`
- File Provider: `org.laap.mobile.FileProvider`
- AgentWidget: `org.laap.mobile.AgentWidget`
- Tests: `org.laap.mobile.Tests`
- UI Tests: `org.laap.mobile.UITests`

可在 `src/ios/Minis.xcodeproj/project.pbxproj` 中搜索 `PRODUCT_BUNDLE_IDENTIFIER` 复核。

---

## 三、自动化脚本构建（推荐）

已提供脚本：`scripts/build_ios.sh`

### 3.1 开发版 IPA（安装到已注册设备）

```bash
cd LAAP-Mobile
./scripts/build_ios.sh \
  --team YOUR_TEAM_ID \
  --method development \
  --output ./build/ios
```

### 3.2 Ad-Hoc 分发版

```bash
./scripts/build_ios.sh \
  --team YOUR_TEAM_ID \
  --method ad-hoc \
  --output ./build/ios
```

### 3.3 App Store Connect / TestFlight 版

```bash
./scripts/build_ios.sh \
  --team YOUR_TEAM_ID \
  --method app-store-connect \
  --output ./build/ios \
  --upload
```

> `--upload` 会尝试用 `xcrun altool` 上传；若 Xcode 版本已移除该工具，脚本会提示改用 Transporter.app 手动上传。

### 3.4 参数说明

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-t, --team` | Apple Team ID（10 位） | 自动签名 |
| `-m, --method` | `development` / `ad-hoc` / `app-store-connect` | `development` |
| `-o, --output` | 输出目录 | `./build/ios` |
| `-c, --clean` | 构建前 clean | false |
| `-u, --upload` | 构建后上传 App Store | false |
| `--debug` | 使用 Debug 配置 | Release |

### 3.5 输出产物

```
build/ios/
├── LAAP-Mobile.xcarchive      # 归档包
├── ExportOptions_*.plist      # 导出配置
└── LAAP-Mobile.ipa            # 最终安装包（名称取决于 Xcode 导出）
```

---

## 四、手动打包步骤

如果不想用脚本，可按以下步骤手动操作。

### 4.1 清理并归档

```bash
cd LAAP-Mobile/src/ios

xcodebuild -project Minis.xcodeproj \
  -scheme Minis \
  -configuration Release \
  -archivePath ../../build/ios/LAAP-Mobile.xcarchive \
  -destination "generic/platform=iOS" \
  DEVELOPMENT_TEAM=YOUR_TEAM_ID \
  -allowProvisioningUpdates \
  archive
```

> 第一次运行时，`-allowProvisioningUpdates` 会让 Xcode 自动在 Apple Developer 后台创建 App ID 和 Provisioning Profile。请确保登录了正确的 Apple ID（Xcode → Settings → Accounts）。

### 4.2 导出 IPA

创建 `ExportOptions.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>development</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>stripSwiftSymbols</key>
    <true/>
    <key>thinning</key>
    <string>&lt;none&gt;</string>
    <key>compileBitcode</key>
    <false/>
    <key>uploadSymbols</key>
    <true/>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>manageAppVersionAndBuildNumber</key>
    <true/>
</dict>
</plist>
```

然后导出：

```bash
xcodebuild -exportArchive \
  -archivePath ../../build/ios/LAAP-Mobile.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath ../../build/ios
```

---

## 五、签名与证书常见问题

### 5.1 自动签名失败

若出现 `No signing certificate "iOS Development" found`：

1. Xcode → Settings → Accounts → 添加 Apple ID
2. 点击 Download Manual Profiles
3. 在 target 的 Signing & Capabilities 中勾选 "Automatically manage signing"
4. 重新运行脚本

### 5.2 Bundle ID 已被占用

如果提示 `The app ID "org.laap.mobile" cannot be registered to your development team`：

- 说明该 bundle ID 已被其他开发者账号注册。
- 检查当前登录的 Apple ID 是否正确。
- 或临时改为 `org.laap.mobile.debug` 等变体进行测试。

### 5.3 App Groups / iCloud 容器未启用

LAAP 需要以下能力（已配置在 entitlements 中）：

- App Groups: `group.org.laap.mobile`
- iCloud: `iCloud.org.laap.mobile`

首次自动签名时，Xcode 会尝试在 Apple Developer 后台创建这些容器。如果失败，请手动登录 [developer.apple.com](https://developer.apple.com) 创建同名 App Group 与 iCloud Container。

### 5.4 导出时提示 "Provisioning profile doesn't include"

通常是因为设备未注册到开发账号。开发版需要把测试设备的 UDID 加入 [Devices](https://developer.apple.com/account/resources/devices/list)。

---

## 六、安装到设备

### 6.1 通过 Xcode

1. 连接 iPhone
2. Xcode → Window → Devices and Simulators
3. 把 `LAAP-Mobile.ipa` 拖到设备上

### 6.2 通过 Apple Configurator 2

适合批量安装 Ad-Hoc 包。

### 6.3 通过 TestFlight

使用 `--method app-store-connect --upload` 上传后，在 TestFlight 中添加内部测试员即可分发。

---

## 七、上传 App Store Connect

### 7.1 使用 Transporter.app（推荐）

1. 从 Mac App Store 安装 [Transporter](https://apps.apple.com/us/app/transporter/id1450874784)
2. 登录 Apple ID
3. 拖入 `build/ios/*.ipa`
4. 点击交付

### 7.2 使用命令行（旧版 Xcode）

```bash
xcrun altool --upload-app \
  --type ios \
  --file build/ios/LAAP-Mobile.ipa \
  --team-id YOUR_TEAM_ID
```

---

## 八、后续维护

- 每次版本更新前，修改 `src/ios/Info.plist` 中的 `CFBundleShortVersionString` 和 `CFBundleVersion`。
- 脚本已设置 `manageAppVersionAndBuildNumber = true`，导出时会自动递增构建号。
- 如需支持 iOS 17+ 的新能力（如 Live Activity、Interactive Widget），保持 Xcode 为最新版本。

---

## 九、快速参考命令

```bash
# 1. 进入仓库
cd LAAP-Mobile

# 2. 开发版 IPA
./scripts/build_ios.sh --team YOUR_TEAM_ID --method development

# 3. TestFlight 版 IPA 并上传
./scripts/build_ios.sh --team YOUR_TEAM_ID --method app-store-connect --upload

# 4. 清理构建缓存后打包
./scripts/build_ios.sh --team YOUR_TEAM_ID --method app-store-connect --clean
```

---

## 十、备注

- 工程文件、Scheme 和目标名目前仍沿用原始 OpenMinis 的 `Minis` 内部标识（如 `Minis.xcodeproj`、`Minis` target）。这不会影响打包和用户看到的 App 名称；用户可见名称由 `Info.plist` 的 `CFBundleDisplayName` 控制，已设为 **LAAP**。
- 如需彻底重命名 Xcode target 和产物，请在 Xcode 中手动重命名 Target、Scheme 和 Test bundles，并同步修改所有引用。此操作有破坏工程索引的风险，建议在独立分支进行。
