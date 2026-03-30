# mvp-phase1.md — MVP 마일스톤 계획

---

## 개발 환경 구조

```
[어디서든] SSH → openclaw (Linux 개발 서버)
  Claude Code 실행
  코드 작성 + pytest + ruff + mypy
  git push → GitHub
      ↓
  GitHub Actions (windows-latest)
  → PyInstaller → MacroFlow.exe
  → Releases 업로드
      ↓
  [회사 PC] 일회성 접속 → exe 다운로드 → 실행 테스트
```

**openclaw에서 Win32 코드 실행 방법:**
`src/macroflow/win32/__init__.py` 가 Linux에서 자동으로 mock을 주입.
실제 Win32 동작 확인은 GitHub Actions 빌드 후 exe로 테스트.

---

## 마일스톤 0: 개발 환경 셋업 ← 지금 여기

**목표**: openclaw → GitHub → Releases 파이프라인 동작 확인

완료 기준:
- [ ] GitHub 저장소 생성 및 이 하네스 코드 push
- [ ] `main` push 시 GitHub Actions 워크플로우 트리거 확인
- [ ] `dist/MacroFlow.exe` Releases에 자동 업로드 확인
- [ ] 회사 PC에서 exe 다운로드 후 더블클릭 실행 확인
- [ ] **GetPixel 보안 정책 통과 여부 확인** (회사 PC에서 최우선 테스트)

---

## 마일스톤 1: Win32 기반 이벤트 캡처 (핵심)

**목표**: `recorder.py` 기본 동작 — LL Hook으로 이벤트 캡처 후 raw_events 생성

완료 기준:
- [ ] `win32/hooks.py` — WH_MOUSE_LL + WH_KEYBOARD_LL ctypes 구현
- [ ] `win32/dpi.py` — 논리 해상도 조회 + 좌표 비율 변환
- [ ] `recorder.py` — Hook 이벤트 → MacroEvent 변환, id 생성
- [ ] 단축키(F6) 토글로 녹화 시작/중지
- [ ] ESC 3회 긴급 중지
- [ ] 빠른 타이핑(10키/100ms) 이벤트 순서 보존 확인
- [ ] pytest: mock으로 recorder 로직 테스트 통과
- [ ] exe 빌드 후 실제 Windows에서 동작 확인

---

## 마일스톤 2: JSON 저장 + 기본 재생

**목표**: 녹화한 매크로를 JSON으로 저장하고 재생 가능

완료 기준:
- [ ] `macro_file.py` — MacroData 직렬화/역직렬화
- [ ] raw_events / events 이중 구조 저장
- [ ] 임시 저장 (`%APPDATA%\MacroFlow\temp\`)
- [ ] `win32/sendinput.py` — SendInput ctypes 구현
- [ ] `player.py` — 절대 타임스탬프 기준 재생 + 드리프트 보정
- [ ] click/drag 판별 (8px / 300ms 임계값)
- [ ] F7 토글로 재생 시작/중지
- [ ] pytest: 재생 타이밍 오차 < 5ms 확인 (mock 환경)
- [ ] exe로 실제 재생 동작 확인

---

## 마일스톤 3: 미니 오버레이 + 기본 GUI

**목표**: 팀원이 사용할 수 있는 최소 UI

완료 기준:
- [ ] 미니 오버레이 창 (180×48px, 항상 최상위, 우하단)
  - 녹화 중: 빨간 점 깜빡임 + 경과 시간 + 이벤트 수
  - 재생 중: 진행률 + 속도 배율
- [ ] 메인 창 에디터 탭
  - 이벤트 목록 테이블
  - mouse_move 일괄 삭제 버튼
  - 딜레이 개별/일괄 수정
  - 원본으로 되돌리기
- [ ] 파일 열기/저장 다이얼로그
- [ ] 재생 전 설정 다이얼로그 (속도/반복/실패 처리)
- [ ] 비기술자 팀원 1명에게 사용성 테스트

---

## 마일스톤 4: color_trigger + 미니 오버레이 완성

**목표**: 금융 웹앱 로딩 감지 기능 — 핵심 기능

완료 기준:
- [ ] `win32/hooks.py` — GetPixel 구현
- [ ] color_trigger 이벤트 재생 (폴링 + tolerance 판별)
- [ ] 실패 팝업 (재시도/건너뛰기/중지)
- [ ] color_check 노드 UI — "화면 클릭해서 좌표 선택" + "현재 색 읽기"
- [ ] **회사 PC 금융 웹앱에서 로딩 감지 실제 동작 확인**
- [ ] timeout 처리 (error / skip / retry)

---

## 마일스톤 5: 드래그앤드롭 시퀀서 (플로우차트)

**목표**: 여러 매크로 JSON을 비주얼 플로우차트로 조합

완료 기준:
- [ ] 캔버스 + 노드 팔레트 UI
- [ ] macro 노드 — JSON 파일 드래그앤드롭
- [ ] color_check 노드 — match/timeout 분기
- [ ] counter 노드 — 반복 카운터
- [ ] `.macroflow` 파일 저장/불러오기
- [ ] 실행 중 노드 상태 시각화 (완료/실행중/실패)
- [ ] 단순 순차 실행 모드 (리스트 드래그앤드롭)

---

## 마일스톤별 예상 순서 및 의존성

```
M0 (환경) → M1 (캡처) → M2 (저장+재생) → M3 (GUI)
                                              ↓
                                        M4 (color_trigger)
                                              ↓
                                        M5 (시퀀서)
```

M3 완료 시점에 팀원 사용성 테스트 실시.
M4 완료 시점에 회사 금융 웹앱 실제 동작 확인 필수.

---

## 리스크 목록

| 리스크 | 발생 시점 | 대응 |
|---|---|---|
| GetPixel 보안 정책 차단 | M0 테스트 | window_trigger 조합으로 대체 전략 수립 |
| LL Hook 빠른 이벤트 손실 | M1 테스트 | Hook 콜백 경량화, 소비자 스레드 분리 |
| PyInstaller SmartScreen 차단 | M0 exe 테스트 | 팀원에게 "추가 정보→실행" 안내 문서 작성 |
| GitHub Actions 빌드 실패 | M0~전체 | 로컬 Windows 환경 fallback 준비 |
