import pygame
import random
from collections import deque

# ============================================================
# GAME CONSTANTS
# ============================================================

TILE = 40
COLS, ROWS = 20, 15

WALL = 0
FLOOR = 1
CHEST = 2
KEY = 3
TRAP = 4

SPEED = 3
GUARD_SPEED = 2

WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + 50
FPS = 60

# Mini-map
MINIMAP_TILE = 6
MINIMAP_MARGIN = 10


# ============================================================
# WORLD GENERATION
# ============================================================

def find_path(grid, start, target):
    """Find a path between two grid cells using BFS."""
    queue = deque([start])
    visited = {start}
    parent = {start: None}

    while queue:
        current = queue.popleft()

        if current == target:
            path = []
            node = current

            while node is not None:
                path.append(node)
                node = parent[node]

            path.reverse()
            return path

        r, c = current

        neighbors = [
            (r - 1, c),
            (r + 1, c),
            (r, c - 1),
            (r, c + 1)
        ]

        for nr, nc in neighbors:
            if not (0 <= nr < ROWS and 0 <= nc < COLS):
                continue

            if grid[nr][nc] == WALL:
                continue

            if (nr, nc) in visited:
                continue

            visited.add((nr, nc))
            parent[(nr, nc)] = current
            queue.append((nr, nc))

    return []


def generate_world():
    """Generate dungeon rooms, corridors, key, chest, traps and guard."""

    grid = [[WALL] * COLS for _ in range(ROWS)]
    rooms = []

    attempts = 0

    while len(rooms) < 8 and attempts < 100:
        attempts += 1

        w = random.randint(4, 6)
        h = random.randint(4, 5)

        x = random.randint(1, COLS - w - 1)
        y = random.randint(1, ROWS - h - 1)

        room = pygame.Rect(x, y, w, h)

        overlap = any(
            room.inflate(2, 2).colliderect(existing)
            for existing in rooms
        )

        if not overlap:
            rooms.append(room)

            for ry in range(y, y + h):
                for rx in range(x, x + w):
                    grid[ry][rx] = FLOOR

    if len(rooms) < 2:
        fallback = pygame.Rect(2, 2, 5, 5)
        second = pygame.Rect(12, 8, 5, 5)

        rooms = [fallback, second]

        for room in rooms:
            for ry in range(room.y, room.y + room.height):
                for rx in range(room.x, room.x + room.width):
                    grid[ry][rx] = FLOOR

    # Connect rooms
    for i in range(len(rooms) - 1):
        ax, ay = rooms[i].centerx, rooms[i].centery
        bx, by = rooms[i + 1].centerx, rooms[i + 1].centery

        cx = ax

        while cx != bx:
            grid[ay][cx] = FLOOR
            cx += 1 if bx > cx else -1

        grid[ay][bx] = FLOOR

        cy = ay

        while cy != by:
            grid[cy][bx] = FLOOR
            cy += 1 if by > cy else -1

        grid[by][bx] = FLOOR

    # Start, key and chest
    start = rooms[0]

    chest_room = rooms[-1]
    key_room = rooms[-2]

    chest_pos = (
        chest_room.centery,
        chest_room.centerx
    )

    key_pos = (
        key_room.centery,
        key_room.centerx
    )

    grid[chest_pos[0]][chest_pos[1]] = CHEST
    grid[key_pos[0]][key_pos[1]] = KEY

    # --------------------------------------------------------
    # SAFE PATH
    # --------------------------------------------------------

    start_cell = (
        start.centery,
        start.centerx
    )

    path_to_key = find_path(
        grid,
        start_cell,
        key_pos
    )

    path_to_chest = find_path(
        grid,
        key_pos,
        chest_pos
    )

    safe_path = set(
        path_to_key + path_to_chest
    )

    # --------------------------------------------------------
    # GUARD PATROL
    # --------------------------------------------------------

    guard_y = chest_room.centery * TILE + 7

    guard_x1 = chest_room.left * TILE + 7
    guard_x2 = (chest_room.right - 1) * TILE + 7

    guard_points = [
        (guard_x1, guard_y),
        (guard_x2, guard_y)
    ]

    # --------------------------------------------------------
    # TRAPS
    # --------------------------------------------------------

    trap_candidates = []

    for r in range(ROWS):
        for c in range(COLS):

            if grid[r][c] != FLOOR:
                continue

            if (r, c) in safe_path:
                continue

            if start.collidepoint(c, r):
                continue

            if r == chest_room.centery:
                continue

            trap_candidates.append((r, c))

    random.shuffle(trap_candidates)

    trap_count = min(
        8,
        len(trap_candidates)
    )

    for r, c in trap_candidates[:trap_count]:
        grid[r][c] = TRAP

    return grid, start, guard_points


# ============================================================
# COLORS
# ============================================================

COLORS = {
    WALL: (60, 50, 70),
    FLOOR: (200, 190, 170),
    CHEST: (200, 160, 30),
    KEY: (220, 220, 60),
    TRAP: (170, 45, 45),
}


# ============================================================
# PLAYER
# ============================================================

class Player:

    def __init__(self, x, y):
        self.rect = pygame.Rect(
            x,
            y,
            28,
            28
        )

        self.color = (60, 120, 220)

        self.has_key = False

    def move(self, keys, grid, rows, cols):
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -SPEED

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = SPEED

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -SPEED

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = SPEED

        self._try_move(
            dx,
            0,
            grid,
            rows,
            cols
        )

        self._try_move(
            0,
            dy,
            grid,
            rows,
            cols
        )

    def _try_move(self, dx, dy, grid, rows, cols):
        new = self.rect.move(dx, dy)

        corners = [
            (new.left, new.top),
            (new.right - 1, new.top),
            (new.left, new.bottom - 1),
            (new.right - 1, new.bottom - 1)
        ]

        for px, py in corners:
            c = px // TILE
            r = py // TILE

            if not (0 <= r < rows and 0 <= c < cols):
                return

            if grid[r][c] == WALL:
                return

        self.rect = new

    def draw(self, screen):
        pygame.draw.ellipse(
            screen,
            self.color,
            self.rect
        )

        # Small key indicator beside player
        if self.has_key:
            pygame.draw.circle(
                screen,
                (220, 220, 60),
                (
                    self.rect.right - 6,
                    self.rect.top + 6
                ),
                5
            )


# ============================================================
# GUARD
# ============================================================

class Guard:

    def __init__(self, point1, point2):
        self.rect = pygame.Rect(
            point1[0],
            point1[1],
            26,
            26
        )

        self.left_limit = min(
            point1[0],
            point2[0]
        )

        self.right_limit = max(
            point1[0],
            point2[0]
        )

        self.speed = GUARD_SPEED
        self.direction = 1
        self.color = (190, 60, 60)

    def update(self):
        self.rect.x += (
            self.speed * self.direction
        )

        if self.rect.x >= self.right_limit:
            self.rect.x = self.right_limit
            self.direction = -1

        elif self.rect.x <= self.left_limit:
            self.rect.x = self.left_limit
            self.direction = 1

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.color,
            self.rect,
            border_radius=6
        )

        pygame.draw.circle(
            screen,
            (240, 220, 220),
            (
                self.rect.centerx - 5,
                self.rect.centery - 4
            ),
            3
        )

        pygame.draw.circle(
            screen,
            (240, 220, 220),
            (
                self.rect.centerx + 5,
                self.rect.centery - 4
            ),
            3
        )


# ============================================================
# GAME ENGINE
# ============================================================

class GameEngine:

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        pygame.display.set_caption(
            "Treasure Hunt"
        )

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(
            "monospace",
            24
        )

        self.big_font = pygame.font.SysFont(
            "monospace",
            40,
            bold=True
        )

        self.reset()

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    def reset(self):
        (
            self.grid,
            start,
            guard_points
        ) = generate_world()

        if start:
            sx = start.x * TILE + 6
            sy = start.y * TILE + 6
        else:
            sx = TILE + 6
            sy = TILE + 6

        self.start_pos = (
            sx,
            sy
        )

        self.player = Player(
            sx,
            sy
        )

        self.guard = Guard(
            guard_points[0],
            guard_points[1]
        )

        self.won = False

        self.status = (
            "Find the KEY, then the CHEST!"
        )

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
            ):
                self.reset()

        return True

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update(self):
        if self.won:
            return

        keys = pygame.key.get_pressed()

        self.player.move(
            keys,
            self.grid,
            ROWS,
            COLS
        )

        self.guard.update()

        # Guard collision
        if self.player.rect.colliderect(
            self.guard.rect
        ):
            self.player.rect.topleft = (
                self.start_pos
            )

            self.status = (
                "The guard caught you! "
                "Back to the start!"
            )

            return

        pr = (
            self.player.rect.centery
            // TILE
        )

        pc = (
            self.player.rect.centerx
            // TILE
        )

        if not (
            0 <= pr < ROWS
            and 0 <= pc < COLS
        ):
            return

        cell = self.grid[pr][pc]

        # Trap
        if cell == TRAP:
            self.player.rect.topleft = (
                self.start_pos
            )

            self.status = (
                "Ouch! You triggered a trap! "
                "Back to the start!"
            )

            return

        # Key
        if cell == KEY:
            self.player.has_key = True

            self.grid[pr][pc] = FLOOR

            self.status = (
                "Got the key! Find the CHEST!"
            )

        # Chest
        elif cell == CHEST:
            if self.player.has_key:
                self.won = True

                self.status = (
                    "Treasure found!"
                )

    # --------------------------------------------------------
    # MINI-MAP
    # --------------------------------------------------------

    def draw_minimap(self):
        """Draw the real-time dungeon mini-map."""

        map_width = (
            COLS * MINIMAP_TILE
        )

        map_height = (
            ROWS * MINIMAP_TILE
        )

        panel = pygame.Rect(
            WIDTH
            - map_width
            - MINIMAP_MARGIN * 2,

            MINIMAP_MARGIN,

            map_width
            + MINIMAP_MARGIN * 2,

            map_height
            + MINIMAP_MARGIN * 2
        )

        pygame.draw.rect(
            self.screen,
            (15, 15, 25),
            panel
        )

        pygame.draw.rect(
            self.screen,
            (220, 220, 220),
            panel,
            2
        )

        for r in range(ROWS):
            for c in range(COLS):

                cell = self.grid[r][c]

                if cell == WALL:
                    color = (45, 40, 55)
                else:
                    color = (180, 170, 150)

                mini_rect = pygame.Rect(
                    panel.left
                    + MINIMAP_MARGIN
                    + c * MINIMAP_TILE,

                    panel.top
                    + MINIMAP_MARGIN
                    + r * MINIMAP_TILE,

                    MINIMAP_TILE,
                    MINIMAP_TILE
                )

                pygame.draw.rect(
                    self.screen,
                    color,
                    mini_rect
                )

        # Player position
        player_row = (
            self.player.rect.centery
            // TILE
        )

        player_col = (
            self.player.rect.centerx
            // TILE
        )

        if (
            0 <= player_row < ROWS
            and 0 <= player_col < COLS
        ):

            player_rect = pygame.Rect(
                panel.left
                + MINIMAP_MARGIN
                + player_col * MINIMAP_TILE,

                panel.top
                + MINIMAP_MARGIN
                + player_row * MINIMAP_TILE,

                MINIMAP_TILE,
                MINIMAP_TILE
            )

            pygame.draw.rect(
                self.screen,
                (60, 120, 255),
                player_rect
            )

    # --------------------------------------------------------
    # INVENTORY HUD
    # --------------------------------------------------------

    def draw_inventory(self):
        """Draw the key inventory slot."""

        # Inventory label
        label = self.font.render(
            "INVENTORY",
            True,
            (200, 200, 200)
        )

        self.screen.blit(
            label,
            (WIDTH - 190, ROWS * TILE + 5)
        )

        # Inventory slot
        slot = pygame.Rect(
            WIDTH - 65,
            ROWS * TILE + 5,
            40,
            40
        )

        pygame.draw.rect(
            self.screen,
            (45, 45, 60),
            slot
        )

        pygame.draw.rect(
            self.screen,
            (180, 180, 190),
            slot,
            2
        )

        # Draw key when collected
        if self.player.has_key:

            center_x = slot.centerx
            center_y = slot.centery

            # Key ring
            pygame.draw.circle(
                self.screen,
                (255, 220, 60),
                (center_x - 5, center_y - 5),
                7,
                3
            )

            # Key shaft
            pygame.draw.line(
                self.screen,
                (255, 220, 60),
                (center_x, center_y),
                (center_x + 11, center_y + 11),
                4
            )

            # Key teeth
            pygame.draw.line(
                self.screen,
                (255, 220, 60),
                (
                    center_x + 6,
                    center_y + 6
                ),
                (
                    center_x + 6,
                    center_y + 12
                ),
                3
            )

            pygame.draw.line(
                self.screen,
                (255, 220, 60),
                (
                    center_x + 10,
                    center_y + 10
                ),
                (
                    center_x + 10,
                    center_y + 15
                ),
                3
            )

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    def draw(self):
        self.screen.fill(
            (30, 25, 40)
        )

        # Dungeon
        for r in range(ROWS):
            for c in range(COLS):

                cell = self.grid[r][c]

                rect = pygame.Rect(
                    c * TILE,
                    r * TILE,
                    TILE,
                    TILE
                )

                pygame.draw.rect(
                    self.screen,
                    COLORS[cell],
                    rect
                )

                # Key
                if cell == KEY:

                    pygame.draw.circle(
                        self.screen,
                        (255, 240, 60),
                        (
                            c * TILE + TILE // 2,
                            r * TILE + TILE // 2
                        ),
                        10
                    )

                # Chest
                elif cell == CHEST:

                    pygame.draw.rect(
                        self.screen,
                        (180, 120, 20),
                        rect.inflate(-12, -12),
                        border_radius=4
                    )

                # Trap
                elif cell == TRAP:

                    trap_rect = rect.inflate(
                        -10,
                        -10
                    )

                    pygame.draw.rect(
                        self.screen,
                        (150, 35, 35),
                        trap_rect,
                        border_radius=4
                    )

                    pygame.draw.line(
                        self.screen,
                        (240, 210, 210),
                        trap_rect.topleft,
                        trap_rect.bottomright,
                        3
                    )

                    pygame.draw.line(
                        self.screen,
                        (240, 210, 210),
                        trap_rect.topright,
                        trap_rect.bottomleft,
                        3
                    )

        # Guard
        self.guard.draw(
            self.screen
        )

        # Player
        self.player.draw(
            self.screen
        )

        # Mini-map
        self.draw_minimap()

        # ----------------------------------------------------
        # HUD
        # ----------------------------------------------------

        hud = pygame.Rect(
            0,
            ROWS * TILE,
            WIDTH,
            50
        )

        pygame.draw.rect(
            self.screen,
            (20, 20, 35),
            hud
        )

        # Status text
        st = self.font.render(
            self.status,
            True,
            (200, 200, 200)
        )

        self.screen.blit(
            st,
            (8, ROWS * TILE + 13)
        )

        # Restart text
        restart = self.font.render(
            "R=Restart",
            True,
            (150, 150, 150)
        )

        self.screen.blit(
            restart,
            (
                WIDTH - 310,
                ROWS * TILE + 13
            )
        )

        # Inventory
        self.draw_inventory()

        # ----------------------------------------------------
        # WIN SCREEN
        # ----------------------------------------------------

        if self.won:

            overlay = pygame.Surface(
                (WIDTH, ROWS * TILE),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 140)
            )

            self.screen.blit(
                overlay,
                (0, 0)
            )

            msg = self.big_font.render(
                "TREASURE FOUND!",
                True,
                (220, 180, 30)
            )

            sub = self.font.render(
                "Press R to Play Again",
                True,
                (180, 180, 180)
            )

            self.screen.blit(
                msg,
                (
                    WIDTH // 2
                    - msg.get_width() // 2,

                    ROWS * TILE // 2
                    - 30
                )
            )

            self.screen.blit(
                sub,
                (
                    WIDTH // 2
                    - sub.get_width() // 2,

                    ROWS * TILE // 2
                    + 20
                )
            )

        pygame.display.flip()

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    def run(self):
        running = True

        while running:

            running = self.handle_events()

            self.update()

            self.draw()

            self.clock.tick(FPS)

        pygame.quit()


# ============================================================
# START GAME
# ============================================================

if __name__ == "__main__":
    engine = GameEngine()
    engine.run()