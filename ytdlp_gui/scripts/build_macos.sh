#!/usr/bin/env bash
set -euo pipefail

cleanup_build() {
  local exit_status=$?

  rm -rf "${CLEANUP_INSPECTION_DIR:-}"
  if [[ "${BUILD_SUCCEEDED:-0}" -ne 1 && -n "${CLEANUP_ARTIFACT_PATH:-}" ]]; then
    rm -f "$CLEANUP_ARTIFACT_PATH"
  fi

  return "$exit_status"
}

verify_extracted_app() {
  local app_path="$1"

  if find "$app_path" \( -name '._*' -o -name '.__*' \) -print -quit | grep -q .; then
    echo "AppleDouble file found in extracted app: $app_path" >&2
    return 1
  fi

  codesign --verify --deep --strict "$app_path"
}

verify_zip_archive() {
  local archive_path="$1"
  local inspection_dir
  local extracted_app

  inspection_dir="$(mktemp -d)"
  if ! ditto -x -k "$archive_path" "$inspection_dir"; then
    rm -rf "$inspection_dir"
    return 1
  fi

  extracted_app="$inspection_dir/ytdlp-gui.app"
  if [[ ! -d "$extracted_app" ]]; then
    echo "Expected ytdlp-gui.app in archive: $archive_path" >&2
    rm -rf "$inspection_dir"
    return 1
  fi

  if ! verify_extracted_app "$extracted_app"; then
    rm -rf "$inspection_dir"
    return 1
  fi

  rm -rf "$inspection_dir"
}

sanitize_app() {
  local app_path="$1"

  xattr -cr "$app_path"
  find "$app_path" \( -name '._*' -o -name '.__*' \) -delete
}

require_command() {
  local command_name="$1"

  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Required command is unavailable: $command_name" >&2
    exit 1
  }
}

resolve_pyinstaller() {
  if command -v pyinstaller >/dev/null 2>&1; then
    command -v pyinstaller
    return
  fi

  if [[ -x /opt/miniconda3/bin/pyinstaller ]]; then
    printf '%s\n' /opt/miniconda3/bin/pyinstaller
    return
  fi

  echo 'Required command is unavailable: pyinstaller' >&2
  exit 1
}

main() {
  local project_root
  local build_dir
  local dist_dir
  local app_path
  local archive_path
  local inspection_dir
  local pyinstaller_bin

  project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  build_dir="$project_root/build"
  dist_dir="$project_root/dist"
  app_path="$dist_dir/ytdlp-gui.app"
  archive_path="$dist_dir/ytdlp-gui-mac.zip"
  inspection_dir="$(mktemp -d)"
  pyinstaller_bin="$(resolve_pyinstaller)"

  CLEANUP_INSPECTION_DIR="$inspection_dir"
  CLEANUP_ARTIFACT_PATH="$archive_path"
  BUILD_SUCCEEDED=0
  trap cleanup_build EXIT

  require_command codesign
  require_command ditto
  require_command shasum
  [[ -x /opt/homebrew/bin/ffmpeg ]] || {
    echo 'Required executable is unavailable: /opt/homebrew/bin/ffmpeg' >&2
    exit 1
  }

  rm -rf "$build_dir" "$dist_dir/ytdlp-gui" "$app_path"
  rm -f "$archive_path"

  "$pyinstaller_bin" --noconfirm "$project_root/build.spec"
  sanitize_app "$app_path"
  codesign --force --deep --sign - "$app_path"
  codesign --verify --deep --strict "$app_path"

  ditto -c -k --sequesterRsrc --keepParent "$app_path" "$archive_path"
  verify_zip_archive "$archive_path"

  BUILD_SUCCEEDED=1
  shasum -a 256 "$archive_path"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
