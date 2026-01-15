import tkinter as tk
import random


class SnakeGame:
    def __init__(self, cell=20, w=30, h=20, speed_ms=110):
        self.cell = cell
        self.grid_w = w
        self.grid_h = h
        self.speed_ms = speed_ms

        self.root = tk.Tk()
        self.root.title("Змейка (tkinter)")

        self.canvas = tk.Canvas(self.root, width=self.grid_w*self.cell, height=self.grid_h*self.cell)
        self.canvas.pack()

        self.info = tk.Label(self.root, text="Стрелки: движение • R: рестарт • P: пауза", anchor="w")
        self.info.pack(fill="x")

        self.root.bind("<Up>", lambda e: self.set_dir(0, -1))
        self.root.bind("<Down>", lambda e: self.set_dir(0, 1))
        self.root.bind("<Left>", lambda e: self.set_dir(-1, 0))
        self.root.bind("<Right>", lambda e: self.set_dir(1, 0))
        self.root.bind("r", lambda e: self.restart())
        self.root.bind("R", lambda e: self.restart())
        self.root.bind("p", lambda e: self.toggle_pause())
        self.root.bind("P", lambda e: self.toggle_pause())

        self.paused = False
        self.after_id = None

        self.restart()

    def restart(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.canvas.delete("all")
        self.score = 0
        self.game_over = False
        self.paused = False

        midx = self.grid_w // 2
        midy = self.grid_h // 2

        self.snake = [(midx, midy), (midx-1, midy), (midx-2, midy)]
        self.dir = (1, 0)
        self.pending_dir = self.dir

        self.spawn_food()
        self.draw()
        self.tick()

    def toggle_pause(self):
        if self.game_over:
            return
        self.paused = not self.paused
        self.draw()

    def set_dir(self, dx, dy):
        if self.game_over:
            return
        # prevent reversing into itself
        cur_dx, cur_dy = self.dir
        if (dx, dy) == (-cur_dx, -cur_dy):
            return
        self.pending_dir = (dx, dy)

    def spawn_food(self):
        free = set((x, y) for x in range(self.grid_w) for y in range(self.grid_h)) - set(self.snake)
        self.food = random.choice(list(free)) if free else None

    def inside(self, x, y):
        return 0 <= x < self.grid_w and 0 <= y < self.grid_h

    def tick(self):
        if self.game_over:
            self.draw()
            return

        if self.paused:
            self.after_id = self.root.after(self.speed_ms, self.tick)
            return

        self.dir = self.pending_dir
        head_x, head_y = self.snake[0]
        dx, dy = self.dir
        nx, ny = head_x + dx, head_y + dy

        # collisions
        if not self.inside(nx, ny) or (nx, ny) in self.snake:
            self.game_over = True
            self.draw()
            return

        self.snake.insert(0, (nx, ny))

        if self.food and (nx, ny) == self.food:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()

        self.draw()
        self.after_id = self.root.after(self.speed_ms, self.tick)

    def draw_cell(self, x, y, kind):
        x1 = x * self.cell
        y1 = y * self.cell
        x2 = x1 + self.cell
        y2 = y1 + self.cell

        # no custom colors requested, keep defaults simple
        if kind == "snake":
            self.canvas.create_rectangle(x1, y1, x2, y2)
        elif kind == "head":
            self.canvas.create_rectangle(x1, y1, x2, y2, width=3)
        elif kind == "food":
            self.canvas.create_oval(x1+3, y1+3, x2-3, y2-3)

    def draw(self):
        self.canvas.delete("all")

        # food
        if self.food:
            self.draw_cell(self.food[0], self.food[1], "food")

        # snake
        for i, (x, y) in enumerate(self.snake):
            self.draw_cell(x, y, "head" if i == 0 else "snake")

        # HUD
        text = f"Score: {self.score}"
        if self.paused:
            text += " | PAUSE"
        if self.game_over:
            text += " | GAME OVER (нажми R)"
        self.canvas.create_text(8, 8, anchor="nw", text=text)

        # grid (optional, light)
        # Comment out if you want cleaner look
        for x in range(self.grid_w + 1):
            self.canvas.create_line(x*self.cell, 0, x*self.cell, self.grid_h*self.cell)
        for y in range(self.grid_h + 1):
            self.canvas.create_line(0, y*self.cell, self.grid_w*self.cell, y*self.cell)

    def run(self):
        self.root.resizable(False, False)
        self.root.mainloop()


if __name__ == "__main__":
    SnakeGame().run()