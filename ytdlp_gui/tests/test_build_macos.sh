#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo_root/scripts/build_macos.sh"

fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT

mkdir -p "$fixture/ytdlp-gui.app/Contents/MacOS"
printf '#!/bin/sh\nexit 0\n' > "$fixture/ytdlp-gui.app/Contents/MacOS/ytdlp-gui"
chmod +x "$fixture/ytdlp-gui.app/Contents/MacOS/ytdlp-gui"
codesign --force --deep --sign - "$fixture/ytdlp-gui.app"

verify_extracted_app "$fixture/ytdlp-gui.app"

archive="$fixture/ytdlp-gui-mac.zip"
ditto -c -k --sequesterRsrc --keepParent "$fixture/ytdlp-gui.app" "$archive"
verify_zip_archive "$archive"

touch "$fixture/ytdlp-gui.app/Contents/._MacOS"
if verify_extracted_app "$fixture/ytdlp-gui.app"; then
  echo 'expected AppleDouble payload to be rejected' >&2
  exit 1
fi

mkdir -p "$fixture/Dirty.app/Contents/MacOS"
touch "$fixture/Dirty.app/Contents/._MacOS"
sanitize_app "$fixture/Dirty.app"
if find "$fixture/Dirty.app" \( -name '._*' -o -name '.__*' \) -print -quit | grep -q .; then
  echo 'expected sanitize_app to remove AppleDouble files' >&2
  exit 1
fi

archive_fixture="$fixture/failed-build.zip"
touch "$archive_fixture"
CLEANUP_INSPECTION_DIR="$fixture/inspection"
CLEANUP_ARTIFACT_PATH="$archive_fixture"
BUILD_SUCCEEDED=0
cleanup_build
[[ ! -e "$archive_fixture" ]] || {
  echo 'expected cleanup_build to remove an unverified archive' >&2
  exit 1
}

for text in 'Apple Silicon' '우클릭' '열기'; do
  grep -q "$text" "$repo_root/docs/MACOS_INSTALL.md" || {
    echo "missing install guidance: $text" >&2
    exit 1
  }
done

grep -q "(FFPROBE, '.')" "$repo_root/build.spec" || {
  echo 'build.spec must bundle ffprobe alongside ffmpeg' >&2
  exit 1
}
