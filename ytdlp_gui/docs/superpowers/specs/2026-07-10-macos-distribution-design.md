# macOS 공유용 배포물 설계

## 목표

Apple Silicon Mac 사용자가 `ytdlp-gui`를 열 때 현재 발생하는 “손상되었기 때문에 열 수 없습니다” 오류를 제거한다. Apple Developer Program 계정 없이 배포하므로 Gatekeeper의 최초 실행 허용 절차는 남는다.

## 배경 및 원인

기존 `ytdlp-gui-mac.pkg`의 payload에는 `._*` AppleDouble 부가 파일이 142개 포함되어 있다. 패키지에서 추출한 앱은 `codesign --verify --deep --strict`에서 `a sealed resource is missing or invalid`로 실패한다. `pkgbuild`와 `productbuild`는 macOS 15의 `com.apple.provenance` 메타데이터를 같은 방식으로 payload에 포함하므로, 둘 다 이 배포물에 사용할 수 없다. 반면 `ditto`로 만든 ZIP을 해제한 앱은 동일 검사에 통과한다.

## 범위

- PyInstaller 앱을 새로 빌드한다.
- 앱 번들의 확장 속성과 `._*` 파일을 제거한다.
- 정리된 앱을 ad-hoc 서명한다.
- Finder에서 해제할 `.zip` 배포물을 만든다.
- 새 ZIP을 임시 위치에 풀어 앱의 코드 서명 무결성을 검사한다.
- 검증을 통과한 경우에만 최종 `.zip`을 남긴다.
- 친구에게 전달할 최초 실행 안내를 문서화한다.

## 제외 범위

- Developer ID 서명, Apple 공증(notarization), 자동 업데이트는 포함하지 않는다. 이 기능들은 유료 Apple Developer Program 계정과 인증서가 필요하다.
- Intel Mac 및 universal binary 지원은 포함하지 않는다. 이번 배포물은 Apple Silicon(`arm64`) 대상이다.

## 구성

`scripts/build_macos.sh`는 배포 작업의 단일 진입점이다.

1. 기존 PyInstaller 산출물 디렉터리를 정리하고 `build.spec`로 앱을 빌드한다.
2. 생성한 `dist/ytdlp-gui.app`에서 확장 속성과 `._*` 파일을 제거한다.
3. `codesign --force --deep --sign -`으로 앱을 ad-hoc 서명하고 엄격한 무결성 검사를 실행한다.
4. `ditto`로 `dist/ytdlp-gui-mac.zip`을 생성한다.
5. ZIP을 임시 디렉터리에 해제하고 내부 앱에 다시 `codesign --verify --deep --strict`를 실행한다.
6. 모든 검증이 성공하면 `.zip`의 SHA-256 체크섬을 출력한다. 실패하면 오류와 함께 종료한다.

빌드 과정은 임시 검사 파일을 시스템 임시 디렉터리에만 만들며, 앱·패키지 산출물은 프로젝트의 `dist/` 아래에 둔다.

## 오류 처리

- `ffmpeg`, `pyinstaller`, `ditto`, `codesign` 중 하나라도 없으면 원인을 알리는 오류와 함께 종료한다.
- `build.spec`에 지정된 `ffmpeg` 경로가 없으면 빌드를 시작하지 않는다.
- 코드 서명 검증 또는 ZIP 재검증 실패 시 성공한 배포물로 오인되지 않도록 새 `.zip`을 삭제하고 실패로 종료한다.

## 검증 기준

- ZIP에서 해제한 앱에서 `._*`와 `.__*` 파일 수가 0이다.
- ZIP에서 해제한 앱이 `codesign --verify --deep --strict`를 통과한다.
- 기존 Python 테스트 스위트가 통과한다.

## 사용자 안내

정식 공증 전까지 친구는 `.zip`을 해제한 뒤 앱을 응용 프로그램 폴더로 옮기고 Finder에서 한 번 우클릭해 **열기**를 선택해야 한다. 터미널 명령이나 시스템 전역 보안 설정 변경은 안내하지 않는다.
