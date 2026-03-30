# SECURITY.md — Windows 배포 보안 전략

---

## 1. 실행 권한

### UAC (User Account Control)
- MacroFlow는 **관리자 권한 불필요** (`asInvoker`)
- Win32 LL Hook (`WH_MOUSE_LL`, `WH_KEYBOARD_LL`)은 일반 사용자 권한으로 동작
- PyInstaller 매니페스트에 `asInvoker` 명시 (`build/macroflow.manifest`)

### 예외: UAC 창 이벤트 캡처 불가
LL Hook은 UAC 권한 상승 창의 이벤트를 캡처하지 못한다.
녹화 중 UAC 창이 뜨면 경고 표시 후 계속 녹화 (해당 구간 이벤트 누락 안내).

---

## 2. SmartScreen 경고 대응

코드 서명(Code Signing Certificate) 없이 배포할 경우:
- 첫 실행 시 "Windows에서 PC를 보호했습니다" 경고 표시
- **팀원 안내**: "추가 정보" 클릭 → "실행" 클릭

### 팀원용 안내 문구 (Releases 페이지에 포함)
```
처음 실행 시 Windows 보안 경고가 표시될 수 있습니다.
"추가 정보"를 클릭한 후 "실행" 버튼을 클릭하세요.
이는 내부 배포 앱에서 정상적으로 발생하는 현상입니다.
```

---

## 3. GetPixel 보안 정책 검토

### GetPixel은 스크린샷이 아님
| 구분 | API | 동작 | 정책 위반 가능성 |
|---|---|---|---|
| 스크린샷 | BitBlt, PrintScreen, DXGIOutputDuplication | 화면 영역을 메모리/파일로 복사 | 높음 |
| 픽셀 읽기 | GetPixel | 단일 픽셀 RGB값 1개 반환 | 낮음 |

### MVP 최우선 테스트 항목
회사 금융 PC에서 GetPixel 호출이 DLP/보안 솔루션에 걸리는지 직접 확인 필요.
확인 방법: M0 exe 빌드 후 회사 PC에서 color_trigger 노드 동작 테스트.

### GetPixel 차단 시 대안
```
대안 1: window_trigger만 사용 (창 제목 변화 감지)
대안 2: 고정 wait 이벤트로 대체 (타이밍 기반)
대안 3: 보안팀과 GetPixel 허용 예외 신청
```

---

## 4. 데이터 보안

### 매크로 파일 (JSON) 민감 정보 처리
- 매크로 파일에는 좌표·타이밍 정보만 저장
- 키 입력(key_down/key_up)에 실제 입력 내용이 포함됨
  → 비밀번호 입력 구간은 녹화하지 않도록 사용자 교육 필요
  → 향후 "민감 구간 마스킹" 기능 추가 검토 (Phase2)

### 임시 저장 파일
- 경로: `%APPDATA%\MacroFlow\temp\`
- 앱 정상 종료 시 temp 파일 자동 삭제 옵션 제공
- 회사 DLP가 AppData 폴더를 스캔할 수 있음 → 민감 입력 구간 주의

### 네트워크
- MacroFlow는 네트워크 요청을 일절 하지 않음
- 업데이트 확인, 원격 측정(telemetry) 없음
- GitHub Releases 다운로드는 사용자가 브라우저에서 직접 수행

---

## 5. 개발 서버 (openclaw) 보안

### GitHub 인증
- openclaw → GitHub: SSH 키 인증 권장 (`~/.ssh/id_ed25519`)
- HTTPS + Personal Access Token도 가능하나 SSH 키 선호
- GitHub Actions 토큰: `GITHUB_TOKEN` (자동 생성, 별도 설정 불필요)

### 코드 보안
- `pyproject.toml`에 의존성 버전 고정 (`uv.lock` 파일 커밋)
- `uv.lock` 없으면 빌드마다 의존성 버전이 달라질 수 있음
