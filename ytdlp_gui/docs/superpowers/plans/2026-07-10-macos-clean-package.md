# macOS Clean ZIP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an Apple Silicon macOS `.zip` whose extracted app passes strict code-signature verification and contains no AppleDouble files.

**Architecture:** A Bash entry point builds the existing PyInstaller spec, signs the app, creates a Finder-compatible ZIP, then extracts and validates the archive. A Bash integration test creates a tiny signed fixture app and tests the helpers.

**Tech Stack:** Bash, PyInstaller, macOS `codesign`, `ditto`, `shasum`, `pytest`.

## Global Constraints

- Target Apple Silicon (`arm64`) macOS only.
- Use ad-hoc signing (`codesign --sign -`); Developer ID signing and notarization are excluded.
- A failed build or verification must not leave a newly generated `dist/ytdlp-gui-mac.zip` behind.
- ZIP verification must check for both `._*` and `.__*` files and run `codesign --verify --deep --strict` on the extracted app.
- Do not modify application runtime code.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `scripts/build_macos.sh` | Builds, ad-hoc signs, archives, and verifies the macOS app. |
| `tests/test_build_macos.sh` | Creates controlled archive fixtures and tests packaging helpers. |
| `docs/MACOS_INSTALL.md` | Explains Apple Silicon installation and one-time Finder approval. |

### Task 1: Add a testable archive verifier

**Files:**
- Create: `tests/test_build_macos.sh`
- Create: `scripts/build_macos.sh`

**Interfaces:**
- Produces: `verify_extracted_app APP_PATH` and `verify_zip_archive ARCHIVE_PATH`, which exit nonzero for AppleDouble files or failed strict signing verification.

- [ ] **Step 1: Write the failing test**

```bash
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo_root/scripts/build_macos.sh"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT
mkdir -p "$fixture/Clean.app/Contents/MacOS"
printf '#!/bin/sh\nexit 0\n' > "$fixture/Clean.app/Contents/MacOS/Clean"
chmod +x "$fixture/Clean.app/Contents/MacOS/Clean"
codesign --force --deep --sign - "$fixture/Clean.app"
verify_extracted_app "$fixture/Clean.app"
ditto -c -k --sequesterRsrc --keepParent "$fixture/ytdlp-gui.app" "$fixture/ytdlp-gui-mac.zip"
verify_zip_archive "$fixture/ytdlp-gui-mac.zip"
touch "$fixture/Clean.app/Contents/._MacOS"
if verify_extracted_app "$fixture/Clean.app"; then exit 1; fi
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `bash tests/test_build_macos.sh`

Expected: fail because `scripts/build_macos.sh` does not exist.

- [ ] **Step 3: Write the minimal implementation**

```bash
#!/usr/bin/env bash
set -euo pipefail
verify_extracted_app() {
  local app_path="$1"
  if find "$app_path" \( -name '._*' -o -name '.__*' \) -print -quit | grep -q .; then
    echo "AppleDouble file found in extracted app" >&2
    return 1
  fi
  codesign --verify --deep --strict "$app_path"
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `bash tests/test_build_macos.sh`

Expected: exit status 0; the clean archive passes and its AppleDouble fixture is rejected.

- [ ] **Step 5: Commit**

```bash
git add ytdlp_gui/scripts/build_macos.sh ytdlp_gui/tests/test_build_macos.sh
git commit -m "test: cover macOS archive verification"
```

### Task 2: Build, archive, and revalidate the app

**Files:**
- Modify: `scripts/build_macos.sh`
- Test: `tests/test_build_macos.sh`

**Interfaces:**
- Produces: final `dist/ytdlp-gui-mac.zip` only after archive validation succeeds.

- [ ] **Step 1: Extend the failing test**

```bash
mkdir -p "$fixture/Dirty.app/Contents/MacOS"
touch "$fixture/Dirty.app/Contents/._MacOS"
sanitize_app "$fixture/Dirty.app"
if find "$fixture/Dirty.app" \( -name '._*' -o -name '.__*' \) -print -quit | grep -q .; then exit 1; fi
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `bash tests/test_build_macos.sh`

Expected: fail with `sanitize_app: command not found`.

- [ ] **Step 3: Implement the build pipeline**

Under `if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then`, require PyInstaller, `codesign`, `ditto`, `shasum`, and `/opt/homebrew/bin/ffmpeg`; clear old build artifacts; run `pyinstaller --noconfirm build.spec`; ad-hoc sign `dist/ytdlp-gui.app`; run strict verification; archive the app with `ditto -c -k --sequesterRsrc --keepParent`; and call `verify_zip_archive` on the final ZIP. Delete the final archive on any validation failure and print its SHA-256 checksum only on success.

- [ ] **Step 4: Run the test to verify it passes**

Run: `bash tests/test_build_macos.sh`

Expected: exit status 0.

- [ ] **Step 5: Build and verify the distribution artifact**

Run: `bash scripts/build_macos.sh`

Expected: `dist/ytdlp-gui-mac.zip` exists, reports a SHA-256 checksum, and exits 0.

- [ ] **Step 6: Run all automated tests**

Run: `pytest -q && bash tests/test_build_macos.sh`

Expected: every Python test passes and the packaging integration test exits 0.

- [ ] **Step 7: Commit**

```bash
git add ytdlp_gui/scripts/build_macos.sh ytdlp_gui/tests/test_build_macos.sh
git commit -m "fix: produce verified macOS archive"
```

### Task 3: Document the supported installation path

**Files:**
- Create: `docs/MACOS_INSTALL.md`
- Test: `tests/test_build_macos.sh`

**Interfaces:**
- Produces: recipient-facing installation and first-run instructions.

- [ ] **Step 1: Write the failing documentation check**

```bash
for text in 'Apple Silicon' '우클릭' '열기'; do
  grep -q "$text" "$repo_root/docs/MACOS_INSTALL.md" || exit 1
done
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `bash tests/test_build_macos.sh`

Expected: fail because `docs/MACOS_INSTALL.md` does not exist.

- [ ] **Step 3: Write the installation guide**

```markdown
# ytdlp-gui 설치 방법 (macOS)

이 배포본은 Apple Silicon(M1/M2/M3/M4) Mac용입니다.

1. `ytdlp-gui-mac.zip`의 압축을 해제합니다.
2. `ytdlp-gui.app`을 Finder의 응용 프로그램 폴더로 옮깁니다.
3. 처음 한 번은 앱을 우클릭한 뒤 **열기**를 선택하고, 확인 창에서 다시 **열기**를 선택합니다.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `bash tests/test_build_macos.sh`

Expected: exit status 0.

- [ ] **Step 5: Commit**

```bash
git add ytdlp_gui/docs/MACOS_INSTALL.md ytdlp_gui/tests/test_build_macos.sh
git commit -m "docs: add macOS install guide"
```

## Plan Self-Review

- Spec coverage: Tasks 1–2 cover re-signing, ZIP generation, ZIP extraction, and strict verification. Task 3 covers first-run instructions. Developer ID signing and Intel support remain excluded.
- Placeholder scan: no deferred or ambiguous implementation actions remain.
- Interface consistency: `verify_extracted_app APP_PATH` and `sanitize_app APP_PATH` are defined before the build pipeline uses them; the same test script invokes both.
