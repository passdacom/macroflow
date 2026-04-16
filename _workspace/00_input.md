# 코드 리뷰 입력 정보

## 대상 프로젝트
- **이름**: MacroFlow
- **버전**: v0.2.5
- **언어**: Python 3.11+
- **프레임워크**: PyQt6 6.6+, ctypes Win32 LL Hook, PyInstaller 6.x
- **목적**: Windows 전용 마우스·키보드 매크로 녹화/재생 데스크톱 앱 (단일 .exe 배포)

## 대상 파일 (전체 소스)
```
src/macroflow/
├── __init__.py
├── main.py
├── types.py
├── recorder.py        ← Win32 LL Hook 기반 이벤트 캡처
├── player.py          ← SendInput 기반 재생 엔진
├── macro_file.py      ← JSON 직렬화/역직렬화
├── script_engine.py   ← 조건 분기·변수 처리
├── ui/
│   ├── main_window.py
│   ├── editor.py
│   ├── sequencer.py
│   └── favorites.py   ← 최근 신규 추가
└── win32/
    ├── hooks.py        ← WH_KEYBOARD_LL, WH_MOUSE_LL ctypes 래퍼
    ├── sendinput.py    ← SendInput ctypes 래퍼
    └── dpi.py          ← DPI 스케일링 처리
```

## 리뷰 범위
**풀 리뷰** — 스타일, 보안, 성능, 아키텍처 전 영역

## 컨텍스트
- 최근 세션에서 구현한 기능:
  1. 즐겨찾기 탭 (`ui/favorites.py` 신규)
  2. OEM 특수문자·키패드 VK 코드 매핑 확장 (`recorder.py`, `editor.py`)
  3. 이전 매크로 복원 기능 (`ui/main_window.py`)
  4. 색 체크 삽입 타임스탬프 오류 수정 (`ui/editor.py`)
  5. 색/창 트리거 이후 급속 재생 방지 (`player.py`)
  6. 딜레이 음수 입력 지원 + 이벤트 순서 역전 방지 (`player.py`, `ui/editor.py`)

## 스타일 가이드
- Python: PEP 8 + Google Python Style
- 타입 힌트 필수 (모든 함수 시그니처)
- Docstring 필수 (Google style, public 클래스·함수)
- ruff + mypy strict 통과 필수

## 핵심 설계 원칙 (core-beliefs.md)
1. 클릭/드래그 판별은 재생 시점에 (녹화 시 raw 저장)
2. Win32 LL Hook 단일 메시지 펌프 (pynput 금지)
3. 절대 타임스탬프 기준 재생 (time.sleep 누적 금지)
4. DPI-aware 좌표 비율 정규화
5. SendInput 직접 호출

## 경로 정보
- 소스 루트: `/root/.openclaw/workspace/macroflow/src/macroflow/`
- CLAUDE.md: `/root/.openclaw/workspace/macroflow/CLAUDE.md`
