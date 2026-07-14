# 변경 내역

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
