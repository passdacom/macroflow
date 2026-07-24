# 변경 내역

## Unreleased

### 추가

- F8 글로벌 단축키와 툴바 버튼으로 녹화·일반/구간/반복 재생 일시중지·재개
- 우측 하단 오버레이의 `PAUSE · REC` / `PAUSE · PLAY` 상태 표시
- 시퀀서에 매크로 사이 문구 입력·좌/우/더블클릭·색상 대기·고정 대기 단계 추가
- 동일 매크로 반복 배치, 단계 복제, stable step ID 기반 재정렬
- `.macroflow` v1.1 `inline_events` 및 재생 설정 snapshot 저장

### 안정성

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
