"""
EVE Online 트래킹(명중 품질) 미터 - 세로 분할 막대 오버레이

- 전투 로그의 명중 품질 문구로 동작합니다. 별도 설정이 필요 없습니다.
- 터렛 + 미사일 사격만 표시합니다. (드론, 파이터 제외)
- 평균 없이, 매 사격마다 그 한 발의 명중 품질을 실시간으로 표시합니다.
- 막대: 마지막 사격의 명중 품질
- 상단: 마지막 사격의 명중 품질 문구

조작:
  좌클릭 드래그          : 위치 이동
  우측 하단 ◢ 드래그     : 창 크기 조절
  Ctrl + 마우스 휠       : 창 크기 비율 조절
  좌측 하단 × 클릭       : 종료
"""

import os
import re
import time
import queue
import threading
import traceback
import collections
import tkinter as tk

# ===================== 설정 =====================
SEGMENTS = 40           # 세그먼트 개수
CHARACTER = ""          # 특정 캐릭터 로그만 읽을 경우 캐릭터 이름 입력 (비우면 최근 로그 전체)
HOLD_SEC = 6            # 마지막 사격 표시 유지 시간(초). 이후 막대가 비워짐 (0이면 계속 유지)

COLOR_OFF = "#1c2626"   # 꺼진 세그먼트
BG = "#101414"          # 배경

BAR_WIDTH = 34          # 시작 막대 너비
BAR_HEIGHT = 320        # 시작 막대 높이
MIN_WIDTH = 14
MIN_HEIGHT = 80
READ_INTERVAL = 0.03    # 로그 읽기 주기(초) - 백그라운드 스레드
UI_MS = 30              # 화면 갱신 주기(ms)
FILE_CHECK_SEC = 2      # 새 로그 파일 확인 주기(초)
TAIL_FILES = 4          # 동시에 감시할 최근 로그 파일 수
MISSILE_REF_SAMPLES = 30  # 품질 문구 없는 사격(미사일)의 기준 샘플 수

DEBUG = False           # True: 인식하지 못한 전투 로그를 debug_unmatched.txt에 기록

# 표시할 무기 이름 키워드 (하나라도 포함되면 표시, 드론은 포함되지 않음)
WEAPON_KEYWORDS = [
    # 터렛
    "Laser", "Beam", "Pulse", "Blaster", "Railgun", "Rail", "AutoCannon",
    "Artillery", "Howitzer", "Cannon", "Carbine", "Gatling", "Disintegrator",
    "Accelerator", "Projector",
    # 미사일 (로그에는 탄약 이름으로 기록됨)
    "Missile", "Rocket", "Torpedo", "Launcher",
]
# =================================================

COLOR_TOP = "#7ff5ff"
COLOR_GOOD = "#2fe3c8"
COLOR_MID = "#e3c42f"
COLOR_BAD = "#e3553f"

# 명중 품질 → 막대 높이(0~1), 표시 문자, 색
QUALITY = {
    "wrecks":           (1.00, "WRECK", COLOR_TOP),
    "smashes":          (0.90, "SMASH", COLOR_GOOD),
    "penetrates":       (0.75, "PENE",  COLOR_GOOD),
    "hits":             (0.60, "HIT",   COLOR_MID),
    "glances off":      (0.40, "GLNC",  COLOR_MID),
    "grazes":           (0.20, "GRAZE", COLOR_BAD),
    "barely scratches": (0.10, "SCRT",  COLOR_BAD),
    "miss":             (0.00, "MISS",  COLOR_BAD),
}

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
HIT_HEAD_RE = re.compile(r"\(combat\)\s+(\d+)\s+to\s+(.+)$")
MISS_RE = re.compile(r"\(combat\)\s+Your\s+(?:group of\s+)?(.+?)\s+misses\s+(.+?)\s+completely", re.I)
LISTENER_RE = re.compile(r"Listener:\s*(.+)")
FILE_TS_RE = re.compile(r"(\d{8}_\d{6})")
WEAPON_RE = re.compile("|".join(re.escape(k) for k in WEAPON_KEYWORDS), re.I)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def is_tracked_weapon(weapon):
    return bool(WEAPON_RE.search(weapon))


def value_color(v):
    if v >= 0.7:
        return COLOR_GOOD
    if v >= 0.45:
        return COLOR_MID
    return COLOR_BAD


def debug_write(text):
    if not DEBUG:
        return
    try:
        with open(os.path.join(SCRIPT_DIR, "debug_unmatched.txt"), "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except OSError:
        pass


def find_log_dir():
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "Documents", "EVE", "logs", "Gamelogs"),
        os.path.join(home, "OneDrive", "Documents", "EVE", "logs", "Gamelogs"),
        os.path.join(home, "OneDrive", "문서", "EVE", "logs", "Gamelogs"),
        os.path.join(home, "문서", "EVE", "logs", "Gamelogs"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def log_character(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(10):
                m = LISTENER_RE.search(f.readline())
                if m:
                    return m.group(1).strip()
    except OSError:
        pass
    return None


def recent_logs(log_dir, count):
    """파일 이름의 생성 시각(YYYYMMDD_HHMMSS) 기준으로 최근 로그 탐색"""
    entries = []
    try:
        with os.scandir(log_dir) as it:
            for e in it:
                if e.is_file() and e.name.endswith(".txt"):
                    m = FILE_TS_RE.search(e.name)
                    key = m.group(1) if m else ""
                    entries.append((key, e.name, e.path))
    except OSError:
        return []
    entries.sort(reverse=True)
    result = []
    for _, _, p in entries:
        if CHARACTER and log_character(p) != CHARACTER:
            continue
        result.append(p)
        if len(result) >= count:
            break
    return result


class TailFile:
    def __init__(self, path):
        self.path = path
        self.file = open(path, "rb")
        self.file.seek(0, os.SEEK_END)
        self.pos = self.file.tell()
        self.buffer = b""

    def read_lines(self):
        try:
            size = os.path.getsize(self.path)
        except OSError:
            return []
        if size < self.pos:  # 파일이 재생성/잘린 경우
            self.file.seek(0)
            self.pos = 0
            self.buffer = b""
        if size == self.pos:
            return []
        self.file.seek(self.pos)
        data = self.file.read(size - self.pos)
        self.pos += len(data)
        if not data:
            return []
        self.buffer += data
        parts = self.buffer.split(b"\n")
        self.buffer = parts.pop()
        return [p.decode("utf-8", errors="ignore").strip() for p in parts]

    def close(self):
        try:
            self.file.close()
        except OSError:
            pass


class LogReader(threading.Thread):
    """백그라운드에서 최근 로그 여러 개를 읽어 터렛/미사일 사격만 큐로 전달"""

    def __init__(self, log_dir, out_queue, status_queue):
        super().__init__(daemon=True)
        self.log_dir = log_dir
        self.q = out_queue
        self.status = status_queue
        self.tails = {}
        self.last_check = 0.0

    def _refresh_files(self):
        now = time.time()
        if self.tails and now - self.last_check < FILE_CHECK_SEC:
            return
        self.last_check = now
        wanted = recent_logs(self.log_dir, TAIL_FILES)
        for p in list(self.tails):
            if p not in wanted:
                self.tails.pop(p).close()
        for p in wanted:
            if p not in self.tails:
                try:
                    self.tails[p] = TailFile(p)
                except OSError:
                    pass

    def _parse(self, line, now):
        if "(combat)" not in line:
            return
        text = SPACE_RE.sub(" ", TAG_RE.sub("", line)).strip()

        m = HIT_HEAD_RE.search(text)
        if m:
            dmg = int(m.group(1))
            parts = [s.strip() for s in m.group(2).split(" - ")]
            quality = None
            if len(parts) >= 2 and parts[-1].lower() in QUALITY:
                quality = parts.pop().lower()
            if len(parts) < 2:
                debug_write("[형식] " + text)
                return
            weapon = parts[-1]
            target = " - ".join(parts[:-1])
            if not is_tracked_weapon(weapon):
                return
            self.q.put((now, weapon, target, dmg, quality))
            return

        m = MISS_RE.search(text)
        if m:
            weapon = m.group(1).strip()
            if is_tracked_weapon(weapon):
                self.q.put((now, weapon, m.group(2).strip(), 0, "miss"))
            return

        if " to " in text or "misses" in text:
            debug_write("[미인식] " + text)

    def run(self):
        while True:
            try:
                self._refresh_files()
                now = time.time()
                for t in list(self.tails.values()):
                    for line in t.read_lines():
                        self._parse(line, now)
            except Exception:
                # 어떤 오류가 나도 스레드가 멈추지 않도록 처리
                self.status.put("ERR")
                debug_write("[오류] " + traceback.format_exc())
                for t in self.tails.values():
                    t.close()
                self.tails = {}
                time.sleep(0.5)
            time.sleep(READ_INTERVAL)


class ShotTracker:
    """마지막 사격 한 발의 명중 품질만 보관 (평균 없음)"""

    def __init__(self):
        self.missile_ref = collections.defaultdict(
            lambda: collections.deque(maxlen=MISSILE_REF_SAMPLES))
        self.value = None
        self.quality = None
        self.time = 0.0

    def add(self, now, weapon, target, dmg, q):
        if q:
            value = QUALITY[q][0]
        else:
            # 품질 문구가 없는 사격(미사일): 같은 미사일·대상 최대 적용치 대비 비율
            ref = self.missile_ref[(weapon, target)]
            ref.append(dmg)
            top = max(ref)
            value = dmg / top if top > 0 else 0.0
        self.value = value
        self.quality = q
        self.time = now


class Meter:
    def __init__(self, root, log_dir):
        self.root = root
        self.q = queue.Queue()
        self.status_q = queue.Queue()
        self.tracker = ShotTracker()
        self.has_log = bool(log_dir)
        self.bar_w = BAR_WIDTH
        self.bar_h = BAR_HEIGHT
        self.err_until = 0.0

        if log_dir:
            LogReader(log_dir, self.q, self.status_q).start()

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", 0.92)
        except tk.TclError:
            pass
        root.configure(bg=BG)

        self.top_label = tk.Label(root, text="--", fg="#5f7373", bg=BG)
        self.top_label.pack(fill="x", pady=(4, 2))

        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=1,
                                highlightbackground="#2a3636")
        self.canvas.pack(padx=6)

        bottom = tk.Frame(root, bg=BG)
        bottom.pack(fill="x", pady=(2, 2))
        self.close_btn = tk.Label(bottom, text="×", fg="#4a5c5c", bg=BG,
                                  cursor="hand2", font=("Consolas", 9, "bold"))
        self.close_btn.pack(side="left", anchor="sw")
        self.close_btn.bind("<Button-1>", lambda e: root.destroy())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(fg=COLOR_BAD))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(fg="#4a5c5c"))

        self.grip = tk.Label(bottom, text="◢", fg="#4a5c5c", bg=BG,
                             cursor="size_nw_se", font=("Consolas", 8))
        self.grip.pack(side="right", anchor="se")

        self.rects = []
        self.last_lit = -1
        self.last_color = None
        self._build_bar()

        for w in (root, self.top_label, self.canvas, bottom):
            w.bind("<ButtonPress-1>", self._start_move)
            w.bind("<B1-Motion>", self._on_move)
        for w in (root, self.top_label, self.canvas, bottom, self.grip):
            w.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
            w.bind("<Control-Button-4>", lambda e: self._scale(1.1))
            w.bind("<Control-Button-5>", lambda e: self._scale(1 / 1.1))

        self.grip.bind("<ButtonPress-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._on_resize)

        if not log_dir:
            self.top_label.config(text="로그X", fg=COLOR_BAD)

        self.update()

    # ---------- 막대 생성 / 크기 ----------
    def _build_bar(self):
        self.canvas.config(width=self.bar_w, height=self.bar_h)
        self.canvas.delete("all")
        gap = max(1, round(self.bar_h / 160))
        pad = max(2, round(self.bar_w / 9))
        seg_h = (self.bar_h - gap) / SEGMENTS
        self.rects = []
        for i in range(SEGMENTS):
            y2 = self.bar_h - gap - i * seg_h
            y1 = y2 - seg_h + gap
            self.rects.append(self.canvas.create_rectangle(
                pad, y1, self.bar_w - pad + 1, y2, fill=COLOR_OFF, width=0))
        fsize = max(7, min(16, round(self.bar_w / 3.8)))
        self.top_label.config(font=("Consolas", fsize, "bold"))
        self.last_lit = -1

    def _set_size(self, w, h):
        w = max(MIN_WIDTH, int(w))
        h = max(MIN_HEIGHT, int(h))
        if (w, h) != (self.bar_w, self.bar_h):
            self.bar_w, self.bar_h = w, h
            self._build_bar()

    def _scale(self, factor):
        self._set_size(self.bar_w * factor, self.bar_h * factor)

    def _on_ctrl_wheel(self, e):
        self._scale(1.1 if e.delta > 0 else 1 / 1.1)

    def _start_resize(self, e):
        self._rx, self._ry = e.x_root, e.y_root
        self._rw, self._rh = self.bar_w, self.bar_h

    def _on_resize(self, e):
        self._set_size(self._rw + (e.x_root - self._rx),
                       self._rh + (e.y_root - self._ry))

    # ---------- 이동 ----------
    def _start_move(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _on_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    # ---------- 갱신 ----------
    def update(self):
        try:
            self._update()
        except Exception:
            debug_write("[UI 오류] " + traceback.format_exc())
        self.root.after(UI_MS, self.update)

    def _draw(self, value, color):
        lit = round(max(0.0, min(value, 1.0)) * SEGMENTS)
        if lit != self.last_lit or color != self.last_color:
            for i, r in enumerate(self.rects):
                self.canvas.itemconfig(r, fill=color if i < lit else COLOR_OFF)
            self.last_lit, self.last_color = lit, color

    def _update(self):
        now = time.time()
        while True:
            try:
                self.tracker.add(*self.q.get_nowait())
            except queue.Empty:
                break
        while True:
            try:
                self.status_q.get_nowait()
                self.err_until = now + 1.5
            except queue.Empty:
                break

        t = self.tracker
        active = t.value is not None and (HOLD_SEC <= 0 or now - t.time < HOLD_SEC)

        if active:
            if t.quality in QUALITY:
                _, txt, color = QUALITY[t.quality]
            else:
                color = value_color(t.value)
                txt = f"{int(round(t.value * 100))}%"
            self._draw(t.value, color)
        else:
            self._draw(0.0, COLOR_OFF)

        if not self.has_log:
            return
        if now < self.err_until:
            self.top_label.config(text="RETRY", fg=COLOR_BAD)
        elif active:
            self.top_label.config(text=txt, fg=color)
        else:
            self.top_label.config(text="--", fg="#5f7373")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("EVE Tracking Meter")
    Meter(root, find_log_dir())
    root.geometry("+100+200")
    root.mainloop()
