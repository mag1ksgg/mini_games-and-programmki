import tkinter as tk
import random

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

# -------------------------------------------

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Змейка")

        self.canvas = tk.Canvas(root, width=WIN_W, height=WIN_H, bg="#111")
        self.canvas.pack()

        self.speed_name = "Нормально"
        self.wall_kill = True

        self.running = False
        self.after_id = None

        # ---- ДОБАВЛЕНО: состояния паузы и game over ----
        self.paused = False
        self.game_over_flag = False

        self.root.bind("<Key>", self.key_press)

        self.menu()

    # ---------------- МЕНЮ ----------------
    def menu(self):
        self.canvas.delete("all")
        self.running = False

        # ---- ДОБАВЛЕНО: сброс и отмена тиков ----
        self.paused = False
        self.game_over_flag = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.canvas.create_text(WIN_W//2, 40, text="ЗМЕЙКА",
                                fill="white", font=("Arial", 28, "bold"))

        self.canvas.create_text(WIN_W//2, 90,
            text=f"Скорость: {self.speed_name} ← →",
            fill="lightgray", font=("Arial", 14))

        wall_text = "СМЕРТЬ ОТ СТЕН" if self.wall_kill else "ПРОХОД СКВОЗЬ СТЕНЫ"
        self.canvas.create_text(WIN_W//2, 120,
            text=f"Стены: {wall_text} ↑ ↓",
            fill="lightgray", font=("Arial", 14))

        self.canvas.create_text(WIN_W//2, 170,
            text="Enter — начать игру",
            fill="white", font=("Arial", 14))

        self.canvas.create_text(WIN_W//2, 200,
            text="ESC — выход",
            fill="gray", font=("Arial", 12))

    # ---------------- ИГРА ----------------
    def start(self):
        self.canvas.delete("all")
        self.running = True

        # ---- ДОБАВЛЕНО: сброс паузы и game over ----
        self.paused = False
        self.game_over_flag = False
        self.canvas.delete("pause")

        # ---- ДОБАВЛЕНО: на всякий случай отменяем старый тик ----
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.dir = (1, 0)

        cx, cy = WIDTH // 2, HEIGHT // 2
        self.snake = [(cx, cy), (cx-1, cy), (cx-2, cy)]
        self.spawn_food()
        self.draw()
        self.step()

    def spawn_food(self):
        while True:
            pos = (random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1))
            if pos not in self.snake:
                self.food = pos
                break

    def step(self):
        if not self.running:
            return

        # ---- ДОБАВЛЕНО: пауза (змейка не двигается) ----
        if self.paused:
            self.after_id = self.root.after(SPEEDS[self.speed_name], self.step)
            return

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

        if new_head in self.snake:
            self.game_over()
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.spawn_food()
        else:
            self.snake.pop()

        self.draw()
        self.after_id = self.root.after(SPEEDS[self.speed_name], self.step)

    def draw(self):
        self.canvas.delete("game")

        # еда
        fx, fy = self.food
        self.draw_cell(fx, fy, "red")

        # змейка
        for i, (x, y) in enumerate(self.snake):
            color = "#6aff8f" if i == 0 else "#2ecc71"
            self.draw_cell(x, y, color)

    def draw_cell(self, x, y, color):
        px = x * CELL
        py = y * CELL + 80
        self.canvas.create_rectangle(
            px, py, px+CELL, py+CELL,
            fill=color, outline="#111", tags="game"
        )

    def game_over(self):
        # ---- ИЗМЕНЕНО: игра не закрывается, ждём R ----
        self.running = False
        self.paused = False
        self.game_over_flag = True

        # ---- ДОБАВЛЕНО: отменяем запланированный тик ----
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.canvas.delete("pause")
        self.canvas.create_text(
            WIN_W//2, WIN_H//2,
            text="GAME OVER\nR — заново\nESC — меню",
            fill="white", font=("Arial", 22), justify="center"
        )

    # ---------------- КЛАВИШИ ----------------
    def key_press(self, e):
        if not self.running:
            # ---- ДОБАВЛЕНО: если Game Over — ждём R/Enter ----
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
            elif e.keysym in ("Left", "Right"):
                names = list(SPEEDS.keys())
                i = names.index(self.speed_name)
                self.speed_name = names[(i + (1 if e.keysym == "Right" else -1)) % len(names)]
                self.menu()
            elif e.keysym in ("Up", "Down"):
                self.wall_kill = not self.wall_kill
                self.menu()
            return

        # ---- ДОБАВЛЕНО: пауза на P ----
        if e.keysym.lower() == "p":
            self.paused = not self.paused
            if self.paused:
                self.canvas.delete("pause")
                self.canvas.create_text(
                    WIN_W//2, WIN_H//2,
                    text="ПАУЗА\nНажми P",
                    fill="white", font=("Arial", 22),
                    justify="center", tags="pause"
                )
            else:
                self.canvas.delete("pause")
            return

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