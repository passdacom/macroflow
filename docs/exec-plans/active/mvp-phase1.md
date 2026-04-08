# mvp-phase1.md — MVP 마일스톤 계획

> 최종 업데이트: 2026-04-08 (v0.2.0)

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

## 마일스톤 0: 개발 환경 셋업 ✅ 완료

**목표**: openclaw → GitHub → Releases 파이프라인 동작 확인

완료 기준:
- [x] GitHub 저장소 생성 및 이 하네스 코드 push
- [x] `main` push 시 GitHub Actions 워크플로우 트리거 확인
- [x] `dist/MacroFlow.exe` Releases에 자동 업로드 확인
- [ ] 회사 PC에서 exe 다운로드 후 더블클릭 실행 확인
- [ ] **GetPixel 보안 정책 통과 여부 확인** (회사 PC에서 최우선 테스트)

---

## 마일스톤 1: Win32 기반 이벤트 캡처 ✅ 완료

**목표**: `recorder.py` 기본 동작 — LL Hook으로 이벤트 캡처 후 raw_events 생성

완료 기준:
- [x] `win32/hooks.py` — WH_MOUSE_LL + WH_KEYBOARD_LL ctypes 구현
- [x] `win32/dpi.py` — 논리 해상도 조회 + 좌표 비율 변환
- [x] `recorder.py` — Hook 이벤트 → MacroEvent 변환, id 생성
- [x] 단축키(F6) 토글로 녹화 시작/중지
- [x] ESC 3회 긴급 중지 (녹화 + 재생 + 시퀀서 모두 대응)
- [x] 빠른 타이핑(10키/100ms) 이벤트 순서 보존 확인
- [x] pytest: mock으로 recorder 로직 테스트 통과
- [ ] exe 빌드 후 실제 Windows에서 동작 확인

---

## 마일스톤 2: JSON 저장 + 기본 재생 ✅ 완료

**목표**: 녹화한 매크로를 JSON으로 저장하고 재생 가능

완료 기준:
- [x] `macro_file.py` — MacroData 직렬화/역직렬화
- [x] raw_events / events 이중 구조 저장
- [x] 임시 저장 (`%APPDATA%\MacroFlow\temp\`)
- [x] `win32/sendinput.py` — SendInput ctypes 구현
- [x] `player.py` — 절대 타임스탬프 기준 재생 + 드리프트 보정
- [x] click/drag 판별 (8px / 300ms 임계값)
- [x] F7 토글로 재생 시작/중지
- [x] pytest: 재생 타이밍 오차 < 5ms 확인 (mock 환경)
- [ ] exe로 실제 재생 동작 확인

---

## 마일스톤 3: 미니 오버레이 + 기본 GUI ✅ 완료

**목표**: 팀원이 사용할 수 있는 최소 UI

완료 기준:
- [x] 미니 오버레이 창 (180×48px, 항상 최상위, 우하단)
  - 녹화 중: 빨간 점 깜빡임 + 경과 시간 + 이벤트 수
  - 재생 중: 진행률 + 속도 배율
- [x] 메인 창 에디터 탭
  - 이벤트 목록 테이블 (그룹 표시, source 열)
  - mouse_move 일괄 삭제 버튼
  - 딜레이 개별/일괄 수정
  - 원본으로 되돌리기 (undo/redo)
  - 구간 재생 (시작~끝 행 지정, 전용 재생 버튼)
- [x] 파일 열기/저장 다이얼로그
- [x] 속도/반복/간격 툴바 설정
- [ ] 비기술자 팀원 1명에게 사용성 테스트

---

## 마일스톤 4: color_trigger + 미니 오버레이 완성 ✅ 완료

**목표**: 금융 웹앱 로딩 감지 기능 — 핵심 기능

완료 기준:
- [x] `win32/hooks.py` — GetPixel 구현
- [x] color_trigger 이벤트 재생 (폴링 + tolerance 판별)
- [x] color_check 노드 UI — F6 캡처로 좌표+색 자동 입력
- [x] F7 녹화 중 색상 체크 포인트 삽입
- [ ] **회사 PC 금융 웹앱에서 로딩 감지 실제 동작 확인**
- [ ] timeout 처리 (error / skip / retry) UI

---

## 마일스톤 5: 드래그앤드롭 시퀀서 ✅ 완료

**목표**: 여러 매크로 JSON을 순서대로 조합하여 실행

완료 기준:
- [x] 리스트 기반 드래그앤드롭 순서 변경
- [x] macro 노드 — JSON 파일 드래그앤드롭 추가
- [x] color_check 노드 — FlowEngine 내 match/timeout 분기
- [x] counter 노드 — 반복 카운터
- [x] `.macroflow` 파일 저장/불러오기
- [x] 실행 중 노드 상태 시각화 (완료/실행중/실패)
- [x] 에디터 병합 — 여러 JSON을 하나로 합쳐 에디터에 로드
- [x] 매크로 간 딜레이 스핀박스 (시퀀스 실행 + 병합 공용)
- [x] 파일 경로 버그 수정 — 서로 다른 폴더의 JSON 파일도 정상 실행
- [ ] 비주얼 플로우차트 캔버스 (노드 그래프 편집 UI) — 미구현, 필요 시 추후

---

## 현재 다음 할 일

- [ ] 회사 PC에서 exe 실제 동작 확인 (M0~M5 전 기능)
- [ ] 비기술자 팀원 사용성 테스트
- [ ] 금융 웹앱 color_trigger 실전 검증

---

## 마일스톤별 의존성

```
M0 (환경) → M1 (캡처) → M2 (저장+재생) → M3 (GUI)
                                              ↓
                                        M4 (color_trigger)
                                              ↓
                                        M5 (시퀀서)
```

---

## 리스크 목록

| 리스크 | 발생 시점 | 상태 | 대응 |
|---|---|---|---|
| GetPixel 보안 정책 차단 | M0 테스트 | ⚠️ 미확인 | window_trigger 조합으로 대체 전략 수립 |
| LL Hook 빠른 이벤트 손실 | M1 테스트 | ✅ 해결 | Hook 콜백 경량화, 소비자 스레드 분리 |
| PyInstaller SmartScreen 차단 | M0 exe 테스트 | ⚠️ 미확인 | 팀원에게 "추가 정보→실행" 안내 문서 작성 |
| GitHub Actions 빌드 실패 | M0~전체 | ✅ 정상 | CI 파이프라인 안정적으로 동작 중 |
| 서로 다른 폴더 JSON 파일 실행 오류 | M5 실사용 | ✅ 해결 | 절대 경로 허용, 보안 체크는 상대 경로만 적용 |
