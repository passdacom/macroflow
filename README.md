# MacroFlow

MacroFlow는 Windows에서 마우스·키보드 동작을 녹화하고 재생하는 데스크톱 자동화 도구입니다.

## 다운로드

공식 GitHub Release의 `MacroFlow-*-GPL.zip`을 받으십시오. ZIP에는 실행 파일, 대응 소스 안내, SPDX SBOM, 제3자 고지 및 라이선스 원문이 함께 들어 있습니다. EXE를 별도로 재배포할 수도 있지만, 이 경우 재배포자가 GPLv3 제6조와 모든 제3자 고지·소스 제공 의무를 독립적으로 충족해야 합니다. 전체 GPL ZIP을 그대로 재배포하는 것이 가장 간단한 준수 방법입니다.

## 빌드 및 개발

요구사항과 재현 가능한 명령은 [BUILDING.md](BUILDING.md)를 참고하십시오.

## 보안

MacroFlow는 low-level keyboard/mouse hook과 `SendInput`을 사용합니다. 신뢰할 수 없는 매크로 파일을 실행하지 말고, 비밀번호 등 민감한 입력을 녹화하지 마십시오. 상세 내용은 [SECURITY.md](SECURITY.md)를 참고하십시오.

## 라이선스

MacroFlow는 **GNU General Public License v3.0**에 따라 배포되는 자유 소프트웨어입니다. 사용자는 GPLv3 조건에 따라 실행·연구·수정·복제·재배포할 수 있습니다.

이 프로그램은 어떠한 보증도 없이 제공됩니다. 전체 조건은 [LICENSE](LICENSE)를 참고하십시오. 번들되는 제3자 구성요소와 각 조건은 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)에 정리되어 있습니다.
