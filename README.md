# EVE Tracking Meter

A small always-on-top overlay for **EVE Online** that shows the hit quality of every turret and missile shot in real time, as a vertical segmented bar.

It reads the game's own combat log files only. It does not read game memory, inject anything into the client, or change any game files.

[한국어 설명은 아래에 있습니다](#한국어)

## Quick start

1. Download the ZIP (green **Code** button → **Download ZIP**) and extract it
2. Double-click **`create_shortcut.bat`** — it puts an **EVE Tracking Meter** icon on your desktop
3. From now on, just double-click that desktop icon

(Python 3.9+ must be installed. See Requirements below.)

## Features

- Updates on every shot: the bar jumps to that shot's hit quality, the top label shows the hit text (WRECK, SMASH, HIT, GRAZE, MISS ...)
- Turrets and missiles only(altho missiles gonna always be shown as hit) . Drones and fighters are ignored
- Color coded: cyan = good, yellow = medium, red = poor
- Resizable, movable, borderless, always on top
- Finds the latest combat log automatically and keeps working when the log file changes
- No configuration needed

| Hit text | Bar height |
|---|---|
| Wrecks | 100% |
| Smashes | 90% |
| Penetrates | 75% |
| Hits | 60% |
| Glances Off | 40% |
| Grazes | 20% |
| Barely scratches | 10% |
| Miss | 0% |

Missile hits that have no hit-quality text are shown as a percentage of the best damage that missile has done to the same target.

## Requirements

- Windows
- Python 3.9 or newer (https://www.python.org, check **"Add python.exe to PATH"** during install). No extra packages needed (uses tkinter, included with Python)
- EVE combat logging enabled (on by default). Logs are read from `Documents\EVE\logs\Gamelogs`

## Usage

1. Download or clone this repository (if you downloaded the ZIP, extract it first)
2. Double-click `create_shortcut.bat` once. An **EVE Tracking Meter** shortcut with the meter icon appears on your desktop
3. Start the meter from that shortcut (or double-click `run_tracking_meter.bat`)
4. Run EVE in windowed or fixed-window mode so the overlay can sit on top

If you move the folder later, run `create_shortcut.bat` again.

| Control | Action |
|---|---|
| Left-drag | Move |
| Drag ◢ (bottom right) | Resize |
| Ctrl + mouse wheel | Scale |
| × (bottom left) | Close |

## Settings

Edit the values at the top of `eve_tracking_meter.py`:

- `HOLD_SEC` – how long the last shot stays on screen (0 = until the next shot)
- `CHARACTER` – read only this character's logs when you run several clients
- `WEAPON_KEYWORDS` – add part of a weapon name if one of your weapons is not picked up
- `QUALITY` – bar height and color for each hit text
- `DEBUG = True` – writes unrecognized combat lines to `debug_unmatched.txt`

## Notes

- EVE writes its log files in batches, so a short delay can remain.
- This is a fan-made tool and is not affiliated with or endorsed by CCP Games. Use it at your own discretion.

## License

[MIT](LICENSE)

---

## 한국어

**EVE Online**에서 터렛·미사일 사격의 명중 품질을 실시간으로 보여주는 세로 막대 오버레이입니다.

게임의 전투 로그 파일만 읽습니다. 게임 메모리를 읽거나, 클라이언트에 무언가를 주입하거나, 게임 파일을 바꾸지 않습니다.

### 빠른 시작

1. ZIP으로 내려받아(초록색 **Code** 버튼 → **Download ZIP**) 압축을 풉니다
2. **`create_shortcut.bat`** 를 더블클릭합니다 — 바탕화면에 **EVE Tracking Meter** 아이콘이 생깁니다
3. 앞으로는 바탕화면 아이콘만 더블클릭하면 됩니다

(Python 3.9 이상이 설치되어 있어야 합니다. 아래 필요 환경 참고)

### 기능

- 사격할 때마다 그 한 발의 명중 품질로 막대가 바뀌고, 위쪽에 명중 문구(WRECK, SMASH, HIT, GRAZE, MISS 등)가 표시됩니다
- 터렛과 미사일만 표시하며 드론·파이터는 제외합니다
- 색상: 청록 = 좋음, 노랑 = 보통, 빨강 = 나쁨
- 크기 조절·이동 가능, 테두리 없음, 항상 위에 표시
- 최신 전투 로그를 자동으로 찾고, 로그 파일이 바뀌어도 계속 동작합니다
- 별도 설정 없이 바로 사용 가능

### 필요 환경

- Windows
- Python 3.9 이상 (https://www.python.org, 설치 시 **"Add python.exe to PATH"** 체크). 추가 패키지 없음
- EVE 전투 로그 기록 켜짐 (기본값). `문서\EVE\logs\Gamelogs`에서 읽습니다

### 사용법

1. 이 저장소를 내려받습니다 (ZIP으로 받았다면 먼저 압축을 풉니다)
2. `create_shortcut.bat`를 한 번 더블클릭합니다. 바탕화면에 미터 아이콘이 붙은 **EVE Tracking Meter** 바로가기가 생깁니다
3. 그 바로가기로 실행합니다 (`run_tracking_meter.bat`를 직접 더블클릭해도 됩니다)
4. EVE를 창 모드 또는 전체 창 모드로 실행해야 오버레이가 게임 위에 보입니다

나중에 폴더를 옮기면 `create_shortcut.bat`를 다시 실행하십시오.

| 조작 | 동작 |
|---|---|
| 좌클릭 드래그 | 이동 |
| 우측 하단 ◢ 드래그 | 크기 조절 |
| Ctrl + 마우스 휠 | 비율 유지 확대·축소 |
| 좌측 하단 × | 종료 |

### 설정

`eve_tracking_meter.py` 상단의 값을 바꾸면 됩니다.

- `HOLD_SEC` – 마지막 사격 표시 유지 시간 (0 = 다음 사격까지 유지)
- `CHARACTER` – 여러 클라이언트를 쓸 때 특정 캐릭터 로그만 읽기
- `WEAPON_KEYWORDS` – 인식되지 않는 무기가 있으면 이름 일부를 추가
- `QUALITY` – 명중 문구별 막대 높이와 색
- `DEBUG = True` – 인식하지 못한 전투 로그를 `debug_unmatched.txt`에 기록

### 참고

- EVE가 로그 파일을 일정 간격으로 묶어서 기록하기 때문에 약간의 지연은 남을 수 있습니다.
- 팬이 만든 도구이며 CCP Games와 관련이 없고 공식 승인을 받지 않았습니다. 사용 여부는 본인이 판단하십시오.

### 라이선스

[MIT](LICENSE)
