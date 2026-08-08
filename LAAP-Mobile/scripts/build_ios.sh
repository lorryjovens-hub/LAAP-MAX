#!/usr/bin/env bash
set -euo pipefail

# LAAP-Mobile iOS automated build script for macOS.
# Usage:
#   cd LAAP-Mobile
#   ./scripts/build_ios.sh --team <TEAM_ID> --method development --output ./build/ios
#
# Supported --method values:
#   development       : signed .ipa for direct installation on registered devices
#   ad-hoc            : signed .ipa for OTA distribution to registered devices
#   app-store-connect : .ipa ready for App Store Connect / TestFlight upload
#
# Requirements:
#   - macOS 14+ (Sonoma or newer recommended)
#   - Xcode 16+ (the workspace LastUpgradeVersion is 2620)
#   - Apple Developer account
#   - git-lfs if assets are stored via LFS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IOS_DIR="${PROJECT_ROOT}/src/ios"
XCODE_PROJECT="${IOS_DIR}/Minis.xcodeproj"
SCHEME="Minis"

# Defaults
METHOD="development"
OUTPUT_DIR="${PROJECT_ROOT}/build/ios"
TEAM_ID=""
CONFIGURATION="Release"
CLEAN=0
UPLOAD=0

usage() {
  cat <<EOF
LAAP-Mobile iOS build script

Options:
  -h, --help                  Show this help
  -t, --team TEAM_ID          Apple Developer Team ID (10 characters)
  -m, --method METHOD         Export method: development | ad-hoc | app-store-connect (default: development)
  -o, --output DIR            Output directory (default: ./build/ios)
  -c, --clean                 Clean build folder before building
  -u, --upload                After app-store-connect export, upload the IPA with xcrun altool (deprecated) or Transporter
  --debug                     Use Debug configuration instead of Release

Examples:
  # Build a development IPA for local device install
  ./scripts/build_ios.sh --team ABCDEFGHIJ --method development

  # Build an App Store Connect IPA for TestFlight
  ./scripts/build_ios.sh --team ABCDEFGHIJ --method app-store-connect

EOF
}

log() { echo -e "\033[1;34m[LAAP-iOS]\033[0m $*"; }
warn() { echo -e "\033[1;33m[LAAP-iOS]\033[0m $*" >&2; }
error() { echo -e "\033[1;31m[LAAP-iOS]\033[0m $*" >&2; exit 1; }

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help) usage; exit 0 ;;
      -t|--team) TEAM_ID="$2"; shift 2 ;;
      -m|--method) METHOD="$2"; shift 2 ;;
      -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
      -c|--clean) CLEAN=1; shift ;;
      -u|--upload) UPLOAD=1; shift ;;
      --debug) CONFIGURATION="Debug"; shift ;;
      *) error "Unknown argument: $1" ;;
    esac
  done
}

validate() {
  command -v xcodebuild >/dev/null 2>&1 || error "xcodebuild not found. Install Xcode and run 'xcode-select --install' if needed."

  if [[ ! -d "${XCODE_PROJECT}" ]]; then
    error "Xcode project not found at ${XCODE_PROJECT}. Run this script from the repo root."
  fi

  if [[ -z "${TEAM_ID}" ]]; then
    warn "No --team provided. Automatic signing with -allowProvisioningUpdates will be used."
    warn "If you have multiple teams, pass --team <TEAM_ID> to avoid ambiguity."
  elif [[ ! "${TEAM_ID}" =~ ^[A-Z0-9]{10}$ ]]; then
    warn "Team ID '${TEAM_ID}' does not look like a 10-character Apple Team ID. Continuing anyway."
  fi

  case "${METHOD}" in
    development|ad-hoc|app-store-connect) ;;
    *) error "Unsupported export method: ${METHOD}" ;;
  esac
}

prepare_export_options() {
  local template="${SCRIPT_DIR}/ios_export_options.plist.template"
  if [[ ! -f "${template}" ]]; then
    error "Export options template not found: ${template}"
  fi

  mkdir -p "${OUTPUT_DIR}"
  local plist="${OUTPUT_DIR}/ExportOptions_${METHOD}.plist"

  cp "${template}" "${plist}"
  # Replace placeholders
  sed -i '' "s|__METHOD__|${METHOD}|g" "${plist}"
  sed -i '' "s|__TEAM_ID__|${TEAM_ID}|g" "${plist}"

  # app-store-connect requires uploadBitcode/uploadSymbols behavior depending on Xcode version
  if [[ "${METHOD}" == "app-store-connect" ]]; then
    /usr/libexec/PlistBuddy -c "Add :uploadBitcode bool false" "${plist}" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add :uploadSymbols bool true" "${plist}" 2>/dev/null || true
  fi

  echo "${plist}"
}

main() {
  parse_args "$@"
  validate

  log "Project root : ${PROJECT_ROOT}"
  log "iOS project  : ${XCODE_PROJECT}"
  log "Scheme       : ${SCHEME}"
  log "Configuration: ${CONFIGURATION}"
  log "Export method: ${METHOD}"
  log "Output dir   : ${OUTPUT_DIR}"

  mkdir -p "${OUTPUT_DIR}"

  local archive_path="${OUTPUT_DIR}/LAAP-Mobile.xcarchive"
  local clean_flag=""
  [[ "${CLEAN}" == "1" ]] && clean_flag="-scheme ${SCHEME} clean"

  # Optional: clean
  if [[ "${CLEAN}" == "1" ]]; then
    log "Cleaning build folder..."
    xcodebuild -project "${XCODE_PROJECT}" \
               -scheme "${SCHEME}" \
               -configuration "${CONFIGURATION}" \
               clean
  fi

  # Build archive
  log "Building archive (this may take several minutes)..."
  local team_args=()
  if [[ -n "${TEAM_ID}" ]]; then
    team_args=("DEVELOPMENT_TEAM=${TEAM_ID}")
  fi

  xcodebuild -project "${XCODE_PROJECT}" \
             -scheme "${SCHEME}" \
             -configuration "${CONFIGURATION}" \
             -archivePath "${archive_path}" \
             -destination "generic/platform=iOS" \
             "${team_args[@]}" \
             -allowProvisioningUpdates \
             archive

  log "Archive created: ${archive_path}"

  # Export IPA
  local export_options_plist
  export_options_plist="$(prepare_export_options)"

  log "Exporting IPA with method '${METHOD}'..."
  xcodebuild -exportArchive \
             -archivePath "${archive_path}" \
             -exportOptionsPlist "${export_options_plist}" \
             -exportPath "${OUTPUT_DIR}"

  # Locate IPA
  local ipa_path
  ipa_path="$(find "${OUTPUT_DIR}" -maxdepth 1 -name '*.ipa' -print -quit)"
  if [[ -z "${ipa_path}" ]]; then
    error "IPA not found in ${OUTPUT_DIR}"
  fi

  log "Build succeeded."
  log "IPA path: ${ipa_path}"

  # Optional App Store upload
  if [[ "${METHOD}" == "app-store-connect" && "${UPLOAD}" == "1" ]]; then
    log "Uploading to App Store Connect..."
    if command -v xcrun >/dev/null 2>&1 && xcrun altool --help >/dev/null 2>&1; then
      # Note: xcrun altool is deprecated in newer Xcode; prefer Transporter or xcrun altool --upload-app
      xcrun altool --upload-app --type ios --file "${ipa_path}" \
                   "${TEAM_ID:+--team-id ${TEAM_ID}}" || warn "Upload failed; use Transporter.app manually."
    else
      warn "xcrun altool not available. Install Transporter.app and upload ${ipa_path} manually."
    fi
  fi
}

main "$@"
