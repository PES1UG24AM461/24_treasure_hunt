import pygame
import random

TILE = 40
COLS, ROWS = 20, 15

WALL, FLOOR, CHEST, KEY, TRAP = 0, 1, 2, 3, 4

SPEED = 3
GUARD_SPEED = 2

WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + 50
FPS = 60


def generate_world():
    grid = [[WALL] * COLS for _ in range(ROWS)]
    rooms = []

    # ---------------------------------------------------------
    # Generate rooms
    # ---------------------------------------------------------
    attempts = 0

    while len(rooms) < 8 and attempts < 100:
        attempts += 1

        # Make every room reasonably sized.
        w = random.randint(4, 6)
        h = random.randint(4, 5)

        x = random.randint(1, COLS - w - 1)
        y = random.randint(1, ROWS - h - 1)

        room = pygame.Rect(x, y, w, h)

        overlap = any(
            room.inflate(2, 2).colliderect(r)
            for r in rooms
        )

        if not overlap:
            rooms.append(room)

            for ry in range(y, y + h):
                for rx in range(x, x + w):
                    grid[ry][rx] = FLOOR

    # ---------------------------------------------------------
    # Connect rooms
    # ---------------------------------------------------------
    for i in range(len(rooms) - 1):

        ax = rooms[i].centerx
        ay = rooms[i].centery

        bx = rooms[i + 1].centerx
        by = rooms[i + 1].centery

        cx = ax

        while cx != bx:
            grid[ay][cx] = FLOOR
            cx += 1 if bx > cx else -1

        cy = ay

        while cy != by:
            grid[cy][bx] = FLOOR
            cy += 1 if by > cy else -1

    # ---------------------------------------------------------
    # Start, key and chest
    # ---------------------------------------------------------
    start = rooms[0] if rooms else None

    if len(rooms) >= 2:

        key_room = rooms[-2]
        chest_room = rooms[-1]

        key_x = key_room.centerx
        key_y = key_room.centery

        chest_x = chest_room.centerx
        chest_y = chest_room.centery

        grid[key_y][key_x] = KEY
        grid[chest_y][chest_x] = CHEST

    # ---------------------------------------------------------
    # TASK 2
    # GUARANTEED guard patrol points.
    # ---------------------------------------------------------
    guard_points = []

    if len(rooms) >= 2:

        chest_room = rooms[-1]

        # Use the row immediately above the chest.
        patrol_y = chest_room.centery - 1

        # Make sure it is inside the room.
        if patrol_y <= chest_room.top:
            patrol_y = chest_room.centery + 1

        # Calculate two points inside the room.
        left_x = chest_room.left * TILE + 7
        right_x = (
            (chest_room.right - 1) * TILE - 33
        )

        # Make absolutely sure the two points differ.
        if right_x <= left_x:
            left_x = chest_room.left * TILE + 7
            right_x = left_x + TILE

        guard_points = [
            (left_x, patrol_y * TILE + 7),
            (right_x, patrol_y * TILE + 7)
        ]

    # ---------------------------------------------------------
    # Find safe path START -> KEY -> CHEST
    # ---------------------------------------------------------
    if start and len(rooms) >= 2:

        start_pos = (
            start.centery,
            start.centerx
        )

        key_pos = (
            rooms[-2].centery,
            rooms[-2].centerx
        )

        chest_pos = (
            rooms[-1].centery,
            rooms[-1].centerx
        )

        def find_path(source, target):

            queue = [source]
            visited = {source}
            parent = {}

            while queue:

                current = queue.pop(0)

                if current == target:

                    path = []
                    node = current

                    while node != source:
                        path.append(node)
                        node = parent[node]

                    path.append(source)

                    return set(path)

                r, c = current

                neighbours = [
                    (r - 1, c),
                    (r + 1, c),
                    (r, c - 1),
                    (r, c + 1)
                ]

                for nr, nc in neighbours:

                    if not (0 <= nr < ROWS):
                        continue

                    if not (0 <= nc < COLS):
                        continue

                    if (nr, nc) in visited:
                        continue

                    if grid[nr][nc] == WALL:
                        continue

                    visited.add((nr, nc))
                    parent[(nr, nc)] = current
                    queue.append((nr, nc))

            return set()

        safe_path = set()

        safe_path.update(
            find_path(start_pos, key_pos)
        )

        safe_path.update(
            find_path(key_pos, chest_pos)
        )

    else:
        safe_path = set()

    # ---------------------------------------------------------
    # TASK 1
    # Place traps away from safe path and guard.
    # ---------------------------------------------------------
    guard_tiles = set()

    if len(guard_points) == 2:

        gx1, gy1 = guard_points[0]
        gx2, gy2 = guard_points[1]

        patrol_row = gy1 // TILE

        left_col = min(gx1, gx2) // TILE
        right_col = max(gx1, gx2) // TILE

        for c in range(
            left_col - 1,
            right_col + 2
        ):

            if 0 <= c < COLS:
                guard_tiles.add(
                    (patrol_row, c)
                )

    trap_candidates = []

    for r in range(ROWS):

        for c in range(COLS):

            if grid[r][c] != FLOOR:
                continue

            # Don't trap the starting room.
            if start and start.collidepoint(c, r):
                continue

            # Don't trap the safe route.
            if (r, c) in safe_path:
                continue

            # Don't trap the guard's patrol area.
            if (r, c) in guard_tiles:
                continue

            trap_candidates.append((r, c))

    random.shuffle(trap_candidates)

    for r, c in trap_candidates[:3]:
        grid[r][c] = TRAP

    return grid, start, guard_points


# =============================================================
# COLORS
# =============================================================

COLORS = {
    WALL: (60, 50, 70),
    FLOOR: (200, 190, 170),
    CHEST: (200, 160, 30),
    KEY: (220, 220, 60),
    TRAP: (170, 50, 50),
}


# =============================================================
# PLAYER
# =============================================================

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

        new = self.rect.move(
            dx,
            dy
        )

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


# =============================================================
# TASK 2 — GUARD
# =============================================================

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

        # Move horizontally every frame.
        self.rect.x += (
            self.speed * self.direction
        )

        # Hit right patrol point.
        if self.rect.x >= self.right_limit:

            self.rect.x = self.right_limit

            self.direction = -1

        # Hit left patrol point.
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

        # Eyes
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


# =============================================================
# GAME ENGINE
# =============================================================

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

        # -----------------------------------------------------
        # TASK 2 — Create guard.
        # -----------------------------------------------------

        self.guard = Guard(
            guard_points[0],
            guard_points[1]
        )

        self.won = False

        self.status = (
            "Find the KEY, then the CHEST!"
        )

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

    def update(self):

        if self.won:
            return

        # -----------------------------------------------------
        # Player movement
        # -----------------------------------------------------

        keys = pygame.key.get_pressed()

        self.player.move(
            keys,
            self.grid,
            ROWS,
            COLS
        )

        # -----------------------------------------------------
        # TASK 2 — Guard movement.
        # -----------------------------------------------------

        self.guard.update()

        # -----------------------------------------------------
        # TASK 2 — Guard collision.
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Player tile.
        # -----------------------------------------------------

        pr = (
            self.player.rect.centery
            // TILE
        )

        pc = (
            self.player.rect.centerx
            // TILE
        )

        if 0 <= pr < ROWS and 0 <= pc < COLS:

            cell = self.grid[pr][pc]

            # -------------------------------------------------
            # TASK 1 — Trap.
            # -------------------------------------------------

            if cell == TRAP:

                self.player.rect.topleft = (
                    self.start_pos
                )

                self.status = (
                    "Ouch! You triggered a trap! "
                    "Back to the start!"
                )

            # -------------------------------------------------
            # Key.
            # -------------------------------------------------

            elif cell == KEY:

                self.player.has_key = True

                self.grid[pr][pc] = FLOOR

                self.status = (
                    "Got the key! Find the CHEST!"
                )

            # -------------------------------------------------
            # Chest.
            # -------------------------------------------------

            elif (
                cell == CHEST
                and self.player.has_key
            ):

                self.won = True

                self.status = (
                    "Treasure found!"
                )

    def draw(self):

        self.screen.fill(
            (30, 25, 40)
        )

        # -----------------------------------------------------
        # Draw dungeon.
        # -----------------------------------------------------

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
                        rect.inflate(
                            -12,
                            -12
                        ),
                        border_radius=4
                    )

                # -------------------------------------------------
                # TASK 1 — Trap
                # -------------------------------------------------

                elif cell == TRAP:

                    trap_rect = rect.inflate(
                        -10,
                        -10
                    )

                    pygame.draw.rect(
                        self.screen,
                        (140, 40, 40),
                        trap_rect,
                        border_radius=6
                    )

                    pygame.draw.line(
                        self.screen,
                        (240, 220, 220),
                        (
                            c * TILE + 10,
                            r * TILE + 10
                        ),
                        (
                            c * TILE + TILE - 10,
                            r * TILE + TILE - 10
                        ),
                        3
                    )

                    pygame.draw.line(
                        self.screen,
                        (240, 220, 220),
                        (
                            c * TILE + TILE - 10,
                            r * TILE + 10
                        ),
                        (
                            c * TILE + 10,
                            r * TILE + TILE - 10
                        ),
                        3
                    )

        # -----------------------------------------------------
        # Player
        # -----------------------------------------------------

        self.player.draw(
            self.screen
        )

        # -----------------------------------------------------
        # TASK 2 — Guard
        # -----------------------------------------------------

        self.guard.draw(
            self.screen
        )

        # -----------------------------------------------------
        # HUD
        # -----------------------------------------------------

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

        st = self.font.render(
            self.status
            + "  |  R=Restart",
            True,
            (200, 200, 200)
        )

        self.screen.blit(
            st,
            (
                8,
                ROWS * TILE + 13
            )
        )

        # -----------------------------------------------------
        # Win screen
        # -----------------------------------------------------

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
                    ROWS * TILE // 2 - 30
                )
            )

            self.screen.blit(
                sub,
                (
                    WIDTH // 2
                    - sub.get_width() // 2,
                    ROWS * TILE // 2 + 20
                )
            )

        pygame.display.flip()

    def run(self):

        running = True

        while running:

            running = self.handle_events()

            self.update()

            self.draw()

            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":

    engine = GameEngine()
    engine.run()