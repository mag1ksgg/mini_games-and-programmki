import tkinter as tk
from tkinter import messagebox
import random
import time
from collections import deque

MINE = -1

MODES = {
    "Лёгкий (9x9, 10 мин)": (9, 9, 10),
    "Средний (16x16, 40 мин)": (16, 16, 40),
    "Сложный (16x30, 99 мин)": (16, 30, 99),
}

NUMBER_COLORS = {
    1: "#1e4ed8", # blue
    2: "#15803d", # green
    3: "#dc2626", # red
    4: "#4c1d95", # purple
    5: "#7f1d1d", # dark red
    6: "#0e7490", # teal
    7: "#111827", # almost black
    8: "#374151", # gray
}

def in_bounds(r, c, h, w):
    return 0 <= r < h and 0 <= c < w

def neighbors(r, c, h, w):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc, h, w):
                yield nr, nc

class MinesweeperApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Minesweeper (tkinter)")
        self.root.resizable(False, False)

        # State
        self.h = 9
        self.w = 9
        self.mines = 10
        self.first_click = True
        self.game_over = False
        self.flags_count = 0
        self.opened_count = 0

        self.field = []
        self.visible = []
        self.flags = []
        self.buttons = []

        # Timer
        self.start_time = None
        self.timer_running = False
        self.timer_after_id = None

        self._build_ui()
        self.new_game(*MODES["Лёгкий (9x9, 10 мин)"])

    def _build_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Игра", menu=game_menu)

        modes_menu = tk.Menu(game_menu, tearoff=0)
        game_menu.add_cascade(label="Режим", menu=modes_menu)

        for label, (h, w, m) in MODES.items():
            modes_menu.add_command(
                label=label,
                command=lambda hh=h, ww=w, mm=m: self.new_game(hh, ww, mm)
            )

        game_menu.add_separator()
        game_menu.add_command(label="Новая игра", command=lambda: self.new_game(self.h, self.w, self.mines))
        game_menu.add_command(label="Выход", command=self.root.destroy)
        self.root.config(menu=menubar)

        # Top panel
        top = tk.Frame(self.root, padx=10, pady=8)
        top.pack(fill="x")

        # Mine counter
        self.mines_var = tk.StringVar(value="000")
        mines_box = tk.Label(
            top, textvariable=self.mines_var, width=5,
            font=("Consolas", 16, "bold"),
            bg="#111827", fg="#f9fafb", padx=8, pady=4
        )
        mines_box.pack(side="left")

        # Reset button (smiley)
        self.reset_btn = tk.Button(
            top, text="🙂", font=("Segoe UI Emoji", 16),
            width=3, command=lambda: self.new_game(self.h, self.w, self.mines)
        )
        self.reset_btn.pack(side="left", expand=True)

        # Timer
        self.time_var = tk.StringVar(value="000")
        time_box = tk.Label(
            top, textvariable=self.time_var, width=5,
            font=("Consolas", 16, "bold"),
            bg="#111827", fg="#f9fafb", padx=8, pady=4
        )
        time_box.pack(side="right")

        # Board frame
        self.board_frame = tk.Frame(self.root, padx=10, pady=10, bg="#e5e7eb")
        self.board_frame.pack()

        # Help footer
        footer = tk.Label(
            self.root,
            text="ЛКМ — открыть | ПКМ — флаг | Первый клик безопасный (и 3×3 вокруг).",
            fg="#374151", pady=6
        )
        footer.pack(fill="x")

    def _reset_arrays(self):
        self.field = [[0 for _ in range(self.w)] for _ in range(self.h)]
        self.visible = [[False for _ in range(self.w)] for _ in range(self.h)]
        self.flags = [[False for _ in range(self.w)] for _ in range(self.h)]
        self.buttons = [[None for _ in range(self.w)] for _ in range(self.h)]

    def _destroy_board(self):
        for child in self.board_frame.winfo_children():
            child.destroy()

    def new_game(self, h, w, mines):
        # Stop timer
        self._stop_timer()

        self.h, self.w, self.mines = h, w, mines
        self.first_click = True
        self.game_over = False
        self.flags_count = 0
        self.opened_count = 0
        self.start_time = None

        self.reset_btn.config(text="🙂")
        self.time_var.set("000")
        self._update_mines_counter()

        self._reset_arrays()
        self._destroy_board()
        self._build_board_buttons()

    def _build_board_buttons(self):
        # Slight “3D” look: raised buttons, nice padding
        for r in range(self.h):
            for c in range(self.w):
                btn = tk.Button(
                    self.board_frame,
                    text="",
                    width=2,
                    height=1,
                    font=("Segoe UI", 12, "bold"),
                    relief="raised",
                    bd=2,
                    bg="#d1d5db",
                    activebackground="#cbd5e1"
                )
                btn.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")

                # Bind clicks
                btn.bind("<Button-1>", lambda e, rr=r, cc=c: self.on_left_click(rr, cc))
                btn.bind("<Button-3>", lambda e, rr=r, cc=c: self.on_right_click(rr, cc))

                self.buttons[r][c] = btn

        # Make grid uniform
        for r in range(self.h):
            self.board_frame.grid_rowconfigure(r, weight=1)
        for c in range(self.w):
            self.board_frame.grid_columnconfigure(c, weight=1)

    def _update_mines_counter(self):
        remaining = max(0, self.mines - self.flags_count)
        self.mines_var.set(f"{remaining:03d}")

    def _start_timer(self):
        if self.timer_running:
            return
        self.timer_running = True
        self.start_time = time.time()
        self._tick_timer()

    def _stop_timer(self):
        self.timer_running = False
        if self.timer_after_id is not None:
            try:
                self.root.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

    def _tick_timer(self):
        if not self.timer_running or self.game_over or self.start_time is None:
            return
        elapsed = int(time.time() - self.start_time)
        elapsed = min(elapsed, 999)
        self.time_var.set(f"{elapsed:03d}")
        self.timer_after_id = self.root.after(250, self._tick_timer)

    def _place_mines_and_numbers(self, safe_r, safe_c):
        """
        Place mines, avoiding a 3x3 safe zone around (safe_r, safe_c).
        """
        forbidden = set()
        forbidden.add((safe_r, safe_c))
        for nr, nc in neighbors(safe_r, safe_c, self.h, self.w):
            forbidden.add((nr, nc))

        cells = [(r, c) for r in range(self.h) for c in range(self.w) if (r, c) not in forbidden]
        random.shuffle(cells)
        mine_cells = set(cells[:self.mines])

        for r, c in mine_cells:
            self.field[r][c] = MINE

        for r in range(self.h):
            for c in range(self.w):
                if self.field[r][c] == MINE:
                    continue
                cnt = 0
                for nr, nc in neighbors(r, c, self.h, self.w):
                    if self.field[nr][nc] == MINE:
                        cnt += 1
                self.field[r][c] = cnt

    def on_left_click(self, r, c):
        if self.game_over:
            return
        if self.flags[r][c]:
            return
        if self.visible[r][c]:
            return

        if self.first_click:
            self._place_mines_and_numbers(r, c)
            self.first_click = False
            self._start_timer()

        if self.field[r][c] == MINE:
            self._lose(r, c)
            return

        self._open_cell_or_flood(r, c)

        if self._check_win():
            self._win()

    def on_right_click(self, r, c):
        if self.game_over:
            return
        if self.visible[r][c]:
            return

        self.flags[r][c] = not self.flags[r][c]
        if self.flags[r][c]:
            self.flags_count += 1
            self.buttons[r][c].config(text="🚩", fg="#111827")
        else:
            self.flags_count -= 1
            self.buttons[r][c].config(text="", fg="#111827")

        self._update_mines_counter()

        if not self.first_click and self._check_win():
            self._win()

    def _open_cell_or_flood(self, r, c):
        """
        Open this cell; if it is 0, flood fill open all connected zeros and their borders.
        """
        q = deque()
        q.append((r, c))

        while q:
            cr, cc = q.popleft()
            if self.visible[cr][cc] or self.flags[cr][cc]:
                continue

            self.visible[cr][cc] = True
            self.opened_count += 1

            btn = self.buttons[cr][cc]
            btn.config(relief="sunken", bd=1, bg="#f3f4f6", activebackground="#f3f4f6")

            val = self.field[cr][cc]
            if val == 0:
                btn.config(text="")
                for nr, nc in neighbors(cr, cc, self.h, self.w):
                    if not self.visible[nr][nc] and not self.flags[nr][nc]:
                        q.append((nr, nc))
            else:
                btn.config(text=str(val), fg=NUMBER_COLORS.get(val, "#111827"))

    def _reveal_all(self, exploded_at=None):
        for r in range(self.h):
            for c in range(self.w):
                btn = self.buttons[r][c]
                val = self.field[r][c]
                if val == MINE:
                    if exploded_at == (r, c):
                        btn.config(text="💥", bg="#fecaca", relief="sunken", bd=1)
                    else:
                        btn.config(text="💣", bg="#e5e7eb", relief="sunken", bd=1)
                else:
                    if not self.visible[r][c]:
                        self.visible[r][c] = True
                        btn.config(relief="sunken", bd=1, bg="#f3f4f6", activebackground="#f3f4f6")
                    if val == 0:
                        btn.config(text="")
                    else:
                        btn.config(text=str(val), fg=NUMBER_COLORS.get(val, "#111827"))

    def _lose(self, r, c):
        self.game_over = True
        self._stop_timer()
        self.reset_btn.config(text="😵")
        self._reveal_all(exploded_at=(r, c))
        messagebox.showinfo("Поражение", "Бум 💥 Ты попал на мину!")

    def _win(self):
        self.game_over = True
        self._stop_timer()
        self.reset_btn.config(text="😎")

        # Auto-flag all mines for nice finish
        for r in range(self.h):
            for c in range(self.w):
                if self.field[r][c] == MINE and not self.flags[r][c]:
                    self.flags[r][c] = True
                    self.flags_count += 1
                    self.buttons[r][c].config(text="🚩")
        self._update_mines_counter()

        messagebox.showinfo("Победа", "Красавчик 😎 Все мины обезврежены!")

    def _check_win(self):
        """
        Win if all non-mine cells are opened.
        """
        if self.first_click:
            return False
        total_cells = self.h * self.w
        non_mines = total_cells - self.mines
        return self.opened_count == non_mines

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MinesweeperApp()
    app.run()