# CLAUDE.md — MacroFlow 에이전트 컨텍스트

> 이 파일은 Claude Code 에이전트가 매 세션 시작 시 가장 먼저 읽는 파일입니다.
> 코드 작성 전에 반드시 전체를 숙지하세요.

---

## 1. 프로젝트 한 줄 요약

**MacroFlow** — 마우스·키보드 동작을 녹화하고 재생하는 **Windows 전용** 데스크톱 매크로 앱.
팀 내부 배포 전용. 비기술자도 단일 `.exe` 실행만으로 사용 가능해야 한다.

---

## 2. 기술 스택

| 구분 | 선택 | 비고 |
|---|---|---|
| 언어 | Python 3.11+ | 3.10 이하 사용 금지 |
| 이벤트 캡처 | **ctypes + Win32 LL Hook** | pynput Listener 사용 금지 (이벤트 순서 보장 불가) |
| 이벤트 재생 | **ctypes + SendInput API** | pynput 재생 제어 사용 금지 |
| GUI | PyQt6 6.6+ | PyQt5 문법 사용 금지 |
| 빌드/배포 | PyInstaller 6.x (onefile) | Windows 단일 .exe 배포 |
| 테스트 | pytest 8.x + pytest-qt | |
| 코드 품질 | ruff + mypy | CI에서 강제 |
| 패키지 관리 | uv | pip 직접 사용 금지 |

> **왜 pynput 대신 ctypes 직접 호출인가?**
> pynput은 마우스·키보드를 별도 스레드로 처리하여 빠른 입력 시 이벤트 순서가
> 역전될 수 있다. Windows Low-Level Hook (WH_KEYBOARD_LL, WH_MOUSE_LL)을
> 단일 메시지 펌프 스레드에서 직접 처리하면 OS 레벨에서 순서가 보장된다.
> 재생도 SendInput을 직접 호출해야 키/마우스 이벤트가 원자적으로 처리된다.

---

## 3. 디렉토리 구조

```
macro-harness/
├── CLAUDE.md
├── ARCHITECTURE.md
├── SECURITY.md
├── pyproject.toml
├── src/
│   └── macroflow/
│       ├── __init__.py
│       ├── main.py
│       ├── recorder.py         ← LL Hook 기반 이벤트 캡처
│       ├── player.py           ← SendInput 기반 재생 엔진
│       ├── macro_file.py       ← JSON 직렬화/역직렬화
│       ├── script_engine.py    ← 조건 분기·변수 처리
│       ├── win32/
│       │   ├── hooks.py        ← WH_KEYBOARD_LL, WH_MOUSE_LL ctypes 래퍼
│       │   ├── sendinput.py    ← SendInput ctypes 래퍼
│       │   └── dpi.py          ← DPI 스케일링 처리
│       └── ui/
│           ├── main_window.py
│           ├── sequencer.py
│           └── editor.py
├── tests/
├── docs/
│   ├── design-docs/
│   │   ├── core-beliefs.md     ← ★ 설계 원칙 및 과거 실패 학습
│   │   └── index.md
│   ├── exec-plans/
│   │   ├── active/
│   │   │   └── mvp-phase1.md
│   │   ├── completed/
│   │   └── tech-debt-tracker.md
│   ├── generated/
│   │   └── macro-json-schema.md
│   ├── product-specs/
│   │   ├── json-format-spec.md
│   │   ├── macro-recorder.md
│   │   ├── macro-player.md
│   │   ├── scripting-engine.md
│   │   ├── drag-drop-sequencer.md
│   │   └── index.md
│   └── references/
│       ├── win32-hooks-llms.txt
│       └── pyqt6-llms.txt
└── build/
    └── macroflow-win.spec
```

---

## 4. 코딩 컨벤션

- Type hints 필수: 모든 함수 시그니처
- Docstring 필수: Google style, 모든 public 클래스·함수
- ruff 통과 필수: `uv run ruff check .`
- mypy strict: `uv run mypy src/` 오류 0건

네이밍: 클래스 PascalCase / 함수·변수 snake_case / 상수 UPPER_SNAKE_CASE

---

## 5. 핵심 커맨드

```bash
uv sync                                        # 환경 설치
uv run python -m macroflow                     # 앱 실행
uv run pytest tests/ -v                        # 테스트
uv run ruff check . && uv run mypy src/        # 품질 검사
uv run pyinstaller build/macroflow-win.spec    # Windows exe 빌드
```

---

## 6. 에이전트 행동 규칙

### 반드시 할 것
- 새 기능 시작 전 docs/product-specs/ 해당 스펙 파일 먼저 읽기
- docs/design-docs/core-beliefs.md 숙지 — 과거 실패 패턴 반복 금지
- JSON 포맷 변경 시 json-format-spec.md 먼저 업데이트
- Win32 API 호출은 src/macroflow/win32/ 하위에만 작성
- 테스트 없이 recorder.py / player.py / macro_file.py 변경 금지

### 절대 하지 말 것
- pynput Listener 사용 — 이벤트 순서 보장 불가
- pynput Controller 로 재생 — SendInput 사용할 것
- 녹화 시점에 클릭/드래그 분류 — RAW 이벤트 저장, 재생 시 판별
- time.sleep() 을 타이밍 기준으로 사용 — 절대 타임스탬프 기준 재생
- eval() / exec() 를 script_engine.py 샌드박스 외부에서 사용
- PyQt5 호환 문법 사용

---

## 7. 알려진 기술적 지뢰 (과거 실패에서 학습)

> 자세한 내용: docs/design-docs/core-beliefs.md

| 지뢰 | 증상 | 해결책 |
|---|---|---|
| pynput 멀티스레드 이벤트 역전 | 빠른 타이핑 시 순서 꼬임 | Win32 LL Hook 단일 메시지 펌프 |
| 녹화 시점 클릭/드래그 분류 | 클릭↔드래그 오인식 | RAW 저장 + 재생 시 임계값 판별 |
| time.sleep() 누적 오차 | 긴 매크로 타이밍 드리프트 | 절대 타임스탬프 기준 + 드리프트 보정 |
| DPI 스케일링 미처리 | 다른 PC에서 좌표 어긋남 | 좌표 비율 정규화 + DPI Aware 선언 |
| 미세 이동 중 클릭 | 클릭이 드래그로 오인식 | 거리 임계값 8px + 시간 임계값 300ms |

### ⚠️ mypy CI 반복 실패 패턴 (로컬 mypy 없음 → 서버 코드 작성 시 주의)

로컬에서 mypy를 실행할 수 없으므로 아래 규칙을 반드시 준수해야 CI 실패를 방지한다.

**규칙 1 — PyQt6 반환값 None 가능성**
`QMenu.addAction()`, `QListWidget.viewport()` 등 PyQt6 메서드는 mypy 타입이 `X | None`이다.
→ `.triggered`, `.mapToGlobal()` 등을 바로 호출하면 `union-attr` 오류.
→ **반드시** `assert result is not None` 추가 후 사용.

**규칙 2 — sys.excepthook 세 번째 인자 타입**
`sys.excepthook` 시그니처의 세 번째 파라미터는 `types.TracebackType | None`.
→ `object`로 선언하면 `logging.critical(exc_info=...)` 호출 시 `arg-type` 오류.
→ **반드시** `import types` 후 `types.TracebackType | None` 사용.

**규칙 3 — 메서드명 불일치 (AttributeError → 무음 앱 종료)**
Qt 슬롯에서 `AttributeError` 발생 시 로그 없이 앱이 종료된다.
→ 새 메서드를 작성할 때 호출부(main_window.py)와 정의부(widget.py)의 메서드명을 반드시 교차 확인.
→ `add_macro` vs `add_favorite` 같은 불일치가 실제로 발생한 사례.

**규칙 4 — 표준 라이브러리 정밀 타입 사용**
`logging.Logger.critical/error` 등의 `exc_info` 인자는 `bool | tuple[type[BaseException], BaseException, TracebackType | None] | ...` 형식을 요구.
→ 커스텀 타입(`object`, `Any`)으로 넘기지 말 것. 정확한 stdlib 타입을 `import types`로 가져와 사용.

---

## 8. 현재 진행 상태 (v0.2.8 — 2026-04-15 기준)

### 마일스톤
- [x] M0: CI/CD 환경 — GitHub Actions, Windows EXE 빌드, Releases 자동 업로드
- [x] M1: Win32 이벤트 캡처 — WH_MOUSE_LL/WH_KEYBOARD_LL, DPI 정규화, ESC×3 긴급 중지
- [x] M2: JSON 저장 + 재생 — SendInput, 절대 타임스탬프 기반 재생, click/drag 판별
- [x] M3: 오버레이 + GUI — 에디터(undo/redo, 구간 재생), 오버레이, F6/F7 핫키
- [x] M4: color_trigger — GetPixel 색상 감지, F7 삽입, ColorCheckNode
- [x] M5: 시퀀서 — 드래그앤드롭, .macroflow 저장/불러오기, 실행 상태 시각화

### M5 이후 추가 구현
- [x] 마우스 휠 녹화/재생 (수직·수평, 그룹 표시)
- [x] 에디터 병합 — 여러 JSON → 하나로 병합, source 열 표시
- [x] 시퀀서 UX 개선 — 중복 버튼 제거, 파일 간 경로 버그 수정
- [x] 매크로 간 딜레이 스핀박스 (시퀀스 실행 + 병합 공용)
- [x] ESC×3 — 시퀀서 실행 중에도 무조건 작동하도록 수정
- [x] 구간 재생 전용 버튼 + 스핀박스 크기 개선
- [x] 즐겨찾기 탭 — favorites/ 폴더, 더블클릭 로드, 우클릭 시퀀서 추가
- [x] 키 수정 버그 수정 — OEM 특수문자 VK 매핑 + VkKeyScanA 폴백
- [x] 이전 매크로 복원 — F6 실수 시 1클릭 복원 (메모리+파일 백업)
- [x] 음수 딜레이 이벤트 순서 역전 방지 — last_significant_event_end_ns 클램프
- [x] drag sleep 100ms 제거 — 단일 SendInput 배치 호출로 타이밍 드리프트 수정
- [x] GDI 핸들 누수 수정 — get_pixel_color() try/finally

**현재 단계**: 기능 구현 완료. 실사용 피드백 기반 UX 개선 중.

---

## 10. GitHub Actions CI/CD

### 빌드 트리거
- `main` 브랜치 push 시 자동 빌드
- Windows runner(`windows-latest`)에서 PyInstaller로 단일 `.exe` 생성
- GitHub Releases에 자동 업로드

### 릴리즈 태그 형식
```
v{version}-build.{run_number}
예: v0.1.0-build.12
```

### 팀원 다운로드 방법
1. GitHub 저장소 → Releases 탭
2. 최신 릴리즈의 `MacroFlow.exe` 다운로드
3. 더블클릭 실행 (설치 불필요)
4. 첫 실행 시 SmartScreen 경고 → "추가 정보" → "실행" 클릭

### ⚠️ 회사 방화벽 GitHub 차단 시 대안
github.com 접속이 안 되면 아래 중 하나로 대체:
- **Gitea self-hosted**: 사내 서버에 Git + CI 직접 구축
- **네트워크 드라이브 배포**: CI 빌드 후 exe를 사내 공유 폴더에 자동 복사
- **이메일 배포**: GitHub Actions에서 메일로 exe 첨부 발송

> 확인 필요: 회사 PC에서 github.com 접속 가능 여부 → MVP 진입 전 테스트
