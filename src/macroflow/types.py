"""MacroFlow 핵심 데이터 타입 정의.

모든 이벤트 타입, MacroData 컨테이너, 메타·설정 클래스를 여기에 정의한다.
이 모듈은 Win32 및 PyQt6에 의존하지 않으므로 모든 환경에서 임포트 가능하다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(kw_only=True)
class MacroEvent:
    """모든 매크로 이벤트의 공통 기반 클래스.

    Attributes:
        id: 8자리 hex 문자열. 녹화 시 생성, 이후 변경 불가.
        type: 이벤트 종류 문자열.
        timestamp_ns: 녹화 시작 기준 경과 나노초 (perf_counter_ns).
        delay_override_ms: None이면 timestamp_ns 기준 절대 시간으로 재생.
            값이 있으면 직전 이벤트 후 N ms 대기.
    """

    id: str
    type: str
    timestamp_ns: int
    delay_override_ms: int | None = None
    source_file: str = ""


@dataclass(kw_only=True)
class MouseButtonEvent(MacroEvent):
    """mouse_down / mouse_up 이벤트.

    Attributes:
        x_ratio: 화면 너비 대비 X 좌표 비율 (0.0~1.0).
        y_ratio: 화면 높이 대비 Y 좌표 비율 (0.0~1.0).
        button: 마우스 버튼 종류.
        recorded_color: 녹화 시 해당 좌표의 픽셀 색 (#RRGGBB). None이면 미저장.
        color_check_enabled: True이면 재생 시 클릭 전 recorded_color와 현재 픽셀 색을
            비교하여 불일치 시 해당 클릭을 스킵한다.
    """

    x_ratio: float
    y_ratio: float
    button: Literal["left", "right", "middle"] = "left"
    recorded_color: str | None = None
    color_check_enabled: bool = False
    color_check_on_mismatch: Literal["skip", "stop"] = "skip"


@dataclass(kw_only=True)
class MouseMoveEvent(MacroEvent):
    """mouse_move 이벤트.

    Attributes:
        x_ratio: 화면 너비 대비 X 좌표 비율 (0.0~1.0).
        y_ratio: 화면 높이 대비 Y 좌표 비율 (0.0~1.0).
    """

    x_ratio: float
    y_ratio: float


@dataclass(kw_only=True)
class KeyEvent(MacroEvent):
    """key_down / key_up 이벤트.

    Attributes:
        key: 사람이 읽을 수 있는 키 이름 (예: "a", "enter", "f6").
        vk_code: Windows Virtual Key Code. 재생 시 이 값 사용.
    """

    key: str
    vk_code: int


@dataclass(kw_only=True)
class MouseWheelEvent(MacroEvent):
    """mouse_wheel 이벤트 — 마우스 휠 스크롤.

    core-beliefs.md 원칙 4: 좌표는 비율로 저장.
    재생 시 커서를 x_ratio/y_ratio 위치로 먼저 이동한 뒤 휠 입력을 전송해야
    올바른 윈도우가 스크롤 이벤트를 받는다.

    Attributes:
        delta: 스크롤 양. 양수=위/우, 음수=아래/좌. WHEEL_DELTA(120) 단위.
        axis: 스크롤 축. "vertical" 또는 "horizontal".
        x_ratio: 발생 위치 X 비율 (0.0~1.0).
        y_ratio: 발생 위치 Y 비율 (0.0~1.0).
    """

    delta: int          # 양수=위/우, 음수=아래/좌 (1노치 = ±120)
    axis: str           # "vertical" | "horizontal"
    x_ratio: float      # 발생 위치 (재생 시 커서 선이동에 사용)
    y_ratio: float


@dataclass(kw_only=True)
class WaitEvent(MacroEvent):
    """wait 이벤트 — UI에서 수동 삽입하는 고정 대기.

    Attributes:
        duration_ms: 대기 시간 (밀리초).
    """

    duration_ms: int


@dataclass(kw_only=True)
class ColorTriggerEvent(MacroEvent):
    """color_trigger 이벤트 — GetPixel 기반 픽셀 색 감지 대기.

    core-beliefs.md 원칙 7: 스크린샷 API 절대 사용 금지.
    GetPixel로 단일 픽셀만 읽는다.

    Attributes:
        x_ratio: 감지할 픽셀의 X 좌표 비율.
        y_ratio: 감지할 픽셀의 Y 좌표 비율.
        target_color: 기다릴 목표 색상 (#RRGGBB 형식).
        tolerance: RGB 채널별 허용 오차 (±tolerance). 기본 10.
        timeout_ms: 최대 대기 시간 (밀리초).
        check_interval_ms: 폴링 주기 (밀리초).
        on_timeout: 타임아웃 시 동작.
    """

    x_ratio: float
    y_ratio: float
    target_color: str  # "#RRGGBB"
    tolerance: int = 10
    timeout_ms: int = 10000
    check_interval_ms: int = 50
    on_timeout: Literal["error", "skip", "retry"] = "error"


@dataclass(kw_only=True)
class WindowTriggerEvent(MacroEvent):
    """window_trigger 이벤트 — 창 제목 감지 대기.

    Attributes:
        window_title_contains: 감지할 창 제목 부분 문자열.
        timeout_ms: 최대 대기 시간 (밀리초).
        on_timeout: 타임아웃 시 동작.
    """

    window_title_contains: str
    timeout_ms: int = 10000
    on_timeout: Literal["error", "skip", "retry"] = "error"


@dataclass(kw_only=True)
class ConditionEvent(MacroEvent):
    """condition 이벤트 — DSL 표현식 기반 조건 분기.

    Attributes:
        expression: 평가할 DSL 표현식 (script_engine.py 샌드박스 내에서만 실행).
        if_true: 조건이 참일 때 실행할 이벤트 목록.
        if_false: 조건이 거짓일 때 실행할 이벤트 목록.
    """

    expression: str
    if_true: list[AnyEvent] = field(default_factory=list)
    if_false: list[AnyEvent] = field(default_factory=list)


@dataclass(kw_only=True)
class LoopEvent(MacroEvent):
    """loop 이벤트 — 반복 실행.

    Attributes:
        count: 반복 횟수. -1이면 stop() 호출 또는 핫키까지 무한 반복.
        events: 반복할 이벤트 목록.
    """

    count: int
    events: list[AnyEvent] = field(default_factory=list)


# 모든 이벤트 타입의 합집합 — recorder/player/macro_file에서 사용
AnyEvent = (
    MouseButtonEvent
    | MouseMoveEvent
    | MouseWheelEvent
    | KeyEvent
    | WaitEvent
    | ColorTriggerEvent
    | WindowTriggerEvent
    | ConditionEvent
    | LoopEvent
)


@dataclass(kw_only=True)
class MacroMeta:
    """매크로 파일 메타데이터.

    Attributes:
        version: JSON 스키마 버전. 마이그레이션 판단에 사용.
        app_version: 녹화 당시 앱 버전.
        created_at: ISO 8601 생성 시각.
        screen_width: 녹화 당시 논리 해상도 너비 (DPI 보정 후).
        screen_height: 녹화 당시 논리 해상도 높이 (DPI 보정 후).
        dpi_scale: 녹화 PC의 DPI 배율 (1.0=100%, 1.25=125%).
        author: 작성자 (선택).
        description: 매크로 설명 (선택).
    """

    version: str
    app_version: str
    created_at: str
    screen_width: int
    screen_height: int
    dpi_scale: float
    author: str = ""
    description: str = ""


@dataclass(kw_only=True)
class MacroSettings:
    """재생 및 판별 임계값 설정.

    core-beliefs.md 원칙 1: 클릭/드래그 판별은 재생 시 이 값으로 수행.

    Attributes:
        click_dist_threshold_px: 클릭 판별 거리 임계값 (픽셀).
        click_time_threshold_ms: 클릭 판별 시간 임계값 (밀리초).
        default_playback_speed: 재생 속도 배율.
        color_trigger_check_interval_ms: 색 감지 폴링 주기 (밀리초).
        color_trigger_default_timeout_ms: 색 감지 최대 대기 시간 (밀리초).
    """

    click_dist_threshold_px: int = 8
    click_time_threshold_ms: int = 300
    default_playback_speed: float = 1.0
    color_trigger_check_interval_ms: int = 50
    color_trigger_default_timeout_ms: int = 10000
    color_check_click_tolerance: int = 10


@dataclass(kw_only=True)
class MacroData:
    """매크로 전체 데이터 컨테이너.

    Attributes:
        meta: 파일 메타데이터.
        settings: 재생·판별 임계값.
        raw_events: 녹화 원본 이벤트. 절대 수정하지 않는다.
        events: 재생에 사용하는 편집본. 모든 편집은 여기서만.
        is_edited: raw_events와 events가 다른지 여부.
    """

    meta: MacroMeta
    settings: MacroSettings
    raw_events: list[AnyEvent]
    events: list[AnyEvent]
    is_edited: bool = False
