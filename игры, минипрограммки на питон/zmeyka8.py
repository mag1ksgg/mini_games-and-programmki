import tkinter as tk
import random
import time

# ---------------- НАСТРОЙКИ ----------------
CELL = 25
WIDTH = 20
HEIGHT = 16

WIN_W = WIDTH * CELL
WIN_H = HEIGHT * CELL + 80

SPEEDS = {
    "Медленно": 180,
    "Нормально": 120,
    "Быстро": 80,
    "Хардкор": 50
}

FRAME_MS = 16 # ~60 FPS

THEMES = [
    {
        "name": "Classic",
        "bg": "#111111",
        "head": "#6aff8f",
        "body": "#2ecc71",
        "food": "#ff4d4d",
        "ui": "lightgray",
        "text": "white"
    },
    {
        "name": "Neon Purple",
        "bg": "#0b0614",
        "head": "#b98cff",
        "body": "#7c3aed",
        "food": "#00f5d4",
        "ui": "#b8b8b8",
        "text": "white"
    },
    {
        "name": "Desert",
        "bg": "#2a1f14",
        "head": "#ffd166",
        "body": "#f4a261",
        "food": "#06d6a0",
        "ui": "#d0c7bd",
        "text": "white"
    },
    {
        "name": "Ice",
        "bg": "#081a24",
        "head": "#7dd3fc",
        "body": "#38bdf8",
        "food": "#fb7185",
        "ui": "#bcd5e6",
        "text": "white"
    },
]
# -------------------------------------------


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Змейка")

        self.canvas = tk.Canvas(root, width=WIN_W, height=WIN_H, bg="#111", highlightthickness=0)
        self.canvas.pack()

        self.speed_name = "Нормально"
        self.wall_kill = True

        self.running = False
        self.after_id = None

        self.paused = False
        self.game_over_flag = False

        # плавность
        self.last_frame_time = time.perf_counter()
        self.accum_ms = 0.0
        self.prev_snake = []

        # темы
        self.theme_idx = 0
        self.apply_theme()

        self.root.bind("<Key>", self.key_press)

        self.menu()
        self.animation_loop()

    # ---------------- ТЕМА ----------------
    def apply_theme(self):
        t = THEMES[self.theme_idx]
        self.canvas.configure(bg=t["bg"])

    def T(self):
        return THEMES[self.theme_idx]

    # ---------------- МЕНЮ ----------------
    def menu(self):
        self.canvas.delete("all")
        self.running = False

        self.paused = False
        self.game_over_flag = False

        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        t = self.T()

        self.canvas.create_text(WIN_W // 2, 40, text="ЗМЕЙКА",
                                fill=t["text"], font=("Arial", 28, "bold"))

        # Поменял направления стрелок в меню:
        # Скорость — ↑ ↓, Стены — ← →
        self.canvas.create_text(WIN_W // 2, 90,
                                text=f"Скорость: {self.speed_name} ↑ ↓",
                                fill=t["ui"], font=("Arial", 14))

        wall_text = "СМЕРТЬ ОТ СТЕН" if self.wall_kill else "ПРОХОД СКВОЗЬ СТЕНЫ"
        self.canvas.create_text(WIN_W // 2, 120,
                                text=f"Стены: {wall_text} ← →",
                                fill=t["ui"], font=("Arial", 14))

        self.canvas.create_text(WIN_W // 2, 150,
                                text=f"Локация: {t['name']} A D",
                                fill=t["ui"], font=("Arial", 14))

        self.canvas.create_text(WIN_W // 2, 190,
                                text="Enter — начать игру",
                                fill=t["text"], font=("Arial", 14))

        self.canvas.create_text(WIN_W // 2, 220,
                                text="ESC — выход",
                                fill="gray", font=("Arial", 12))

    # ---------------- ИГРА ----------------
    def start(self):
        self.canvas.delete("all")
        self.running = True

        self.paused = False
        self.game_over_flag = False
        self.canvas.delete("pause")

        self.dir = (1, 0)

        cx, cy = WIDTH // 2, HEIGHT // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.prev_snake = self.snake.copy()

        self.spawn_food()

        self.last_frame_time = time.perf_counter()
        self.accum_ms = 0.0

        self.draw_interpolated(0.0)

    def spawn_food(self):
        while True:
            pos = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
            if pos not in self.snake:
                self.food = pos
                break

    # ---- ЛОГИЧЕСКИЙ ШАГ (по клеткам) ----
    def logic_step(self):
        if not self.running or self.paused:
            return

        self.prev_snake = self.snake.copy()

        hx, hy = self.snake[0]
        dx, dy = self.dir
        nx, ny = hx + dx, hy + dy

        if self.wall_kill:
            if nx < 0 or nx >= WIDTH or ny < 0 or ny >= HEIGHT:
                self.game_over()
                return
        else:
            nx %= WIDTH
            ny %= HEIGHT

        new_head = (nx, ny)

        tail = self.snake[-1]
        will_grow = (new_head == self.food)
        body_to_check = self.snake if will_grow else self.snake[:-1]
        if new_head in body_to_check:
            self.game_over()
            return

        self.snake.insert(0, new_head)

        if will_grow:
            self.spawn_food()
        else:
            self.snake.pop()

        # выравниваем длины prev/curr
        if len(self.prev_snake) < len(self.snake):
            last = self.prev_snake[-1]
            while len(self.prev_snake) < len(self.snake):
                self.prev_snake.append(last)
        elif len(self.prev_snake) > len(self.snake):
            self.prev_snake = self.prev_snake[:len(self.snake)]

    # ---------------- ПЛАВНАЯ ОТРИСОВКА ----------------
    def cell_to_center(self, x, y):
        # x,y могут быть дробными/unwrap — в wrap режиме мы модим при переводе в пиксели
        px = ((x % WIDTH) + 0.5) * CELL
        py = ((y % HEIGHT) + 0.5) * CELL + 80
        return px, py

    def unwrap_pair(self, a, b, mod):
        """
        Делает так, чтобы переход a->b был "коротким" (в пределах примерно 1 клетки),
        добавляя/убавляя mod к b.
        """
        d = b - a
        if d > 1:
            b -= mod
        elif d < -1:
            b += mod
        return a, b

    def build_smooth_points(self, alpha):
        """
        Возвращает список точек (cx,cy) для сегментов змеи.
        В режиме "сквозь стены" используем unwrap, чтобы НЕ рисовалась линия через всю карту.
        """
        if not self.prev_snake or len(self.prev_snake) != len(self.snake):
            self.prev_snake = self.snake.copy()

        pts = []
        for (pxc, pyc), (cxc, cyc) in zip(self.prev_snake, self.snake):
            ax, bx = pxc, cxc
            ay, by = pyc, cyc

            if not self.wall_kill:
                ax, bx = self.unwrap_pair(ax, bx, WIDTH)
                ay, by = self.unwrap_pair(ay, by, HEIGHT)

            x = ax + (bx - ax) * alpha
            y = ay + (by - ay) * alpha
            pts.append((x, y))
        return pts

    def draw_interpolated(self, alpha):
        self.canvas.delete("game")
        t = self.T()

        # еда (круглая)
        fx, fy = self.food
        cx, cy = self.cell_to_center(fx, fy)
        r_food = CELL * 0.33
        self.canvas.create_oval(cx - r_food, cy - r_food, cx + r_food, cy + r_food,
                                fill=t["food"], outline="", tags="game")

        if not self.snake:
            return

        # соберём smooth точки (в клетках, возможно unwrap)
        spts = self.build_smooth_points(alpha)

        # переведём в пиксели
        ppts = [self.cell_to_center(x, y) for x, y in spts]

        # ---- ТЕЛО: рисуем несколькими кусками, если есть "перепрыгивание" через край ----
        # это окончательно убирает баг длинной змейки через всю карту
        body_w = max(6, CELL - 8)

        def dist(a, b):
            return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

        segments = []
        cur = [ppts[0]]
        for i in range(1, len(ppts)):
            if dist(ppts[i-1], ppts[i]) > CELL * 1.25: # разрыв (wrap)
                if len(cur) >= 2:
                    segments.append(cur)
                cur = [ppts[i]]
            else:
                cur.append(ppts[i])
        if len(cur) >= 2:
            segments.append(cur)

        for seg in segments:
            flat = []
            for x, y in seg:
                flat.extend([x, y])
            self.canvas.create_line(
                *flat,
                fill=t["body"],
                width=body_w,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
                smooth=True,
                splinesteps=12,
                tags="game"
            )

        # ---- ГОЛОВА ----
        hx, hy = ppts[0]
        r_head = CELL * 0.42
        self.canvas.create_oval(hx - r_head, hy - r_head, hx + r_head, hy + r_head,
                                fill=t["head"], outline="", tags="game")

        # глазки
        dx, dy = self.dir
        eye_shift = CELL * 0.12
        eye_r = CELL * 0.08
        px, py = -dy, dx
        ex1 = hx + dx * eye_shift + px * eye_shift
        ey1 = hy + dy * eye_shift + py * eye_shift
        ex2 = hx + dx * eye_shift - px * eye_shift
        ey2 = hy + dy * eye_shift - py * eye_shift
        self.canvas.create_oval(ex1 - eye_r, ey1 - eye_r, ex1 + eye_r, ey1 + eye_r,
                                fill=t["bg"], outline="", tags="game")
        self.canvas.create_oval(ex2 - eye_r, ey2 - eye_r, ex2 + eye_r, ey2 + eye_r,
                                fill=t["bg"], outline="", tags="game")

        # UI сверху
        self.canvas.create_text(10, 15, anchor="w",
                                text=f"Локация: {t['name']} | Скорость: {self.speed_name} | Длина: {len(self.snake)}",
                                fill=t["ui"], font=("Arial", 12), tags="game")

    def animation_loop(self):
        now = time.perf_counter()
        dt_ms = (now - self.last_frame_time) * 1000.0
        self.last_frame_time = now

        tick_ms = SPEEDS[self.speed_name]

        if self.running and not self.game_over_flag:
            if not self.paused:
                self.accum_ms += dt_ms

                max_catchup = 6
                steps = 0
                while self.accum_ms >= tick_ms and steps < max_catchup:
                    self.logic_step()
                    self.accum_ms -= tick_ms
                    steps += 1

                alpha = 0.0 if tick_ms <= 0 else (self.accum_ms / tick_ms)
                alpha = max(0.0, min(1.0, alpha))
                self.draw_interpolated(alpha)
            else:
                self.draw_interpolated(0.0)

        self.root.after(FRAME_MS, self.animation_loop)

    def game_over(self):
        self.running = False
        self.paused = False
        self.game_over_flag = True

        t = self.T()
        self.canvas.delete("pause")
        self.canvas.create_text(
            WIN_W // 2, WIN_H // 2,
            text="GAME OVER\nR — заново\nESC — меню",
            fill=t["text"], font=("Arial", 22), justify="center", tags="pause"
        )

    # ---------------- КЛАВИШИ ----------------
    def key_press(self, e):
        # --- когда не в игре ---
        if not self.running:
            if self.game_over_flag:
                if e.keysym.lower() == "r" or e.keysym == "Return":
                    self.start()
                elif e.keysym == "Escape":
                    self.menu()
                return

            if e.keysym == "Return":
                self.start()
            elif e.keysym == "Escape":
                self.root.destroy()

            # в меню: скорость теперь ↑ ↓
            elif e.keysym in ("Up", "Down"):
                names = list(SPEEDS.keys())
                i = names.index(self.speed_name)
                self.speed_name = names[(i + (1 if e.keysym == "Down" else -1)) % len(names)]
                self.menu()

            # в меню: стены теперь ← →
            elif e.keysym in ("Left", "Right"):
                self.wall_kill = not self.wall_kill
                self.menu()

            # в меню: тема A/D
            elif e.keysym.lower() == "a":
                self.theme_idx = (self.theme_idx - 1) % len(THEMES)
                self.apply_theme()
                self.menu()
            elif e.keysym.lower() == "d":
                self.theme_idx = (self.theme_idx + 1) % len(THEMES)
                self.apply_theme()
                self.menu()

            return

        # --- в игре ---
        if e.keysym.lower() == "p":
            self.paused = not self.paused
            if self.paused:
                t = self.T()
                self.canvas.delete("pause")
                self.canvas.create_text(
                    WIN_W // 2, WIN_H // 2,
                    text="ПАУЗА\nНажми P",
                    fill=t["text"], font=("Arial", 22),
                    justify="center", tags="pause"
                )
            else:
                self.canvas.delete("pause")
            return

        # поворот по клеткам (логика), движение плавное (рендер)
        if e.keysym in ("w", "Up") and self.dir != (0, 1):
            self.dir = (0, -1)
        elif e.keysym in ("s", "Down") and self.dir != (0, -1):
            self.dir = (0, 1)
        elif e.keysym in ("a", "Left") and self.dir != (1, 0):
            self.dir = (-1, 0)
        elif e.keysym in ("d", "Right") and self.dir != (-1, 0):
            self.dir = (1, 0)
        elif e.keysym.lower() == "r":
            self.start()
        elif e.keysym == "Escape":
            self.menu()


# ---------------- ЗАПУСК ----------------
root = tk.Tk()
game = SnakeGame(root)
root.mainloop()