# MacroFlow

MacroFlow는 Windows에서 마우스·키보드 동작을 녹화하고 재생하는 데스크톱 자동화 도구입니다.

## 다운로드

공식 GitHub Release의 `MacroFlow-*-GPL.zip`을 받으십시오. ZIP에는 실행 파일, 대응 소스 안내, SPDX SBOM, 제3자 고지 및 라이선스 원문이 함께 들어 있습니다. 같은 Release에는 정확한 MacroFlow·PyQt6·PyQt6-sip·Qt Base·Qt SVG·Qt Image Formats·CPython·OpenSSL·libffi·bzip2·XZ Utils·PyInstaller·빌드 도구 소스 archive와 각 SHA-256 sidecar도 게시됩니다. EXE를 별도로 재배포할 수도 있지만, 이 경우 재배포자가 GPLv3 제6조와 모든 제3자 고지·소스 제공 의무를 독립적으로 충족해야 합니다. 전체 GPL ZIP과 companion source asset을 함께 재배포하는 것이 가장 간단한 준수 방법입니다.

## 빠른 실행 슬롯

네 번째 `빠른 실행` 탭에서 자주 사용하는 매크로를 5개 슬롯에 연결할 수 있습니다. 각 슬롯은 이름, 매크로 JSON 파일, 글로벌 단축키를 기억하며 기본 단축키는 `Ctrl+Alt+1`부터 `Ctrl+Alt+5`까지입니다.

1. 슬롯에서 `매크로 선택...`으로 파일을 연결합니다.
2. 필요한 경우 슬롯 이름과 단축키를 변경합니다.
3. `빠른 실행 설정 적용`을 누릅니다.
4. 프로그램이 대기 중일 때 슬롯 단축키를 누르면 해당 매크로를 최신 파일 내용으로 한 번만 실행합니다.

슬롯 실행은 현재 매크로 에디터의 파일과 편집 상태를 바꾸지 않으며 다음 슬롯을 자동 실행하지 않습니다. 매크로 실행 사이의 사용자 확인·선택이 끝난 뒤 다음 단축키를 직접 누르십시오. 녹화·일반 재생·시퀀스 실행 중의 추가 슬롯 호출은 대기열에 쌓이지 않고 거부됩니다. 슬롯 단축키는 `설정 → 단축키 설정...`에서도 변경할 수 있고, `ESC`를 빠르게 세 번 누르는 긴급 중지는 슬롯 재생에도 동일하게 적용됩니다.

## 빌드 및 개발

요구사항과 재현 가능한 명령은 [BUILDING.md](BUILDING.md)를 참고하십시오.

## 보안

MacroFlow는 low-level keyboard/mouse hook과 `SendInput`을 사용합니다. 신뢰할 수 없는 매크로 파일을 실행하지 말고, 비밀번호 등 민감한 입력을 녹화하지 마십시오. 상세 내용은 [SECURITY.md](SECURITY.md)를 참고하십시오.

## 라이선스

MacroFlow는 **GNU General Public License v3.0**에 따라 배포되는 자유 소프트웨어입니다. 사용자는 GPLv3 조건에 따라 실행·연구·수정·복제·재배포할 수 있습니다.

개인 및 기업의 업무·상업적 사용이 가능합니다. 바이너리 또는 수정본을 외부에 배포하는 경우 수령자에게 해당 바이너리의 전체 대응 소스를 제공하고 GPLv3 권리를 제한하지 않아야 합니다.

이 프로그램은 어떠한 보증도 없이 제공됩니다. 전체 조건은 [LICENSE](LICENSE)를 참고하십시오. 번들되는 제3자 구성요소와 각 조건은 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)에 정리되어 있습니다.
