# 변경 내역

## v1.5.0 — 2026-07-29

### 추가

- 설정 가능한 글로벌 운영 단축키(F1~F24, Windows 예약 F12 제외)와 에디터 내부 동작 추가 단축키
- 텍스트 입력·클릭·색 체크 삽입을 툴바·우클릭 메뉴·키보드에서 동일한 명령으로 실행
- 매크로 에디터와 시퀀서의 작업 흐름별 다중 행 툴바 및 현재 탭 문서용 파일 명령
- F8 글로벌 단축키와 툴바 버튼으로 녹화·일반/구간/반복 재생 일시중지·재개
- 우측 하단 오버레이의 `PAUSE · REC` / `PAUSE · PLAY` 상태 표시
- 시퀀서에 매크로 사이 문구 입력·좌/우/더블클릭·색상 대기·고정 대기 단계 추가
- 동일 매크로 반복 배치, 단계 복제, stable step ID 기반 재정렬
- `.macroflow` v1.1 `inline_events` 및 재생 설정 snapshot 저장

### 안정성

- 글로벌 단축키 세트의 원자적 교체·부분 실패 정리·이전 설정 rollback·degraded fail-closed 처리
- QSettings 저장 후 sync/readback 검증과 저장 실패 시 runtime 설정 복구
- 활성 글로벌 키에서 recorder suppression을 파생해 변경 전 키를 정상 녹화 가능
- 설정 다이얼로그의 modal nested event loop 중 자동화 명령 차단 및 적용 직전 idle 재검증
- 실제 Windows `RegisterHotKey` 점유 충돌과 이전 세트 복구를 검증하는 Windows 전용 테스트
- 녹화 pause 구간의 이벤트와 경과시간을 timestamp에서 제거하고 queue 경계 이벤트 보존
- 재생 active-time clock으로 재개 후 catch-up 실행과 timeout 소진 방지
- pause는 열린 key·mouse gesture의 원래 release 뒤 안전 경계에서 적용
- stop/error 시 남아 있는 key·mouse 입력을 정확히 한 번 release
- 기존 macro JSON 관대한 loader와 canonical `.macroflow` v1.0 호환 유지
- 실행 전 전체 preflight로 부분 실행·입력 부작용 방지
- error EndNode와 failure edge 없는 오류의 success 오보고 방지
- 에디터·시퀀서 F6 capture owner 단일화 및 탭 전환·종료 정리
- Windows EXE에 side-effect-free mixed-sequence codec smoke 추가
- player session handle로 FlowEngine이 소유한 재생만 중지하도록 격리
- 시퀀스 실행 중 매크로 열기·편집·저장을 잠가 preflight 이후 파일 변경 방지
- native/QShortcut F6을 단일 router로 통합하고 녹화 중 중지 동작 우선
- packaged codec smoke에 30초 timeout·process tree 정리·SHA256 출력 추가

### 수정

- 시퀀서 탭의 `Ctrl+O/S/Shift+S`가 매크로 파일이 아닌 현재 플로우 문서에 적용되도록 수정
- 삽입 후 stable event ID로 새 행을 선택·스크롤·포커스하고 stale 비동기 색 캡처를 취소
- 860px 창과 14pt 접근성 글꼴에서 필수 툴바 동작이 overflow 메뉴로 숨지 않도록 문구·폭 조정
- 색 대기 hover 갱신을 8px 이동·50ms 유지·원위치 복귀로 강화하고 pause·stop·timeout 경계 보장
- 클릭/드래그 판정을 재생 지연이 아닌 RAW 녹화 시간으로 고정해 색 일치 후 체크박스 클릭이 간헐적으로 drag로 변형되던 문제 수정

## v1.3.1 — 2026-07-23

### 수정

- 시퀀서가 표현할 수 없는 메타데이터·노드 속성을 가진 플로우를 거부해 덮어쓰기 손실 방지
- 정규 시퀀서 문서의 생성 시각을 저장·로드 후에도 보존
- `FlowEngine` 중복 시작을 원자적으로 차단하고 stop timeout 동안 worker handle 유지

### 배포 검증

- Linux와 Windows에서 잠금된 의존성으로 전체 테스트 실행
- PyInstaller EXE 빌드 후 실제 메인 창 startup smoke 추가
- GitHub Release는 수동 `workflow_dispatch`에서만 생성

## v1.3.0 — 2026-07-14

### 추가

- 녹화·일반 재생·반복 재생·시퀀스 실행 상태를 표시하는 반투명 오버레이
- 색 체크의 대기·무시·중지 동작과 action별 timeout 설정
- 시퀀스 저장·로드·매크로 병합 및 Windows RDP 실환경 smoke 도구
- Condition/Loop 내부 이벤트의 기록 시간·delay override·재생 속도 지원

### 개선

- 오버레이 긴 문구·최대 진행률 표시와 드래그·화면 경계 배치
- 클릭·색 체크·WaitEvent 이후 timeline compensation
- 시퀀스 실행 중 목록 변경 차단과 실행 간 signal generation 격리
- F7·긴급 중지·hook 시작 실패·stop timeout lifecycle 정리
- expression sandbox의 허용 연산 제한과 문자열 증폭 방어

### 수정

- 색 조회 중 중지 후 클릭이 실행될 수 있던 문제
- polling interval보다 짧은 timeout이 초과 대기하던 문제
- Condition/Loop 내부 대기 후 다음 이벤트가 즉시 따라잡기 실행되던 문제
- 이전 시퀀스의 늦은 signal이 새 실행 상태를 변경하던 문제
- 시퀀스 worker가 살아 있는 동안 다른 재생·녹화를 시작할 수 있던 문제

### 검증

- Linux 전체 pytest, Ruff, mypy 통과
- Windows source-runtime 전체 pytest 및 실제 click·text·color·drag·wheel smoke 통과
