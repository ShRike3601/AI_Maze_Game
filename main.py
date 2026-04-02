import sys
import time
import heapq
import random
from collections import deque

import pygame

pygame.init()

BASE_WIDTH = 1180
BASE_HUD_HEIGHT = 88
BASE_GRID_SIZE = 740
BASE_UI_HEIGHT = 170
BASE_HEIGHT = BASE_HUD_HEIGHT + BASE_GRID_SIZE + BASE_UI_HEIGHT
BASE_GRID_X = 16
BASE_GAP = 16
BASE_RIGHT_PANEL_W = BASE_WIDTH - (BASE_GRID_X + BASE_GRID_SIZE + BASE_GAP + BASE_GAP)

display_info = pygame.display.Info()
MAX_WIN_W = int(display_info.current_w * 0.92)
MAX_WIN_H = int(display_info.current_h * 0.88)
SCALE = min(MAX_WIN_W / BASE_WIDTH, MAX_WIN_H / BASE_HEIGHT, 1.0)


def sv(value, minimum=1):
    return max(minimum, int(round(value * SCALE)))


HUD_HEIGHT = sv(BASE_HUD_HEIGHT, 70)
UI_HEIGHT = sv(BASE_UI_HEIGHT, 130)
GRID_SIZE = sv(BASE_GRID_SIZE, 520)
GRID_X = sv(BASE_GRID_X, 10)
GRID_GAP = sv(BASE_GAP, 10)
RIGHT_PANEL_W = sv(BASE_RIGHT_PANEL_W, 300)

WIDTH = GRID_X + GRID_SIZE + GRID_GAP + RIGHT_PANEL_W + GRID_GAP
HEIGHT = HUD_HEIGHT + GRID_SIZE + UI_HEIGHT

# Hard clamp to avoid bleeding on smaller displays.
if WIDTH > MAX_WIN_W:
    overflow = WIDTH - MAX_WIN_W
    GRID_SIZE = max(460, GRID_SIZE - overflow)
    WIDTH = GRID_X + GRID_SIZE + GRID_GAP + RIGHT_PANEL_W + GRID_GAP
if HEIGHT > MAX_WIN_H:
    overflow = HEIGHT - MAX_WIN_H
    GRID_SIZE = max(460, GRID_SIZE - overflow)
    HEIGHT = HUD_HEIGHT + GRID_SIZE + UI_HEIGHT
    WIDTH = GRID_X + GRID_SIZE + GRID_GAP + RIGHT_PANEL_W + GRID_GAP

GRID_Y = HUD_HEIGHT
ROWS = 20
COLS = 20
CELL_SIZE = GRID_SIZE // ROWS

MIN_GRID_CELLS = 12
MAX_GRID_CELLS = 200

VISIT_DELAY_MS = 25
PATH_DELAY_MS = 8
MAZE_OPENNESS = 0.30
EDGE_OPENNESS = 0.85
DEFAULT_CONFIG = {
    "grid_cells": 20,
    "visit_delay": 25,
    "maze_open": 0.30,
    "edge_open": 0.85,
}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Lab - BFS vs DFS vs A*")
clock = pygame.time.Clock()

# Palette
APP_BG = (14, 18, 24)
HUD_BG = (20, 26, 34)
PANEL_BG = (18, 24, 32)
GRID_LINE = (44, 58, 76)
WALL = (58, 68, 84)
CELL = (27, 36, 49)
START = (34, 197, 94)
GOAL = (239, 68, 68)
VISITED = (56, 189, 248)
PATH = (250, 204, 21)
PLAYER = (167, 139, 250)
TEXT = (226, 232, 240)
TEXT_DIM = (148, 163, 184)
BTN_IDLE = (36, 49, 64)
BTN_ACTIVE = (14, 116, 144)
BTN_ACCENT = (22, 163, 74)
BTN_WARN = (148, 35, 35)
OVERLAY_BG = (8, 11, 16, 210)

grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
start_pos = None
goal_pos = None

selected_algo = "BFS"
node_mode = "MANUAL"

visited_nodes = set()
path = []

is_animating = False
run_nodes_counter = 0
run_elapsed_time = 0.0
run_started_at = None
run_mode = None

player_active = False
player_pos = None
player_steps = 0
player_visited = set()

baseline_dirty = True
astar_baseline = None
result_overlay = None
scene = "landing"

title_font = pygame.font.SysFont("segoeui", sv(34, 24), bold=True)
font = pygame.font.SysFont("segoeui", sv(26, 18))
small_font = pygame.font.SysFont("segoeui", sv(22, 16))
tiny_font = pygame.font.SysFont("segoeui", sv(18, 13))
landing_title_font = pygame.font.SysFont("segoeui", sv(56, 36), bold=True)

start_button = pygame.Rect((WIDTH // 2) - sv(110, 80), (HEIGHT // 2) + sv(20, 14), sv(220, 160), sv(64, 46))
exit_button = pygame.Rect((WIDTH // 2) - sv(110, 80), (HEIGHT // 2) + sv(104, 74), sv(220, 160), sv(64, 46))

# Controls
btn_y1 = GRID_Y + GRID_SIZE + sv(10, 8)
btn_y2 = GRID_Y + GRID_SIZE + sv(68, 48)
bfs_button = pygame.Rect(sv(18, 12), btn_y1, sv(88, 62), sv(44, 32))
dfs_button = pygame.Rect(sv(114, 80), btn_y1, sv(88, 62), sv(44, 32))
astar_button = pygame.Rect(sv(210, 148), btn_y1, sv(88, 62), sv(44, 32))
run_button = pygame.Rect(sv(306, 216), btn_y1, sv(88, 62), sv(44, 32))
play_button = pygame.Rect(sv(402, 284), btn_y1, sv(88, 62), sv(44, 32))
maze_button = pygame.Rect(sv(498, 352), btn_y1, sv(130, 92), sv(44, 32))
clear_button = pygame.Rect(sv(636, 450), btn_y1, sv(88, 62), sv(44, 32))
stop_button = pygame.Rect(sv(732, 518), btn_y1, sv(118, 84), sv(44, 32))
manual_mode_button = pygame.Rect(sv(18, 12), btn_y2, sv(160, 114), sv(40, 30))
auto_mode_button = pygame.Rect(sv(186, 132), btn_y2, sv(140, 100), sv(40, 30))

right_panel_rect = pygame.Rect(GRID_X + GRID_SIZE + GRID_GAP, GRID_Y + sv(10, 8), RIGHT_PANEL_W, GRID_SIZE - sv(20, 14))
active_slider = None
stop_requested = False
astar_g_scores = {}
bfs_depths = {}
dfs_depths = {}
large_grid_popout = False

settings_panel_rect = pygame.Rect(right_panel_rect.x, right_panel_rect.y, right_panel_rect.width, int(right_panel_rect.height * 0.62))
algo_info_rect = pygame.Rect(
    right_panel_rect.x,
    settings_panel_rect.bottom + 12,
    right_panel_rect.width,
    right_panel_rect.bottom - (settings_panel_rect.bottom + 12),
)
default_settings_button = pygame.Rect(settings_panel_rect.x + sv(16, 10), settings_panel_rect.bottom - sv(38, 28), settings_panel_rect.width - sv(32, 20), sv(30, 24))

sliders = {
    "grid_cells": {
        "label": "Grid Size",
        "min": MIN_GRID_CELLS,
        "max": MAX_GRID_CELLS,
        "step": 1,
        "value": ROWS,
        "rect": pygame.Rect(settings_panel_rect.x + 18, settings_panel_rect.y + 82, settings_panel_rect.width - 36, 8),
    },
    "visit_delay": {
        "label": "Search Delay (ms)",
        "min": 5,
        "max": 140,
        "step": 1,
        "value": VISIT_DELAY_MS,
        "rect": pygame.Rect(settings_panel_rect.x + 18, settings_panel_rect.y + 176, settings_panel_rect.width - 36, 8),
    },
    "maze_open": {
        "label": "Maze Openness",
        "min": 0.10,
        "max": 0.55,
        "step": 0.01,
        "value": MAZE_OPENNESS,
        "rect": pygame.Rect(settings_panel_rect.x + 18, settings_panel_rect.y + 270, settings_panel_rect.width - 36, 8),
    },
    "edge_open": {
        "label": "Edge Openness",
        "min": 0.40,
        "max": 1.00,
        "step": 0.01,
        "value": EDGE_OPENNESS,
        "rect": pygame.Rect(settings_panel_rect.x + 18, settings_panel_rect.y + 364, settings_panel_rect.width - 36, 8),
    },
}


def draw_button(rect, text, color, text_color=TEXT):
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, GRID_LINE, rect, 1, border_radius=10)
    label = small_font.render(text, True, text_color)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)


def wrap_text(text, text_font, max_width):
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if text_font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_wrapped_text(text, x, y, text_font, color, max_width, line_gap=4):
    lines = wrap_text(text, text_font, max_width)
    cy = y
    for line in lines:
        surf = text_font.render(line, True, color)
        screen.blit(surf, (x, cy))
        cy += surf.get_height() + line_gap
    return cy


def clamp(value, low, high):
    return max(low, min(high, value))


def slider_ratio(slider):
    return (slider["value"] - slider["min"]) / (slider["max"] - slider["min"])


def slider_value_from_x(slider, x_pos):
    rect = slider["rect"]
    ratio = clamp((x_pos - rect.x) / rect.width, 0.0, 1.0)
    raw = slider["min"] + ratio * (slider["max"] - slider["min"])
    step = slider["step"]
    snapped = round(raw / step) * step
    return clamp(snapped, slider["min"], slider["max"])


def grid_pixel_size():
    return GRID_SIZE


def get_grid_render_rect():
    if scene == "game" and large_grid_popout and ROWS >= 120:
        side = min(WIDTH - 80, HEIGHT - 140)
        return pygame.Rect((WIDTH - side) // 2, HUD_HEIGHT + 10, side, side)
    return pygame.Rect(GRID_X, GRID_Y, GRID_SIZE, GRID_SIZE)


def is_auto_speed_locked():
    return ROWS >= 25


def get_render_step():
    if ROWS >= 180:
        return 120
    if ROWS >= 140:
        return 80
    if ROWS >= 100:
        return 50
    if ROWS >= 70:
        return 20
    if ROWS >= 45:
        return 10
    return 1


def get_path_render_step():
    if ROWS >= 180:
        return 16
    if ROWS >= 140:
        return 12
    if ROWS >= 100:
        return 8
    if ROWS >= 70:
        return 4
    return 1


def update_search_speed_policy():
    global VISIT_DELAY_MS, PATH_DELAY_MS
    if ROWS >= 33:
        VISIT_DELAY_MS = 1
        PATH_DELAY_MS = 4
    elif ROWS >= 31:
        VISIT_DELAY_MS = 2
        PATH_DELAY_MS = 6
    elif ROWS >= 25:
        VISIT_DELAY_MS = 3
        PATH_DELAY_MS = 8
    else:
        VISIT_DELAY_MS = int(sliders["visit_delay"]["value"])
        PATH_DELAY_MS = 12


def get_cell_from_mouse(pos):
    x, y = pos
    grid_rect = get_grid_render_rect()
    active_size = grid_rect.width
    if y < grid_rect.y or y >= grid_rect.y + active_size:
        return None
    if x < grid_rect.x or x >= grid_rect.x + active_size:
        return None
    row = int(((y - grid_rect.y) * ROWS) / active_size)
    col = int(((x - grid_rect.x) * COLS) / active_size)
    row = int(clamp(row, 0, ROWS - 1))
    col = int(clamp(col, 0, COLS - 1))
    if 0 <= row < ROWS and 0 <= col < COLS:
        return row, col
    return None


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors_of(cell):
    row, col = cell
    return [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]


def reconstruct_path(parent, start, goal):
    if goal != start and goal not in parent:
        return []
    out = []
    node = goal
    while node != start:
        out.append(node)
        node = parent[node]
    out.append(start)
    out.reverse()
    return out


def astar(grid_data, start, goal):
    start_t = time.time()
    open_set = []
    heapq.heappush(open_set, (0, start))
    g_score = {start: 0}
    parent = {}
    visited = set()
    nodes_expanded = 0

    while open_set:
        _, current = heapq.heappop(open_set)
        nodes_expanded += 1
        if current == goal:
            break
        if current in visited:
            continue
        visited.add(current)

        for r, c in neighbors_of(current):
            if not (0 <= r < ROWS and 0 <= c < COLS):
                continue
            if grid_data[r][c] == 1:
                continue
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get((r, c), float("inf")):
                g_score[(r, c)] = tentative_g
                parent[(r, c)] = current
                f_score = tentative_g + heuristic((r, c), goal)
                heapq.heappush(open_set, (f_score, (r, c)))

    result_path = reconstruct_path(parent, start, goal)
    return result_path, visited, nodes_expanded, time.time() - start_t


def bfs(grid_data, start, goal):
    start_t = time.time()
    queue = deque([start])
    visited = {start}
    parent = {}
    nodes_expanded = 0

    while queue:
        current = queue.popleft()
        nodes_expanded += 1
        if current == goal:
            break
        for r, c in neighbors_of(current):
            if 0 <= r < ROWS and 0 <= c < COLS and grid_data[r][c] != 1 and (r, c) not in visited:
                visited.add((r, c))
                parent[(r, c)] = current
                queue.append((r, c))

    result_path = reconstruct_path(parent, start, goal)
    return result_path, visited, nodes_expanded, time.time() - start_t


def dfs(grid_data, start, goal):
    start_t = time.time()
    stack = [start]
    visited = {start}
    parent = {}
    nodes_expanded = 0

    while stack:
        current = stack.pop()
        nodes_expanded += 1
        if current == goal:
            break
        for r, c in [(current[0] - 1, current[1]), (current[0], current[1] - 1), (current[0] + 1, current[1]), (current[0], current[1] + 1)]:
            if 0 <= r < ROWS and 0 <= c < COLS and grid_data[r][c] != 1 and (r, c) not in visited:
                visited.add((r, c))
                parent[(r, c)] = current
                stack.append((r, c))

    result_path = reconstruct_path(parent, start, goal)
    return result_path, visited, nodes_expanded, time.time() - start_t


def clear_search_results():
    global path, visited_nodes, run_nodes_counter, run_elapsed_time, run_started_at, run_mode
    global astar_g_scores, bfs_depths, dfs_depths
    path = []
    visited_nodes = set()
    run_nodes_counter = 0
    run_elapsed_time = 0.0
    run_started_at = None
    run_mode = None
    astar_g_scores = {}
    bfs_depths = {}
    dfs_depths = {}


def clear_result_overlay():
    global result_overlay
    result_overlay = None


def invalidate_baseline():
    global baseline_dirty
    baseline_dirty = True


def set_start(cell):
    global start_pos
    row, col = cell
    if grid[row][col] == 1:
        grid[row][col] = 0
    if start_pos:
        grid[start_pos[0]][start_pos[1]] = 0
    start_pos = (row, col)
    if goal_pos == start_pos:
        clear_goal()
    grid[row][col] = 2
    clear_search_results()
    clear_result_overlay()
    invalidate_baseline()


def clear_goal():
    global goal_pos
    if goal_pos:
        grid[goal_pos[0]][goal_pos[1]] = 0
    goal_pos = None
    invalidate_baseline()


def set_goal(cell):
    global goal_pos, start_pos
    row, col = cell
    if grid[row][col] == 1:
        grid[row][col] = 0
    if goal_pos:
        grid[goal_pos[0]][goal_pos[1]] = 0
    goal_pos = (row, col)
    if start_pos == goal_pos:
        if start_pos:
            grid[start_pos[0]][start_pos[1]] = 0
        start_pos = None
    grid[row][col] = 3
    clear_search_results()
    clear_result_overlay()
    invalidate_baseline()


def auto_place_start_goal():
    open_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == 0]
    if len(open_cells) < 2:
        return False

    min_distance = max(7, (ROWS + COLS) // 3)
    best_pair = None
    best_distance = -1

    for _ in range(400):
        s = random.choice(open_cells)
        g = random.choice(open_cells)
        if s == g:
            continue
        dist = abs(s[0] - g[0]) + abs(s[1] - g[1])
        if dist > best_distance:
            best_distance = dist
            best_pair = (s, g)
        if dist >= min_distance:
            trial_path, _, _, _ = bfs(grid, s, g)
            if trial_path:
                set_start(s)
                set_goal(g)
                return True

    if best_pair:
        s, g = best_pair
        trial_path, _, _, _ = bfs(grid, s, g)
        if trial_path:
            set_start(s)
            set_goal(g)
            return True
    return False


def apply_grid_size(new_size):
    global ROWS, COLS, CELL_SIZE, player_active, player_pos, grid, start_pos, goal_pos, large_grid_popout
    new_size = int(clamp(new_size, MIN_GRID_CELLS, MAX_GRID_CELLS))
    if new_size == ROWS:
        return
    old_rows = ROWS
    old_cols = COLS
    old_grid = [row[:] for row in grid]
    old_start = start_pos
    old_goal = goal_pos

    ROWS = new_size
    COLS = new_size
    CELL_SIZE = GRID_SIZE // ROWS
    player_active = False
    player_pos = None
    sliders["grid_cells"]["value"] = ROWS

    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    overlap_r = min(old_rows, ROWS)
    overlap_c = min(old_cols, COLS)
    for r in range(overlap_r):
        for c in range(overlap_c):
            if old_grid[r][c] == 1:
                grid[r][c] = 1

    start_pos = old_start if old_start and old_start[0] < ROWS and old_start[1] < COLS and grid[old_start[0]][old_start[1]] != 1 else None
    goal_pos = old_goal if old_goal and old_goal[0] < ROWS and old_goal[1] < COLS and grid[old_goal[0]][old_goal[1]] != 1 else None

    if start_pos:
        grid[start_pos[0]][start_pos[1]] = 2
    if goal_pos and goal_pos != start_pos:
        grid[goal_pos[0]][goal_pos[1]] = 3
    elif goal_pos == start_pos:
        goal_pos = None

    large_grid_popout = ROWS >= 120
    update_search_speed_policy()
    clear_search_results()
    clear_result_overlay()
    invalidate_baseline()
    if node_mode == "AUTO" and (not start_pos or not goal_pos):
        auto_place_start_goal()


def apply_slider_value(slider_key, value):
    global VISIT_DELAY_MS, MAZE_OPENNESS, EDGE_OPENNESS
    slider = sliders[slider_key]
    slider["value"] = value
    if slider_key == "grid_cells":
        apply_grid_size(int(value))
    elif slider_key == "visit_delay":
        if not is_auto_speed_locked():
            VISIT_DELAY_MS = int(value)
    elif slider_key == "maze_open":
        MAZE_OPENNESS = float(value)
    elif slider_key == "edge_open":
        EDGE_OPENNESS = float(value)


def reset_settings_to_default():
    apply_grid_size(int(DEFAULT_CONFIG["grid_cells"]))
    apply_slider_value("visit_delay", DEFAULT_CONFIG["visit_delay"])
    apply_slider_value("maze_open", DEFAULT_CONFIG["maze_open"])
    apply_slider_value("edge_open", DEFAULT_CONFIG["edge_open"])
    sliders["visit_delay"]["value"] = DEFAULT_CONFIG["visit_delay"]
    sliders["maze_open"]["value"] = MAZE_OPENNESS
    sliders["edge_open"]["value"] = EDGE_OPENNESS
    update_search_speed_policy()


def generate_procedural_maze():
    global grid, start_pos, goal_pos
    grid = [[1 for _ in range(COLS)] for _ in range(ROWS)]

    odd_rows = [r for r in range(1, ROWS, 2)]
    odd_cols = [c for c in range(1, COLS, 2)]
    if not odd_rows or not odd_cols:
        grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    else:
        sr = random.choice(odd_rows)
        sc = random.choice(odd_cols)
        stack = [(sr, sc)]
        grid[sr][sc] = 0

        while stack:
            r, c = stack[-1]
            candidates = []
            for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr < ROWS - 1 and 1 <= nc < COLS - 1 and grid[nr][nc] == 1:
                    candidates.append((nr, nc, r + dr // 2, c + dc // 2))
            if candidates:
                nr, nc, wr, wc = random.choice(candidates)
                grid[wr][wc] = 0
                grid[nr][nc] = 0
                stack.append((nr, nc))
            else:
                stack.pop()

    # Braid the maze to create many alternate routes.
    interior_walls = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == 1]
    random.shuffle(interior_walls)
    for r, c in interior_walls[: int(len(interior_walls) * MAZE_OPENNESS)]:
        grid[r][c] = 0

    # No hard border walls.
    for r in range(ROWS):
        if random.random() < EDGE_OPENNESS:
            grid[r][0] = 0
        if random.random() < EDGE_OPENNESS:
            grid[r][COLS - 1] = 0
    for c in range(COLS):
        if random.random() < EDGE_OPENNESS:
            grid[0][c] = 0
        if random.random() < EDGE_OPENNESS:
            grid[ROWS - 1][c] = 0

    start_pos = None
    goal_pos = None
    clear_search_results()
    clear_result_overlay()
    invalidate_baseline()
    if node_mode == "AUTO":
        auto_place_start_goal()


def compute_astar_baseline():
    global astar_baseline, baseline_dirty
    if not start_pos or not goal_pos:
        astar_baseline = None
        baseline_dirty = False
        return
    baseline_path, _, nodes_expanded, elapsed = astar(grid, start_pos, goal_pos)
    astar_baseline = {
        "path_len": len(baseline_path),
        "moves": max(0, len(baseline_path) - 1),
        "nodes": nodes_expanded,
        "time": elapsed,
        "solvable": bool(baseline_path),
    }
    baseline_dirty = False


def present_result(mode, success, elapsed, nodes_count, path_len, steps_count=None):
    global result_overlay
    optimal_moves = None
    is_optimal = False
    optimal_text = "No baseline available"

    if astar_baseline and astar_baseline["solvable"]:
        optimal_moves = astar_baseline["moves"]
        if mode == "PLAYER":
            is_optimal = steps_count == optimal_moves if success else False
            optimal_text = f"A* best moves: {optimal_moves}, your moves: {steps_count}"
        else:
            algo_moves = max(0, path_len - 1) if success else None
            is_optimal = algo_moves == optimal_moves if success else False
            optimal_text = f"A* best moves: {optimal_moves}, {mode} moves: {algo_moves}"
    elif astar_baseline and not astar_baseline["solvable"]:
        optimal_text = "A*: no path exists on this map"

    result_overlay = {
        "mode": mode,
        "success": success,
        "elapsed": elapsed,
        "nodes": nodes_count,
        "path_len": path_len,
        "steps": steps_count,
        "optimal": is_optimal,
        "optimal_text": optimal_text,
    }


def process_runtime_events():
    global running, stop_requested
    for pe in pygame.event.get():
        if pe.type == pygame.QUIT:
            running = False
            stop_requested = True
            return
        if pe.type == pygame.MOUSEBUTTONDOWN and pe.button == 1 and stop_button.collidepoint(pe.pos):
            stop_requested = True


def smooth_wait(delay_ms):
    global run_elapsed_time
    if delay_ms <= 0:
        return
    end_time = time.perf_counter() + (delay_ms / 1000.0)
    while running and not stop_requested and time.perf_counter() < end_time:
        process_runtime_events()
        if run_started_at is not None:
            run_elapsed_time = time.time() - run_started_at
        draw_scene()
        pygame.display.flip()
        clock.tick(240)


def run_selected_algorithm():
    global path, visited_nodes, is_animating, run_nodes_counter, result_overlay, running, stop_requested
    global astar_g_scores, bfs_depths, dfs_depths
    global run_started_at, run_elapsed_time, run_mode, player_active, player_pos
    if not start_pos or not goal_pos:
        return
    if baseline_dirty:
        compute_astar_baseline()
    if astar_baseline and not astar_baseline["solvable"]:
        present_result(selected_algo, False, 0.0, 0, 0)
        return

    clear_result_overlay()
    clear_search_results()
    player_active = False
    player_pos = None
    is_animating = True
    stop_requested = False
    run_mode = selected_algo
    run_started_at = time.time()
    render_step = get_render_step()
    path_render_step = get_path_render_step()
    visit_delay = VISIT_DELAY_MS
    path_delay = PATH_DELAY_MS

    parent = {}
    found = False

    if selected_algo == "BFS":
        frontier = deque([start_pos])
        discovered = {start_pos}
        bfs_depths = {start_pos: 0}
        while frontier and running and not stop_requested:
            process_runtime_events()
            if not running or stop_requested:
                break
            current = frontier.popleft()
            run_nodes_counter += 1
            if current not in (start_pos, goal_pos):
                visited_nodes.add(current)
            if current == goal_pos:
                found = True
                break
            for n in neighbors_of(current):
                r, c = n
                if 0 <= r < ROWS and 0 <= c < COLS and grid[r][c] != 1 and n not in discovered:
                    discovered.add(n)
                    parent[n] = current
                    bfs_depths[n] = bfs_depths[current] + 1
                    frontier.append(n)
            run_elapsed_time = time.time() - run_started_at
            should_render = (run_nodes_counter % render_step == 0) or current == goal_pos
            if should_render:
                draw_scene()
                pygame.display.flip()
                smooth_wait(visit_delay)

    elif selected_algo == "DFS":
        frontier = [start_pos]
        discovered = {start_pos}
        dfs_depths = {start_pos: 0}
        while frontier and running and not stop_requested:
            process_runtime_events()
            if not running or stop_requested:
                break
            current = frontier.pop()
            run_nodes_counter += 1
            if current not in (start_pos, goal_pos):
                visited_nodes.add(current)
            if current == goal_pos:
                found = True
                break
            for n in [(current[0] - 1, current[1]), (current[0], current[1] - 1), (current[0] + 1, current[1]), (current[0], current[1] + 1)]:
                r, c = n
                if 0 <= r < ROWS and 0 <= c < COLS and grid[r][c] != 1 and n not in discovered:
                    discovered.add(n)
                    parent[n] = current
                    dfs_depths[n] = dfs_depths[current] + 1
                    frontier.append(n)
            run_elapsed_time = time.time() - run_started_at
            should_render = (run_nodes_counter % render_step == 0) or current == goal_pos
            if should_render:
                draw_scene()
                pygame.display.flip()
                smooth_wait(visit_delay)

    else:
        frontier = [(heuristic(start_pos, goal_pos), start_pos)]
        g_score = {start_pos: 0}
        astar_g_scores = {start_pos: 0}
        closed = set()
        while frontier and running and not stop_requested:
            process_runtime_events()
            if not running or stop_requested:
                break
            _, current = heapq.heappop(frontier)
            if current in closed:
                continue
            closed.add(current)
            run_nodes_counter += 1
            if current not in (start_pos, goal_pos):
                visited_nodes.add(current)
            if current == goal_pos:
                found = True
                break
            for n in neighbors_of(current):
                r, c = n
                if not (0 <= r < ROWS and 0 <= c < COLS):
                    continue
                if grid[r][c] == 1:
                    continue
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(n, float("inf")):
                    g_score[n] = tentative_g
                    astar_g_scores[n] = tentative_g
                    parent[n] = current
                    heapq.heappush(frontier, (tentative_g + heuristic(n, goal_pos), n))
            run_elapsed_time = time.time() - run_started_at
            should_render = (run_nodes_counter % render_step == 0) or current == goal_pos
            if should_render:
                draw_scene()
                pygame.display.flip()
                smooth_wait(visit_delay)

    if stop_requested:
        is_animating = False
        return

    elapsed = time.time() - run_started_at
    run_elapsed_time = elapsed
    if found:
        full_path = reconstruct_path(parent, start_pos, goal_pos)
        path = []
        for node in full_path:
            process_runtime_events()
            if not running or stop_requested:
                break
            path.append(node)
            run_elapsed_time = time.time() - run_started_at
            should_render_path = (len(path) % path_render_step == 0) or node == goal_pos
            if should_render_path:
                draw_scene()
                pygame.display.flip()
                smooth_wait(path_delay)
        if stop_requested:
            is_animating = False
            return
        present_result(selected_algo, True, elapsed, run_nodes_counter, len(path))
    else:
        path = []
        present_result(selected_algo, False, elapsed, run_nodes_counter, 0)

    is_animating = False


def start_player_mode():
    global player_active, player_pos, player_steps, player_visited, run_started_at, run_elapsed_time, run_mode
    if not start_pos or not goal_pos:
        return
    if baseline_dirty:
        compute_astar_baseline()
    if astar_baseline and not astar_baseline["solvable"]:
        present_result("PLAYER", False, 0.0, 0, 0, steps_count=0)
        return

    clear_result_overlay()
    clear_search_results()
    player_active = True
    player_pos = start_pos
    player_steps = 0
    player_visited = {start_pos}
    run_mode = "PLAYER"
    run_started_at = None
    run_elapsed_time = 0.0


def deactivate_player_mode():
    global player_active, player_pos, stop_requested
    player_active = False
    player_pos = None
    stop_requested = True
    clear_search_results()


def stop_player_mode(success):
    global player_active, player_pos
    elapsed = run_elapsed_time
    nodes_count = len(player_visited)
    present_result("PLAYER", success, elapsed, nodes_count, path_len=0, steps_count=player_steps)
    player_active = False
    player_pos = None


def move_player(delta_row, delta_col):
    global player_pos, player_steps, run_started_at
    if not player_active or not player_pos:
        return
    nr = player_pos[0] + delta_row
    nc = player_pos[1] + delta_col
    if not (0 <= nr < ROWS and 0 <= nc < COLS):
        return
    if grid[nr][nc] == 1:
        return
    if run_started_at is None:
        run_started_at = time.time()
    player_pos = (nr, nc)
    player_steps += 1
    player_visited.add(player_pos)
    if player_pos == goal_pos:
        stop_player_mode(True)


def draw_hud():
    hud_rect = pygame.Rect(0, 0, WIDTH, HUD_HEIGHT)
    pygame.draw.rect(screen, HUD_BG, hud_rect)
    pygame.draw.line(screen, GRID_LINE, (0, HUD_HEIGHT - 1), (WIDTH, HUD_HEIGHT - 1), 1)

    if player_active:
        elapsed_value = run_elapsed_time
        nodes_value = len(player_visited)
        mode_label = "MODE: PLAYER"
    elif is_animating:
        elapsed_value = run_elapsed_time
        nodes_value = run_nodes_counter
        mode_label = f"MODE: {selected_algo}"
    else:
        elapsed_value = run_elapsed_time
        nodes_value = run_nodes_counter if run_nodes_counter else len(visited_nodes)
        mode_label = f"MODE: {selected_algo}"

    title = title_font.render("Maze Search Lab", True, TEXT)
    timer = font.render(f"Time: {elapsed_value:.2f}s", True, TEXT)
    nodes = font.render(f"Nodes Visited: {nodes_value}", True, TEXT)
    mode = small_font.render(mode_label, True, TEXT_DIM)

    screen.blit(title, (sv(16, 10), sv(10, 8)))
    screen.blit(timer, (sv(320, 210), sv(14, 10)))
    screen.blit(nodes, (sv(530, 360), sv(14, 10)))
    screen.blit(mode, (sv(320, 210), sv(52, 38)))


def draw_landing_scene():
    screen.fill(APP_BG)
    title = landing_title_font.render("Maze Search Lab", True, TEXT)
    subtitle = font.render("Visualize BFS, DFS, A* and play manually", True, TEXT_DIM)
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110))
    subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
    screen.blit(title, title_rect)
    screen.blit(subtitle, subtitle_rect)

    draw_button(start_button, "START", BTN_ACCENT)
    draw_button(exit_button, "EXIT", BTN_WARN)


def draw_grid():
    grid_rect = get_grid_render_rect()
    active_size = grid_rect.width
    pygame.draw.rect(screen, CELL, grid_rect)
    draw_cell_borders = ROWS <= 80

    for row in range(ROWS):
        for col in range(COLS):
            x0 = grid_rect.x + int((col * active_size) / COLS)
            x1 = grid_rect.x + int(((col + 1) * active_size) / COLS)
            y0 = grid_rect.y + int((row * active_size) / ROWS)
            y1 = grid_rect.y + int(((row + 1) * active_size) / ROWS)
            rect = pygame.Rect(x0, y0, max(1, x1 - x0), max(1, y1 - y0))
            cell = grid[row][col]
            if cell == 1:
                color = WALL
            elif cell == 2:
                color = START
            elif cell == 3:
                color = GOAL
            elif (row, col) in path:
                color = PATH
            elif (row, col) in visited_nodes:
                color = VISITED
            elif player_active and (row, col) in player_visited:
                color = (58, 82, 108)
            else:
                color = CELL
            pygame.draw.rect(screen, color, rect)
            if draw_cell_borders:
                pygame.draw.rect(screen, GRID_LINE, rect, 1)

    if player_pos:
        x0 = grid_rect.x + int((player_pos[1] * active_size) / COLS)
        x1 = grid_rect.x + int(((player_pos[1] + 1) * active_size) / COLS)
        y0 = grid_rect.y + int((player_pos[0] * active_size) / ROWS)
        y1 = grid_rect.y + int(((player_pos[0] + 1) * active_size) / ROWS)
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        radius = max(2, min(x1 - x0, y1 - y0) // 3)
        pygame.draw.circle(screen, PLAYER, (cx, cy), radius)

    if large_grid_popout and ROWS >= 120:
        tag = tiny_font.render("Large Grid Pop-out View (press V to toggle)", True, TEXT_DIM)
        screen.blit(tag, (grid_rect.x + 10, grid_rect.y + 8))


def draw_side_controls():
    pygame.draw.rect(screen, PANEL_BG, settings_panel_rect, border_radius=12)
    pygame.draw.rect(screen, GRID_LINE, settings_panel_rect, 1, border_radius=12)

    header = font.render("Manual Settings", True, TEXT)
    screen.blit(header, (settings_panel_rect.x + sv(16, 10), settings_panel_rect.y + sv(14, 10)))

    # Keep heading separated and tighten row spacing so the last slider stays above the button.
    y_gap = sv(82, 60)
    base_y = settings_panel_rect.y + sv(66, 48)
    keys = ["grid_cells", "visit_delay", "maze_open", "edge_open"]
    for idx, key in enumerate(keys):
        slider = sliders[key]
        label_y = base_y + idx * y_gap
        slider["rect"] = pygame.Rect(settings_panel_rect.x + sv(18, 12), label_y + sv(30, 22), settings_panel_rect.width - sv(36, 24), sv(8, 6))
        label = small_font.render(slider["label"], True, TEXT_DIM)
        screen.blit(label, (slider["rect"].x, label_y))

        pygame.draw.rect(screen, (42, 54, 70), slider["rect"], border_radius=5)
        if key == "visit_delay" and is_auto_speed_locked():
            slider["value"] = VISIT_DELAY_MS
        ratio = slider_ratio(slider)
        fill_w = max(2, int(slider["rect"].width * ratio))
        fill_rect = pygame.Rect(slider["rect"].x, slider["rect"].y, fill_w, slider["rect"].height)
        fill_color = (95, 115, 138) if key == "visit_delay" and is_auto_speed_locked() else BTN_ACTIVE
        pygame.draw.rect(screen, fill_color, fill_rect, border_radius=5)

        knob_x = slider["rect"].x + int(slider["rect"].width * ratio)
        knob_y = slider["rect"].centery
        knob_color = TEXT_DIM if key == "visit_delay" and is_auto_speed_locked() else TEXT
        pygame.draw.circle(screen, knob_color, (knob_x, knob_y), 9)

        if key in ("maze_open", "edge_open"):
            value_text = f"{int(slider['value'] * 100)}%"
        else:
            value_text = f"{int(slider['value'])}"
        value = small_font.render(value_text, True, TEXT)
        screen.blit(value, (slider["rect"].right - value.get_width(), label_y))
        if key == "visit_delay" and is_auto_speed_locked():
            auto_text = small_font.render("Auto speed for large grids", True, TEXT_DIM)
            screen.blit(auto_text, (slider["rect"].x, label_y + 24))

    draw_button(default_settings_button, "Default Settings", BTN_IDLE)

    pygame.draw.rect(screen, PANEL_BG, algo_info_rect, border_radius=12)
    pygame.draw.rect(screen, GRID_LINE, algo_info_rect, 1, border_radius=12)

    info_x = algo_info_rect.x + sv(14, 10)
    info_y = algo_info_rect.y + sv(12, 8)
    info_w = algo_info_rect.width - sv(28, 20)
    title = small_font.render(f"{selected_algo} Explanation", True, TEXT)
    screen.blit(title, (info_x, info_y))
    info_y += sv(28, 20)

    hover = get_cell_from_mouse(pygame.mouse.get_pos())
    if selected_algo == "A*":
        info_y = draw_wrapped_text(
            "A* evaluates nodes with f(n)=g(n)+h(n). Here h(n) uses Manhattan distance to estimate remaining steps.",
            info_x, info_y, tiny_font, TEXT_DIM, info_w
        ) + 4
        if hover and goal_pos:
            hr, hc = hover
            h_val = abs(hr - goal_pos[0]) + abs(hc - goal_pos[1])
            g_val = astar_g_scores.get(hover)
            f_val = (g_val + h_val) if g_val is not None else "-"
            lines = [
                f"Start Node: ({start_pos[0]}, {start_pos[1]})" if start_pos else "Start Node: -",
                f"Current Node: ({hr}, {hc})",
                f"Goal Node: ({goal_pos[0]}, {goal_pos[1]})",
                f"g(n): {g_val if g_val is not None else '-'}",
                f"h(n): {h_val} = |{hr}-{goal_pos[0]}| + |{hc}-{goal_pos[1]}|",
                f"f(n): {f_val} (f = g + h)",
            ]
            for line in lines:
                info_y = draw_wrapped_text(line, info_x, info_y, tiny_font, TEXT_DIM, info_w) + 2
        else:
            draw_wrapped_text(
                "Hover a grid cell to inspect g(n), h(n), and f(n).",
                info_x, info_y, tiny_font, TEXT_DIM, info_w
            )
    elif selected_algo == "BFS":
        info_y = draw_wrapped_text(
            "BFS uses a FIFO queue and explores in layers. In this grid, it guarantees the shortest path.",
            info_x, info_y, tiny_font, TEXT_DIM, info_w
        ) + 4
        if hover:
            hr, hc = hover
            depth = bfs_depths.get(hover, "-")
            draw_wrapped_text(
                f"Node ({hr},{hc}) BFS layer depth from start: {depth}.",
                info_x, info_y, tiny_font, TEXT_DIM, info_w
            )
        else:
            draw_wrapped_text(
                "Hover a grid cell to inspect explored BFS depth.",
                info_x, info_y, tiny_font, TEXT_DIM, info_w
            )
    else:
        info_y = draw_wrapped_text(
            "DFS uses a LIFO stack and dives deep before backtracking. It may find a path that is not shortest.",
            info_x, info_y, tiny_font, TEXT_DIM, info_w
        ) + 4
        if hover:
            hr, hc = hover
            depth = dfs_depths.get(hover, "-")
            draw_wrapped_text(
                f"Node ({hr},{hc}) DFS discovery depth: {depth}.",
                info_x, info_y, tiny_font, TEXT_DIM, info_w
            )
        else:
            draw_wrapped_text(
                "Hover a grid cell to inspect DFS discovery depth.",
                info_x, info_y, tiny_font, TEXT_DIM, info_w
            )


def draw_controls():
    panel_rect = pygame.Rect(0, GRID_Y + GRID_SIZE, WIDTH, UI_HEIGHT)
    pygame.draw.rect(screen, PANEL_BG, panel_rect)
    pygame.draw.line(screen, GRID_LINE, (0, GRID_Y + GRID_SIZE), (WIDTH, GRID_Y + GRID_SIZE), 1)

    draw_button(bfs_button, "BFS", BTN_ACTIVE if selected_algo == "BFS" else BTN_IDLE)
    draw_button(dfs_button, "DFS", BTN_ACTIVE if selected_algo == "DFS" else BTN_IDLE)
    draw_button(astar_button, "A*", BTN_ACTIVE if selected_algo == "A*" else BTN_IDLE)
    draw_button(run_button, "Run", BTN_ACCENT)
    draw_button(play_button, "Play", BTN_ACTIVE if player_active else BTN_IDLE)
    draw_button(maze_button, "New Maze", BTN_IDLE)
    draw_button(clear_button, "Clear", BTN_WARN)
    draw_button(stop_button, "Stop", BTN_WARN if player_active or is_animating else BTN_IDLE)
    draw_button(manual_mode_button, "Manual Nodes", BTN_ACTIVE if node_mode == "MANUAL" else BTN_IDLE)
    draw_button(auto_mode_button, "Auto Nodes", BTN_ACTIVE if node_mode == "AUTO" else BTN_IDLE)

    hint = small_font.render(
        "Arrows: move player | S/G: place nodes | Enter: run | P: play | B/D/A: algorithm | V: pop-out grid",
        True,
        TEXT_DIM,
    )
    screen.blit(hint, (sv(18, 12), GRID_Y + GRID_SIZE + sv(136, 96)))


def draw_result_overlay():
    if not result_overlay:
        return

    dim_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim_surface.fill(OVERLAY_BG)
    screen.blit(dim_surface, (0, 0))

    box_w = 620
    box_h = 320
    box_x = (WIDTH - box_w) // 2
    box_y = (HEIGHT - box_h) // 2
    box = pygame.Rect(box_x, box_y, box_w, box_h)
    pygame.draw.rect(screen, (22, 29, 38), box, border_radius=16)
    pygame.draw.rect(screen, GRID_LINE, box, 2, border_radius=16)

    mode = result_overlay["mode"]
    success = result_overlay["success"]
    title = f"{mode} Completed" if success else f"{mode} Failed"
    title_color = START if success else GOAL
    screen.blit(title_font.render(title, True, title_color), (box_x + 24, box_y + 20))

    y = box_y + 78
    line1 = font.render(f"Time Taken: {result_overlay['elapsed']:.3f} s", True, TEXT)
    line2 = font.render(f"Nodes Visited: {result_overlay['nodes']}", True, TEXT)
    screen.blit(line1, (box_x + 24, y))
    screen.blit(line2, (box_x + 24, y + 36))

    if mode == "PLAYER":
        steps = result_overlay["steps"]
        line3 = font.render(f"Moves Used: {steps}", True, TEXT)
    else:
        line3 = font.render(f"Path Length: {result_overlay['path_len']}", True, TEXT)
    screen.blit(line3, (box_x + 24, y + 72))

    optimal_line = small_font.render(result_overlay["optimal_text"], True, TEXT_DIM)
    screen.blit(optimal_line, (box_x + 24, y + 124))

    if result_overlay["optimal"]:
        badge = small_font.render("Optimal", True, START)
    else:
        badge = small_font.render("Not Optimal", True, GOAL)
    screen.blit(badge, (box_x + 24, y + 154))

    close_hint = small_font.render("Press SPACE to close", True, TEXT_DIM)
    screen.blit(close_hint, (box_x + 24, box_y + box_h - 38))


def draw_scene():
    if scene == "landing":
        draw_landing_scene()
        return
    screen.fill(APP_BG)
    draw_hud()
    draw_grid()
    draw_side_controls()
    draw_controls()
    draw_result_overlay()


generate_procedural_maze()

running = True
while running:
    dt = clock.tick(120) / 1000.0

    if scene == "game":
        if baseline_dirty and not is_animating:
            compute_astar_baseline()

        if player_active and run_started_at is not None:
            run_elapsed_time = time.time() - run_started_at
        elif is_animating and run_started_at is not None:
            run_elapsed_time = time.time() - run_started_at

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        if scene == "landing":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.collidepoint(event.pos):
                    scene = "game"
                elif exit_button.collidepoint(event.pos):
                    running = False
                    break
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and result_overlay:
                clear_result_overlay()
                continue
            if result_overlay:
                continue

            if event.key == pygame.K_RETURN and not player_active and not is_animating:
                run_selected_algorithm()
            elif event.key == pygame.K_p and not is_animating:
                start_player_mode()
            elif event.key == pygame.K_b:
                selected_algo = "BFS"
            elif event.key == pygame.K_d:
                selected_algo = "DFS"
            elif event.key == pygame.K_a:
                selected_algo = "A*"
            elif event.key == pygame.K_v:
                if ROWS >= 120:
                    large_grid_popout = not large_grid_popout
            elif event.key == pygame.K_m and not is_animating:
                player_active = False
                player_pos = None
                generate_procedural_maze()
            elif event.key == pygame.K_c and not is_animating:
                player_active = False
                player_pos = None
                grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
                start_pos = None
                goal_pos = None
                clear_search_results()
                clear_result_overlay()
                invalidate_baseline()
            elif event.key == pygame.K_s and node_mode == "MANUAL" and not player_active:
                cell = get_cell_from_mouse(pygame.mouse.get_pos())
                if cell:
                    set_start(cell)
            elif event.key == pygame.K_g and node_mode == "MANUAL" and not player_active:
                cell = get_cell_from_mouse(pygame.mouse.get_pos())
                if cell:
                    set_goal(cell)

            if player_active:
                if event.key == pygame.K_UP:
                    move_player(-1, 0)
                elif event.key == pygame.K_DOWN:
                    move_player(1, 0)
                elif event.key == pygame.K_LEFT:
                    move_player(0, -1)
                elif event.key == pygame.K_RIGHT:
                    move_player(0, 1)

        if event.type == pygame.MOUSEMOTION and active_slider is not None:
            if active_slider == "visit_delay" and is_auto_speed_locked():
                continue
            slider = sliders[active_slider]
            new_value = slider_value_from_x(slider, event.pos[0])
            apply_slider_value(active_slider, new_value)
            continue

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and active_slider is not None:
            active_slider = None
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if result_overlay:
                continue
            if stop_button.collidepoint(event.pos):
                deactivate_player_mode()
                continue
            if is_animating:
                continue

            if default_settings_button.collidepoint(event.pos):
                deactivate_player_mode()
                reset_settings_to_default()
                continue

            clicked_slider = None
            for key, slider in sliders.items():
                if key == "visit_delay" and is_auto_speed_locked():
                    continue
                knob_x = slider["rect"].x + int(slider["rect"].width * slider_ratio(slider))
                knob_rect = pygame.Rect(knob_x - 12, slider["rect"].centery - 12, 24, 24)
                track_rect = pygame.Rect(slider["rect"].x, slider["rect"].y - 8, slider["rect"].width, slider["rect"].height + 16)
                if knob_rect.collidepoint(event.pos) or track_rect.collidepoint(event.pos):
                    clicked_slider = key
                    break

            if clicked_slider is not None:
                active_slider = clicked_slider
                new_value = slider_value_from_x(sliders[clicked_slider], event.pos[0])
                apply_slider_value(clicked_slider, new_value)
                continue

            if bfs_button.collidepoint(event.pos):
                selected_algo = "BFS"
            elif dfs_button.collidepoint(event.pos):
                selected_algo = "DFS"
            elif astar_button.collidepoint(event.pos):
                selected_algo = "A*"
            elif run_button.collidepoint(event.pos):
                if not player_active:
                    run_selected_algorithm()
            elif play_button.collidepoint(event.pos):
                start_player_mode()
            elif maze_button.collidepoint(event.pos):
                player_active = False
                player_pos = None
                generate_procedural_maze()
            elif clear_button.collidepoint(event.pos):
                player_active = False
                player_pos = None
                grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
                start_pos = None
                goal_pos = None
                clear_search_results()
                clear_result_overlay()
                invalidate_baseline()
            elif manual_mode_button.collidepoint(event.pos):
                node_mode = "MANUAL"
            elif auto_mode_button.collidepoint(event.pos):
                node_mode = "AUTO"
                auto_place_start_goal()
            elif not player_active:
                cell = get_cell_from_mouse(event.pos)
                if cell:
                    row, col = cell
                    if grid[row][col] in (2, 3):
                        continue
                    grid[row][col] = 0 if grid[row][col] == 1 else 1
                    clear_search_results()
                    clear_result_overlay()
                    invalidate_baseline()

    draw_scene()
    pygame.display.flip()

pygame.quit()
sys.exit()
