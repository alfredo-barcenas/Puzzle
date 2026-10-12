"""
8-Puzzle Game — Juego del 8 Puzzle
Interfaz gráfica moderna con tkinter.
Incluye: temporizador, contador de movimientos, resolver automático (A*), animaciones.
"""

import tkinter as tk
from tkinter import messagebox
import random
import time
import heapq
from copy import deepcopy


# ─────────────────────────────────────────────
#  Paleta de colores
# ─────────────────────────────────────────────
BG_DARK       = "#0f0f1a"
BG_CARD       = "#1a1a2e"
BG_PANEL      = "#16213e"
ACCENT_BLUE   = "#0f3460"
ACCENT_PURPLE = "#533483"
TILE_BG       = "#e94560"
TILE_HOVER    = "#ff6b6b"
TILE_TEXT     = "#ffffff"
EMPTY_BG      = "#1a1a2e"
BORDER_COLOR  = "#533483"
TEXT_MAIN     = "#eaeaea"
TEXT_DIM      = "#888aaa"
BTN_GREEN     = "#00b894"
BTN_BLUE      = "#0984e3"
BTN_ORANGE    = "#e17055"
BTN_PURPLE    = "#6c5ce7"

GOAL_STATE = [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 0]]  # 0 = espacio vacio

TILE_SIZE   = 110   # tamano de cada celda en px
TILE_GAP    = 8
GRID_OFFSET = 20
ANIM_STEPS  = 8     # pasos de animacion por movimiento


# ─────────────────────────────────────────────
#  Logica del puzzle (sin GUI)
# ─────────────────────────────────────────────
def find_blank(state):
    for r in range(3):
        for c in range(3):
            if state[r][c] == 0:
                return r, c

def is_solvable(flat):
    """Cuenta inversiones para determinar si el puzzle es resoluble."""
    tiles = [x for x in flat if x != 0]
    inv = sum(1 for i in range(len(tiles)) for j in range(i+1, len(tiles)) if tiles[i] > tiles[j])
    return inv % 2 == 0

def shuffle_board():
    """Genera un tablero valido y resoluble."""
    while True:
        nums = list(range(9))
        random.shuffle(nums)
        if is_solvable(nums):
            board = [nums[i*3:(i+1)*3] for i in range(3)]
            if board != GOAL_STATE:
                return board

def get_neighbors(state):
    """Devuelve estados vecinos junto con la direccion del movimiento."""
    r, c = find_blank(state)
    moves = [(-1,0), (1,0), (0,-1), (0,1)]
    neighbors = []
    for dr, dc in moves:
        nr, nc = r+dr, c+dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            new = deepcopy(state)
            new[r][c], new[nr][nc] = new[nr][nc], new[r][c]
            neighbors.append((new, (nr, nc, r, c)))
    return neighbors

def heuristic(state):
    """Manhattan distance."""
    dist = 0
    for r in range(3):
        for c in range(3):
            val = state[r][c]
            if val != 0:
                gr, gc = (val-1)//3, (val-1)%3
                dist += abs(r-gr) + abs(c-gc)
    return dist

def solve_astar(start):
    """Resuelve con A*. Devuelve lista de (tile_r, tile_c, blank_r, blank_c)."""
    h = heuristic(start)
    heap = [(h, 0, start, [])]
    visited = set()
    while heap:
        f, g, state, path = heapq.heappop(heap)
        key = str(state)
        if key in visited:
            continue
        visited.add(key)
        if state == GOAL_STATE:
            return path
        for nstate, move in get_neighbors(state):
            nkey = str(nstate)
            if nkey not in visited:
                ng = g + 1
                nh = heuristic(nstate)
                heapq.heappush(heap, (ng+nh, ng, nstate, path+[move]))
    return []


# ─────────────────────────────────────────────
#  Aplicacion principal
# ─────────────────────────────────────────────
class EightPuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8 Puzzle — Juego del Rompecabezas")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        # Estado del juego
        self.board = []
        self.moves = 0
        self.start_time = 0.0
        self.elapsed = 0.0
        self.timer_running = False
        self.animating = False
        self.solve_queue = []

        # Tiles (canvas items)
        self.tile_rects = {}   # valor -> (shadow_id, rect_id, text_id)
        self.tile_pos   = {}   # valor -> (r, c)

        self._build_ui()
        self._new_game()

    # ── Construccion de la UI ──────────────────
    def _build_ui(self):
        # Titulo
        title_frame = tk.Frame(self.root, bg=BG_DARK)
        title_frame.pack(pady=(28, 0))

        tk.Label(title_frame, text="8", font=("Segoe UI", 42, "bold"),
                 fg=TILE_BG, bg=BG_DARK).pack(side="left")
        tk.Label(title_frame, text=" Puzzle", font=("Segoe UI", 42, "bold"),
                 fg=TEXT_MAIN, bg=BG_DARK).pack(side="left")

        tk.Label(self.root, text="Ordena las piezas del 1 al 8",
                 font=("Segoe UI", 11), fg=TEXT_DIM, bg=BG_DARK).pack(pady=(0, 16))

        # Stats
        stats_frame = tk.Frame(self.root, bg=BG_DARK)
        stats_frame.pack(pady=(0, 12))

        self.moves_var = tk.StringVar(value="0")
        self.time_var  = tk.StringVar(value="00:00")

        self._stat_box(stats_frame, "Movimientos", self.moves_var).pack(side="left", padx=18)
        self._stat_box(stats_frame, "Tiempo",      self.time_var ).pack(side="left", padx=18)

        # Canvas del tablero
        board_size = 3 * TILE_SIZE + 2 * TILE_GAP + 2 * GRID_OFFSET
        outer = tk.Frame(self.root, bg=BORDER_COLOR, bd=0, relief="flat")
        outer.pack(pady=8)
        self.canvas = tk.Canvas(outer, width=board_size, height=board_size,
                                bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(padx=3, pady=3)
        self.canvas.bind("<Button-1>", self._on_click)

        # Botones
        btn_frame = tk.Frame(self.root, bg=BG_DARK)
        btn_frame.pack(pady=22)
        self._make_button(btn_frame, "Nuevo",    BTN_BLUE,   self._new_game  ).pack(side="left", padx=8)
        self._make_button(btn_frame, "Resolver", BTN_PURPLE, self._auto_solve).pack(side="left", padx=8)
        self._make_button(btn_frame, "Reiniciar",BTN_ORANGE, self._reset_game).pack(side="left", padx=8)

        # Leyenda
        tk.Label(self.root,
                 text="Haz clic en una pieza adyacente al hueco para moverla",
                 font=("Segoe UI", 9), fg=TEXT_DIM, bg=BG_DARK).pack(pady=(0, 20))

        # Timer loop
        self._tick()

    def _stat_box(self, parent, label, var):
        frame = tk.Frame(parent, bg=BG_PANEL, padx=24, pady=10)
        tk.Label(frame, text=label, font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=BG_PANEL).pack()
        tk.Label(frame, textvariable=var, font=("Segoe UI", 22, "bold"),
                 fg=TEXT_MAIN, bg=BG_PANEL).pack()
        return frame

    def _make_button(self, parent, text, color, command):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 11, "bold"),
                        bg=color, fg="white", activebackground=TILE_HOVER,
                        activeforeground="white", bd=0, padx=18, pady=10,
                        cursor="hand2", relief="flat", command=command)
        btn.bind("<Enter>", lambda e, b=btn, c=color: b.configure(bg=self._lighten(c)))
        btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c))
        return btn

    @staticmethod
    def _lighten(hex_color):
        r = min(255, int(hex_color[1:3], 16) + 30)
        g = min(255, int(hex_color[3:5], 16) + 30)
        b = min(255, int(hex_color[5:7], 16) + 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── Dibujo del tablero ─────────────────────
    def _tile_xy(self, r, c):
        """Esquina superior izquierda de la celda (r,c)."""
        x = GRID_OFFSET + c * (TILE_SIZE + TILE_GAP)
        y = GRID_OFFSET + r * (TILE_SIZE + TILE_GAP)
        return x, y

    def _draw_board(self):
        self.canvas.delete("all")
        self.tile_rects.clear()
        self.tile_pos.clear()

        # Fondo de celdas vacias
        for r in range(3):
            for c in range(3):
                x, y = self._tile_xy(r, c)
                self.canvas.create_rectangle(
                    x, y, x+TILE_SIZE, y+TILE_SIZE,
                    fill=EMPTY_BG, outline=ACCENT_BLUE, width=2, tags="bg")

        # Piezas
        for r in range(3):
            for c in range(3):
                val = self.board[r][c]
                if val != 0:
                    self._draw_tile(val, r, c)

    def _draw_tile(self, val, r, c):
        x, y = self._tile_xy(r, c)
        margin = 4
        shadow = self.canvas.create_rectangle(
            x+margin+2, y+margin+2, x+TILE_SIZE-margin+2, y+TILE_SIZE-margin+2,
            fill="#1a0a14", outline="", tags=f"tile_{val}")
        rect = self.canvas.create_rectangle(
            x+margin, y+margin, x+TILE_SIZE-margin, y+TILE_SIZE-margin,
            fill=TILE_BG, outline=BORDER_COLOR, width=2, tags=f"tile_{val}")
        text = self.canvas.create_text(
            x + TILE_SIZE//2, y + TILE_SIZE//2,
            text=str(val), font=("Segoe UI", 32, "bold"),
            fill=TILE_TEXT, tags=f"tile_{val}")
        self.tile_rects[val] = (shadow, rect, text)
        self.tile_pos[val] = (r, c)

    # ── Logica de movimiento ───────────────────
    def _on_click(self, event):
        if self.animating:
            return
        col = (event.x - GRID_OFFSET) // (TILE_SIZE + TILE_GAP)
        row = (event.y - GRID_OFFSET) // (TILE_SIZE + TILE_GAP)
        if not (0 <= row < 3 and 0 <= col < 3):
            return
        val = self.board[row][col]
        if val == 0:
            return
        br, bc = find_blank(self.board)
        if abs(row-br) + abs(col-bc) == 1:
            self._animate_move(val, row, col, br, bc, callback=self._check_win)

    def _move_tile(self, val, from_r, from_c, to_r, to_c):
        self.board[to_r][to_c] = val
        self.board[from_r][from_c] = 0
        self.tile_pos[val] = (to_r, to_c)
        self.moves += 1
        self.moves_var.set(str(self.moves))

    def _animate_move(self, val, from_r, from_c, to_r, to_c, callback=None):
        if val not in self.tile_rects:
            return
        self.animating = True
        fx, fy = self._tile_xy(from_r, from_c)
        tx, ty = self._tile_xy(to_r, to_c)
        dx = (tx - fx) / ANIM_STEPS
        dy = (ty - fy) / ANIM_STEPS
        items = self.tile_rects[val]
        step = [0]

        def _step():
            if step[0] < ANIM_STEPS:
                for item in items:
                    self.canvas.move(item, dx, dy)
                step[0] += 1
                self.root.after(14, _step)
            else:
                self._move_tile(val, from_r, from_c, to_r, to_c)
                self.animating = False
                if callback:
                    callback()

        _step()

    # ── Control del juego ──────────────────────
    def _new_game(self):
        self.board = shuffle_board()
        self.moves = 0
        self.moves_var.set("0")
        self.start_time = time.time()
        self.elapsed = 0.0
        self.timer_running = True
        self.solve_queue = []
        self.animating = False
        self._draw_board()

    def _reset_game(self):
        self.moves = 0
        self.moves_var.set("0")
        self.start_time = time.time()
        self.elapsed = 0.0
        self.solve_queue = []
        self.animating = False
        self._draw_board()

    def _check_win(self):
        if self.board == GOAL_STATE:
            self.timer_running = False
            mins, secs = divmod(int(self.elapsed), 60)
            messagebox.showinfo(
                "Felicidades!",
                f"Resolviste el puzzle!\n\n"
                f"Movimientos: {self.moves}\n"
                f"Tiempo: {mins:02d}:{secs:02d}"
            )

    # ── Resolver automatico (A*) ───────────────
    def _auto_solve(self):
        if self.animating:
            return
        solution = solve_astar(self.board)
        if not solution:
            messagebox.showinfo("Info", "El puzzle ya esta resuelto.")
            return
        self.solve_queue = solution
        self._execute_solution()

    def _execute_solution(self):
        if not self.solve_queue or self.animating:
            return
        move = self.solve_queue.pop(0)
        tile_r, tile_c, blank_r, blank_c = move
        val = self.board[tile_r][tile_c]

        def _next():
            self._check_win()
            if self.solve_queue:
                self.root.after(60, self._execute_solution)

        self._animate_move(val, tile_r, tile_c, blank_r, blank_c, callback=_next)

    # ── Temporizador ───────────────────────────
    def _tick(self):
        if self.timer_running:
            self.elapsed = time.time() - self.start_time
            mins, secs = divmod(int(self.elapsed), 60)
            self.time_var.set(f"{mins:02d}:{secs:02d}")
        self.root.after(500, self._tick)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = EightPuzzleApp(root)
    root.mainloop()
