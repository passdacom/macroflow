---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/overlay.py"
type: "code"
community: "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
location: "L23"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions
---

# OverlayWindow

## Connections
- [[.__init__()_3]] - `method` [EXTRACTED]
- [[.__init__()_4]] - `calls` [INFERRED]
- [[._paint_hint()]] - `method` [EXTRACTED]
- [[._paint_playing()]] - `method` [EXTRACTED]
- [[._paint_recording()]] - `method` [EXTRACTED]
- [[._position_bottom_right()]] - `method` [EXTRACTED]
- [[._tick()]] - `method` [EXTRACTED]
- [[._toggle_blink()]] - `method` [EXTRACTED]
- [[.mouseMoveEvent()]] - `method` [EXTRACTED]
- [[.mousePressEvent()]] - `method` [EXTRACTED]
- [[.mouseReleaseEvent()]] - `method` [EXTRACTED]
- [[.paintEvent()]] - `method` [EXTRACTED]
- [[.set_event_count()]] - `method` [EXTRACTED]
- [[.set_progress()]] - `method` [EXTRACTED]
- [[.set_repeat()]] - `method` [EXTRACTED]
- [[.show_hint()]] - `method` [EXTRACTED]
- [[.start_playing()]] - `method` [EXTRACTED]
- [[.start_recording()]] - `method` [EXTRACTED]
- [[.stop()_1]] - `method` [EXTRACTED]
- [[.stop_hint()]] - `method` [EXTRACTED]
- [[F6 캡처 모드 현재 마우스 위치와 픽셀 색을 에디터 캡처 콜백으로 전달한다.]] - `uses` [INFERRED]
- [[MacroFlow 메인 창.  전체 상태 머신(idle  recording  stopping  playing)을 관리한다. F6F7 글로]] - `uses` [INFERRED]
- [[MacroFlow 메인 창. 녹화·재생 상태 머신 + UI 통합.]] - `uses` [INFERRED]
- [[MainWindow]] - `uses` [INFERRED]
- [[QSettings에서 창 위치·크기와 마지막 파일을 복원한다.]] - `uses` [INFERRED]
- [[QWidget]] - `inherits` [EXTRACTED]
- [[WM_HOTKEY 처리 (Windows 전용).]] - `uses` [INFERRED]
- [[macros 폴더에 날짜·시간 파일명으로 자동 저장 후 시퀀서에 추가한다.          다이얼로그 없이 즉시 저장되며, 시퀀서 탭으로 자동]] - `uses` [INFERRED]
- [[overlay.py]] - `contains` [EXTRACTED]
- [[경로에서 매크로를 로드하여 에디터에 표시한다.]] - `uses` [INFERRED]
- [[구간 SpinBox 값에서 event_range (start, end exclusive)를 계산한다.]] - `uses` [INFERRED]
- [[구간 재생 전용 버튼 구간이 설정된 경우에만 1회 재생한다.]] - `uses` [INFERRED]
- [[녹화 중 F7 현재 마우스 커서 위치의 픽셀 색을 ColorTriggerEvent로 삽입한다.]] - `uses` [INFERRED]
- [[녹화재생힌트 상태를 표시하는 미니 플로팅 창.]] - `rationale_for` [EXTRACTED]
- [[매크로 로드 후 구간 SpinBox 범위를 갱신한다.]] - `uses` [INFERRED]
- [[빈 구간 입력을 0 sentinel로 되돌려 '처음''끝' 표시를 복원한다.]] - `uses` [INFERRED]
- [[새 녹화 시작 전 기존 매크로를 pre_recording_.json 으로 임시 저장한다.]] - `uses` [INFERRED]
- [[속도 콤보 변경 처리. '직접 입력...' 선택 시 수동 입력 다이얼로그를 띄운다.]] - `uses` [INFERRED]
- [[시퀀서 '에디터로 병합' 결과를 에디터 탭에 로드한다.          병합된 MacroData를 편집 가능한 상태로 에디터에 표시한다.]] - `uses` [INFERRED]
- [[시퀀서 더블클릭 시 매크로를 로드하고 에디터 탭으로 전환한다.]] - `uses` [INFERRED]
- [[시퀀서 탭에서 F7 시퀀스 실행 중이면 중지, 아니면 실행.]] - `uses` [INFERRED]
- [[시퀀스 완료오류 시 emergency hook 해제 후 툴바·상태바를 갱신한다.]] - `uses` [INFERRED]
- [[앱 포커스 상태에서 ESC×3 긴급 중지.]] - `uses` [INFERRED]
- [[에디터에서 단일 이벤트 실행 요청 수신 시 해당 범위만 재생한다.]] - `uses` [INFERRED]
- [[영구 저장용 macros 디렉토리 경로를 반환한다.          PyInstaller 패키징 상태이면 exe 파일 옆 macros 폴더,]] - `uses` [INFERRED]
- [[이전 녹화를 복원한다.          새 녹화를 시작하기 직전에 백업해 둔 매크로를 에디터에 로드한다.         실수로 F6을 눌러 기존]] - `uses` [INFERRED]
- [[즐겨찾기 저장용 favorites 디렉토리 경로를 반환한다.          macros 와 별도의 favorites 폴더를 사용한다.]] - `uses` [INFERRED]
- [[창 위치·크기와 마지막 열었던 파일 경로를 QSettings에 저장한다.]] - `uses` [INFERRED]
- [[최근 녹화 서브메뉴를 임시 저장 파일 목록으로 갱신한다.]] - `uses` [INFERRED]
- [[탭 전환 시 툴바 버튼 상태와 상태바 힌트를 갱신한다.]] - `uses` [INFERRED]
- [[파일 다이얼로그 초기 폴더를 반환한다.          PyInstaller 패키징 상태이면 exe 파일이 있는 폴더,         개발 환경]] - `uses` [INFERRED]
- [[현재 매크로 뒤에 새 녹화를 이어붙이는 녹화 모드를 시작한다.]] - `uses` [INFERRED]
- [[현재 매크로를 이름 입력 후 즐겨찾기 폴더에 저장하고 즐겨찾기 탭에 추가한다.]] - `uses` [INFERRED]
- [[현재 매크로에 저장되는 색 체크 timeout폴링 설정을 편집한다.]] - `uses` [INFERRED]
- [[현재 파일에 덮어쓰기 저장한다.          _current_file이 설정된 경우 확인 다이얼로그 후 덮어쓰기.         _curr]] - `uses` [INFERRED]
- [[현재 활성 탭이 즐겨찾기인지 반환한다.]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions