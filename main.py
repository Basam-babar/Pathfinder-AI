import pygame
import sys
import random
from collections import deque
import heapq

# --- CONFIGURATION & COLORS ---
pygame.init()

# Layout Dimensions
GRID_WIDTH, GRID_HEIGHT = 800, 600
UI_WIDTH = 250
WIDTH, HEIGHT = GRID_WIDTH + UI_WIDTH, GRID_HEIGHT
ROWS, COLS = 30, 40
CELL_SIZE = GRID_WIDTH // COLS

# Modern Color Palette
BG_COLOR = (245, 247, 250)
GRID_LINE_COLOR = (220, 225, 230)
PANEL_COLOR = (43, 48, 58)
TEXT_COLOR = (255, 255, 255)

START_COLOR = (46, 204, 113)      # Green
TARGET_COLOR = (52, 152, 219)     # Blue
WALL_COLOR = (44, 62, 80)         # Dark Blue/Gray
DYN_WALL_COLOR = (155, 89, 182)   # Purple
FRONTIER_COLOR = (243, 156, 18)   # Orange
EXPLORED_COLOR = (174, 214, 241)  # Light Blue
PATH_COLOR = (241, 196, 15)       # Yellow
AGENT_COLOR = (231, 76, 60)       # Red

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GOOD PERFORMANCE TIME APP") # Mandatory Title

font_sm = pygame.font.SysFont("Segoe UI", 14, bold=True)
font_md = pygame.font.SysFont("Segoe UI", 18, bold=True)
font_lg = pygame.font.SysFont("Segoe UI", 24, bold=True)

# Clockwise 8-way directions (Up, Top-Right, Right, Bottom-Right, Bottom, Bottom-Left, Left, Top-Left)
DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

# --- UI CLASSES ---

class Button:
    def __init__(self, x, y, width, height, text, default_color, hover_color, action_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.default_color = default_color
        self.hover_color = hover_color
        self.action_val = action_val
        self.is_hovered = False

    def draw(self, win):
        color = self.hover_color if self.is_hovered else self.default_color
        pygame.draw.rect(win, color, self.rect, border_radius=5)
        pygame.draw.rect(win, (20, 25, 30), self.rect, 2, border_radius=5)
        
        text_surf = font_sm.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        win.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(pos):
                return self.action_val
        return None

# --- CORE PATHFINDING LOGIC ---

def get_neighbors(node, grid):
    x, y = node
    neighbors = []
    for dx, dy in DIRECTIONS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS and grid[ny][nx] != 1:
            neighbors.append((nx, ny))
    return neighbors

def reconstruct_path(came_from, current):
    path = []
    while current in came_from and came_from[current] is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

# Generator Algorithms (Yield states for animation)
def bfs(start, target, grid):
    queue = deque([start])
    came_from = {start: None}
    explored = set([start])
    frontier_set = set([start])

    while queue:
        current = queue.popleft()
        frontier_set.remove(current)

        if current == target:
            yield "FOUND", reconstruct_path(came_from, current), explored, frontier_set; return
        for nxt in get_neighbors(current, grid):
            if nxt not in explored:
                explored.add(nxt)
                frontier_set.add(nxt)
                came_from[nxt] = current
                queue.append(nxt)
        yield "SEARCHING", None, explored, frontier_set
    yield "NOT_FOUND", None, explored, frontier_set

def dfs(start, target, grid):
    stack = [start]
    came_from = {start: None}
    explored = set()
    frontier_set = set([start])

    while stack:
        current = stack.pop()
        if current in frontier_set: frontier_set.remove(current)
        if current in explored: continue
        explored.add(current)

        if current == target:
            yield "FOUND", reconstruct_path(came_from, current), explored, frontier_set; return
        for nxt in reversed(get_neighbors(current, grid)):
            if nxt not in explored:
                frontier_set.add(nxt)
                if nxt not in came_from or came_from[nxt] is None: came_from[nxt] = current
                stack.append(nxt)
        yield "SEARCHING", None, explored, frontier_set
    yield "NOT_FOUND", None, explored, frontier_set

def ucs(start, target, grid):
    pq = [(0, start)]
    came_from = {start: None}
    cost_so_far = {start: 0}
    explored = set()
    frontier_set = set([start])

    while pq:
        current_cost, current = heapq.heappop(pq)
        if current in frontier_set: frontier_set.remove(current)
        if current in explored: continue
        explored.add(current)

        if current == target:
            yield "FOUND", reconstruct_path(came_from, current), explored, frontier_set; return
        for nxt in get_neighbors(current, grid):
            dx, dy = abs(current[0] - nxt[0]), abs(current[1] - nxt[1])
            step_cost = 1.414 if dx == 1 and dy == 1 else 1.0
            new_cost = cost_so_far[current] + step_cost
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                came_from[nxt] = current
                frontier_set.add(nxt)
                heapq.heappush(pq, (new_cost, nxt))
        yield "SEARCHING", None, explored, frontier_set
    yield "NOT_FOUND", None, explored, frontier_set

def dls(start, target, grid, limit):
    stack = [(start, 0)]
    came_from = {start: None}
    explored = {}
    frontier_set = set([start])

    while stack:
        current, depth = stack.pop()
        if current in frontier_set: frontier_set.remove(current)
        if current in explored and explored[current] <= depth: continue
        explored[current] = depth

        if current == target:
            yield "FOUND", reconstruct_path(came_from, current), set(explored.keys()), frontier_set; return
        if depth < limit:
            for nxt in reversed(get_neighbors(current, grid)):
                if nxt not in explored or explored[nxt] > depth + 1:
                    frontier_set.add(nxt)
                    came_from[nxt] = current
                    stack.append((nxt, depth + 1))
        yield "SEARCHING", None, set(explored.keys()), frontier_set
    yield "NOT_FOUND", None, set(explored.keys()), frontier_set

def iddfs(start, target, grid):
    limit = 0
    while limit < ROWS * COLS:
        for status, path, exp, front in dls(start, target, grid, limit):
            if status == "FOUND": yield "FOUND", path, exp, front; return
            yield "SEARCHING", None, exp, front
        limit += 1
    yield "NOT_FOUND", None, set(), set()

def bidirectional(start, target, grid):
    queue_fwd, queue_bwd = deque([start]), deque([target])
    came_from_fwd, came_from_bwd = {start: None}, {target: None}
    explored_fwd, explored_bwd = set([start]), set([target])
    front_fwd, front_bwd = set([start]), set([target])

    while queue_fwd and queue_bwd:
        curr_f = queue_fwd.popleft()
        if curr_f in front_fwd: front_fwd.remove(curr_f)
        if curr_f in explored_bwd:
            p_fwd = reconstruct_path(came_from_fwd, curr_f)
            p_bwd = reconstruct_path(came_from_bwd, curr_f)
            p_bwd.reverse()
            yield "FOUND", p_fwd + p_bwd[1:], explored_fwd.union(explored_bwd), front_fwd.union(front_bwd); return
        for nxt in get_neighbors(curr_f, grid):
            if nxt not in explored_fwd:
                explored_fwd.add(nxt); front_fwd.add(nxt); came_from_fwd[nxt] = curr_f; queue_fwd.append(nxt)

        curr_b = queue_bwd.popleft()
        if curr_b in front_bwd: front_bwd.remove(curr_b)
        if curr_b in explored_fwd:
            p_fwd = reconstruct_path(came_from_fwd, curr_b)
            p_bwd = reconstruct_path(came_from_bwd, curr_b)
            p_bwd.reverse()
            yield "FOUND", p_fwd + p_bwd[1:], explored_fwd.union(explored_bwd), front_fwd.union(front_bwd); return
        for nxt in get_neighbors(curr_b, grid):
            if nxt not in explored_bwd:
                explored_bwd.add(nxt); front_bwd.add(nxt); came_from_bwd[nxt] = curr_b; queue_bwd.append(nxt)

        yield "SEARCHING", None, explored_fwd.union(explored_bwd), front_fwd.union(front_bwd)
    yield "NOT_FOUND", None, explored_fwd.union(explored_bwd), front_fwd.union(front_bwd)

# --- RENDERING ---

def draw_legend_item(win, x, y, color, text):
    pygame.draw.rect(win, color, (x, y, 15, 15), border_radius=3)
    surf = font_sm.render(text, True, TEXT_COLOR)
    win.blit(surf, (x + 25, y))

def draw_ui_panel(win, buttons, state_text, current_algo_name, path_len, speed):
    pygame.draw.rect(win, PANEL_COLOR, (GRID_WIDTH, 0, UI_WIDTH, HEIGHT))
    
    # Title
    title = font_lg.render("PATHFINDER AI", True, (255, 215, 0))
    win.blit(title, (GRID_WIDTH + 25, 20))
    
    # Status Board
    pygame.draw.rect(win, (30, 35, 45), (GRID_WIDTH + 15, 60, UI_WIDTH - 30, 90), border_radius=8)
    win.blit(font_sm.render(f"State: {state_text}", True, TEXT_COLOR), (GRID_WIDTH + 25, 70))
    win.blit(font_sm.render(f"Algorithm: {current_algo_name}", True, TEXT_COLOR), (GRID_WIDTH + 25, 95))
    win.blit(font_sm.render(f"Path Length: {path_len}", True, TEXT_COLOR), (GRID_WIDTH + 25, 120))
    
    # Draw Buttons
    for btn in buttons:
        btn.draw(win)
        
    # Legend
    leg_x, leg_y = GRID_WIDTH + 20, 500
    win.blit(font_md.render("Legend:", True, TEXT_COLOR), (leg_x, leg_y - 30))
    draw_legend_item(win, leg_x, leg_y, START_COLOR, "Start Node")
    draw_legend_item(win, leg_x, leg_y + 25, TARGET_COLOR, "Target Node")
    draw_legend_item(win, leg_x, leg_y + 50, WALL_COLOR, "Static Wall")
    draw_legend_item(win, leg_x + 100, leg_y, DYN_WALL_COLOR, "Dynamic Wall")
    draw_legend_item(win, leg_x + 100, leg_y + 25, FRONTIER_COLOR, "Frontier")
    draw_legend_item(win, leg_x + 100, leg_y + 50, EXPLORED_COLOR, "Explored")

def draw_grid(win, grid, start, target, explored, frontier, path, agent, dynamic_walls):
    win.fill(BG_COLOR)
    for y in range(ROWS):
        for x in range(COLS):
            rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            # Base Grid Lines
            pygame.draw.rect(win, GRID_LINE_COLOR, rect, 1)

            if grid[y][x] == 1:
                color = DYN_WALL_COLOR if (x, y) in dynamic_walls else WALL_COLOR
                pygame.draw.rect(win, color, rect, border_radius=3)
            elif (x, y) in path:
                pygame.draw.rect(win, PATH_COLOR, rect)
            elif (x, y) in frontier:
                pygame.draw.rect(win, FRONTIER_COLOR, rect)
            elif (x, y) in explored:
                pygame.draw.rect(win, EXPLORED_COLOR, rect)
            
            # Start and Target (Drawn last to be on top)
            if (x, y) == start:
                pygame.draw.rect(win, START_COLOR, rect, border_radius=5)
            elif (x, y) == target:
                pygame.draw.rect(win, TARGET_COLOR, rect, border_radius=5)

    if agent:
        center = (agent[0]*CELL_SIZE + CELL_SIZE//2, agent[1]*CELL_SIZE + CELL_SIZE//2)
        pygame.draw.circle(win, AGENT_COLOR, center, CELL_SIZE//2 - 2)

# --- MAIN LOOP ---

def main():
    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    start = (5, ROWS // 2)
    target = (COLS - 5, ROWS // 2)
    
    explored, frontier, path, dynamic_walls = set(), set(), [], set()
    agent = None
    state = "IDLE" 
    algo_generator = None
    current_algo_name = "None"
    current_algo_func = None
    search_speed = 60
    
    clock = pygame.time.Clock()

    # Create Buttons
    btn_color = (60, 70, 85)
    btn_hover = (85, 95, 110)
    act_color = (192, 57, 43)
    act_hover = (231, 76, 60)
    
    buttons = [
        Button(GRID_WIDTH + 15, 170, 105, 35, "BFS", btn_color, btn_hover, "BFS"),
        Button(GRID_WIDTH + 130, 170, 105, 35, "DFS", btn_color, btn_hover, "DFS"),
        Button(GRID_WIDTH + 15, 215, 105, 35, "UCS", btn_color, btn_hover, "UCS"),
        Button(GRID_WIDTH + 130, 215, 105, 35, "DLS", btn_color, btn_hover, "DLS"),
        Button(GRID_WIDTH + 15, 260, 105, 35, "IDDFS", btn_color, btn_hover, "IDDFS"),
        Button(GRID_WIDTH + 130, 260, 105, 35, "Bi-Dir", btn_color, btn_hover, "BIDIR"),
        
        Button(GRID_WIDTH + 15, 320, 70, 30, "Slow", (39, 174, 96), (46, 204, 113), "SPD_15"),
        Button(GRID_WIDTH + 90, 320, 70, 30, "Norm", (39, 174, 96), (46, 204, 113), "SPD_60"),
        Button(GRID_WIDTH + 165, 320, 70, 30, "Fast", (39, 174, 96), (46, 204, 113), "SPD_0"),
        
        Button(GRID_WIDTH + 15, 370, 220, 40, "Clear Path", btn_color, btn_hover, "CLEAR_PATH"),
        Button(GRID_WIDTH + 15, 420, 220, 40, "Clear All Walls", act_color, act_hover, "CLEAR_ALL"),
    ]

    def start_search(name, func):
        nonlocal state, algo_generator, explored, frontier, path, agent, start, current_algo_name, current_algo_func
        explored.clear(); frontier.clear(); path.clear()
        agent = None
        state = "SEARCHING"
        current_algo_name = name
        current_algo_func = func
        algo_generator = func(start, target, grid)

    dragging_start = False
    dragging_target = False

    run = True
    while run:
        # Dynamic Obstacle Spawning
        if state in ["SEARCHING", "MOVING"] and random.random() < 0.03:
            rx, ry = random.randint(0, COLS-1), random.randint(0, ROWS-1)
            if (rx, ry) != start and (rx, ry) != target and grid[ry][rx] == 0 and (rx, ry) != agent:
                grid[ry][rx] = 1
                dynamic_walls.add((rx, ry))
                
                # RE-PLANNING
                if state == "MOVING" and (rx, ry) in path:
                    state = "RE-PLANNING"
                    start = agent
                    start_search(current_algo_name, current_algo_func)

        pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            # Button Interactions
            for btn in buttons:
                btn.check_hover(pos)
                action = btn.is_clicked(pos, event)
                if action:
                    if action == "BFS": start_search("BFS", bfs)
                    elif action == "DFS": start_search("DFS", dfs)
                    elif action == "UCS": start_search("UCS", ucs)
                    elif action == "DLS": start_search("DLS (Depth 25)", lambda s, t, g: dls(s, t, g, 25))
                    elif action == "IDDFS": start_search("IDDFS", iddfs)
                    elif action == "BIDIR": start_search("Bi-Directional", bidirectional)
                    elif action == "SPD_15": search_speed = 15
                    elif action == "SPD_60": search_speed = 60
                    elif action == "SPD_0": search_speed = 0 # Instant
                    elif action == "CLEAR_PATH":
                        explored.clear(); frontier.clear(); path.clear(); agent = None; state = "IDLE"
                    elif action == "CLEAR_ALL":
                        grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
                        dynamic_walls.clear(); explored.clear(); frontier.clear(); path.clear()
                        agent = None; state = "IDLE"

            # Node Dragging Logic
            if state == "IDLE":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    col, row = pos[0] // CELL_SIZE, pos[1] // CELL_SIZE
                    if (col, row) == start: dragging_start = True
                    elif (col, row) == target: dragging_target = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging_start = False
                    dragging_target = False

            # Grid Drawing Logic
            if state == "IDLE" and pos[0] < GRID_WIDTH:
                col, row = pos[0] // CELL_SIZE, pos[1] // CELL_SIZE
                if pygame.mouse.get_pressed()[0]: # Left Click Draw/Drag
                    if dragging_start and grid[row][col] == 0 and (col, row) != target:
                        start = (col, row)
                    elif dragging_target and grid[row][col] == 0 and (col, row) != start:
                        target = (col, row)
                    elif not dragging_start and not dragging_target and (col, row) != start and (col, row) != target:
                        grid[row][col] = 1
                elif pygame.mouse.get_pressed()[2]: # Right Click Erase
                    grid[row][col] = 0

        # State Handling (Search Animation)
        if state == "SEARCHING":
            try:
                # If speed is 0, exhaust the generator instantly
                if search_speed == 0:
                    while True:
                        status, res_path, explored, frontier = next(algo_generator)
                        if status != "SEARCHING": break
                else:
                    status, res_path, explored, frontier = next(algo_generator)

                if status == "FOUND":
                    path = res_path
                    state = "MOVING"
                    agent = start
                elif status == "NOT_FOUND":
                    state = "NO PATH"
            except StopIteration:
                state = "IDLE"

        # Moving Agent Animation
        elif state == "MOVING":
            if path:
                agent = path.pop(0)
                if agent == target:
                    state = "IDLE"
                    start = target 
            else:
                state = "IDLE"

        # Render everything
        draw_grid(WIN, grid, start, target, explored, frontier, path, agent, dynamic_walls)
        draw_ui_panel(WIN, buttons, state, current_algo_name, len(path) if state == "MOVING" or state == "IDLE" and path else "-", search_speed)
        pygame.display.update()
        
        # Framerate Control
        if state == "SEARCHING" and search_speed > 0: clock.tick(search_speed)
        elif state == "MOVING": clock.tick(15) # Slower movement to watch the agent
        else: clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()