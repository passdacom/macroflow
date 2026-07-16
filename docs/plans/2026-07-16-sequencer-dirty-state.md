# 시퀀서 미저장 변경 보호 구현 계획

> 작성일: 2026-07-16
> 근거: `docs/exec-plans/active/2026-04-28-backlog.md`의 SUGGEST-07

## 목표

시퀀서 목록·순서·간격을 수정하고 저장하지 않은 채 다른 플로우를 열거나 앱을 종료할 때 변경이 조용히 유실되지 않도록 한다.

## 우선순위 판단

| 기준 | 판단 |
|---|---|
| Reach | 시퀀서를 편집하는 모든 사용자에게 적용 |
| Impact | 저장 누락에 따른 작업 유실 방지로 높음 |
| Confidence | 기존 백로그에 요구사항이 명시되어 있고 현재 코드에 dirty 추적이 없음을 확인 |
| Effort | 단일 위젯과 MainWindow 연결, 회귀 테스트 추가 수준으로 중간 이하 |

Phase2의 UI Automation·변수·서브플로우보다 제품 방향 의존성이 낮고 안정성 우선 원칙에 직접 부합하므로 다음 기능으로 선정한다.

## 범위

### 포함

1. 다음 유효 변경 후 시퀀서를 dirty 상태로 전환한다.
   - 매크로 파일 추가
   - 선택 항목 제거
   - 드래그앤드롭 순서 변경
   - 매크로 사이 대기값 변경
2. 중복 파일 추가나 실패한 변경 같은 no-op은 dirty로 만들지 않는다.
3. 정상적인 플로우 로드와 저장 성공 후 clean 상태로 전환한다.
4. 저장 실패 또는 저장 다이얼로그 취소 시 dirty 상태와 기존 저장 경로를 유지한다.
5. dirty 상태는 메인 탭 제목 `시퀀서 *`로 표시한다.
6. dirty 상태에서 다른 `.macroflow`를 열거나 앱을 종료하면 `저장 / 저장 안 함 / 취소`를 제공한다.
7. 저장을 선택한 경우 실제 저장 성공 뒤에만 열기·종료를 계속한다.
8. 취소하면 현재 편집 데이터와 앱 창을 유지한다. 안전을 위해 실행 중인 녹화·재생·시퀀서는 확인창 전에 중지한다.
9. 비선형·불균일 간격 등 단순 시퀀서가 손실 없이 표현할 수 없는 플로우는 기존 상태를 유지한 채 로드를 거부한다.
10. 플로우 저장은 임시 파일 기록과 원자적 교체를 사용해 부분 쓰기 실패가 기존 파일을 손상시키지 않도록 한다.

### 제외

- 매크로 에디터 자체의 dirty 상태 UX 변경
- 비선형 플로우 편집 기능
- 다중 모니터·125%/150% DPI Windows 실기기 검증
- 현재 환경에서 제공되지 않는 UAC secure desktop 검증

## Acceptance Criteria

- [x] 새 `MacroSequencerWidget`은 clean이다.
- [x] add/remove/reorder/gap 변경은 dirty를 만든다.
- [x] 중복 add와 제거 대상 없음은 상태를 바꾸지 않는다.
- [x] 성공한 load/save는 clean을 만든다.
- [x] 실패한 save-as는 dirty 및 기존 `_current_flow_path`를 보존한다.
- [x] dirty signal에 따라 탭 제목이 `시퀀서` ↔ `시퀀서 *`로 갱신된다.
- [x] dirty 상태의 open/close에서 Cancel은 편집 데이터와 앱 창을 보존한다.
- [x] 종료 확인 전에 active runtime을 정리하고 worker 종료 실패 시 창 종료를 차단한다.
- [x] Save는 저장 성공 시에만 open/close를 계속한다.
- [x] 손실성 플로우 projection은 현재 편집 상태를 보존한 채 거부한다.
- [x] 부분 직렬화 실패 시 기존 `.macroflow` 파일과 dirty/path 상태를 보존한다.
- [x] 기존 전체 테스트, Ruff, mypy, `git diff --check`가 통과한다.

## 구현 순서

1. `tests/test_sequencer_dirty_state.py`에 위젯 dirty 전이와 저장 성공/실패 테스트를 추가하고 RED를 확인한다.
2. `MacroSequencerWidget`에 `dirty_changed`, `is_dirty`, dirty 전이 헬퍼를 최소 구현한다.
3. add/remove/reorder/gap/load/save 경계에 dirty 전이를 연결한다.
4. 미저장 변경 확인 API를 추가하고 open 경로에 적용한다.
5. MainWindow가 tab title을 갱신하고 close cancel을 존중하도록 테스트를 추가한 뒤 구현한다.
6. targeted test → 전체 test → Ruff → mypy → diff/security review 순으로 검증한다.
