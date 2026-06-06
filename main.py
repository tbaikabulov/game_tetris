import math
import random
import sys

import pygame

COLS = 10
ROWS = 20
CELL = 30
SIDEBAR = 180
WIDTH = COLS * CELL + SIDEBAR
HEIGHT = ROWS * CELL

BLACK = (15, 15, 25)
GRAY = (40, 40, 55)
WHITE = (240, 240, 240)
GRID = (35, 35, 50)

SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
    "X": [[1, 0, 1], [0, 1, 0], [1, 0, 1]],
}

COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
    "X": (255, 0, 200),
}

TRICKY_KIND = "X"
TRICKY_SPAWN_CHANCE = 0.08
TRICKY_LOCK_BONUS = 150


def rotate_matrix(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def random_piece_kind():
    if random.random() < TRICKY_SPAWN_CHANCE:
        return TRICKY_KIND
    standard = [kind for kind in SHAPES if kind != TRICKY_KIND]
    return random.choice(standard)


def piece_display_color(piece, tick=0):
    if piece.kind != TRICKY_KIND:
        return piece.color
    pulse = (math.sin(tick * 0.12) + 1) / 2
    return (
        255,
        int(80 + pulse * 120),
        int(180 + pulse * 75),
    )


class Piece:
    def __init__(self, kind=None):
        self.kind = kind or random_piece_kind()
        self.matrix = [row[:] for row in SHAPES[self.kind]]
        self.x = COLS // 2 - len(self.matrix[0]) // 2
        self.y = 0
        self.color = COLORS[self.kind]
        self.is_tricky = self.kind == TRICKY_KIND

    def rotated(self):
        clone = Piece(self.kind)
        clone.matrix = rotate_matrix(self.matrix)
        clone.x = self.x
        clone.y = self.y
        return clone


class Tetris:
    def __init__(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.current = Piece()
        self.next_piece = Piece()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.drop_timer = 0
        self.drop_speed = 800

    def valid(self, piece, dx=0, dy=0):
        for y, row in enumerate(piece.matrix):
            for x, cell in enumerate(row):
                if not cell:
                    continue
                nx = piece.x + x + dx
                ny = piece.y + y + dy
                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return False
                if ny >= 0 and self.board[ny][nx] is not None:
                    return False
        return True

    def lock_piece(self):
        for y, row in enumerate(self.current.matrix):
            for x, cell in enumerate(row):
                if not cell:
                    continue
                by = self.current.y + y
                bx = self.current.x + x
                if by < 0:
                    self.game_over = True
                    return
                self.board[by][bx] = self.current.color

        if self.current.is_tricky:
            self.score += TRICKY_LOCK_BONUS

        cleared = self.clear_lines()
        if cleared:
            points = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += points.get(cleared, 800) * self.level
            self.lines += cleared
            self.level = 1 + self.lines // 10
            self.drop_speed = max(100, 800 - (self.level - 1) * 70)

        self.current = self.next_piece
        self.next_piece = Piece()
        if not self.valid(self.current):
            self.game_over = True

    def clear_lines(self):
        full_rows = [i for i, row in enumerate(self.board) if all(cell is not None for cell in row)]
        for row_index in full_rows:
            del self.board[row_index]
            self.board.insert(0, [None for _ in range(COLS)])
        return len(full_rows)

    def move(self, dx, dy):
        if self.valid(self.current, dx, dy):
            self.current.x += dx
            self.current.y += dy
            return True
        return False

    def rotate(self):
        rotated = self.current.rotated()
        for kick in (0, -1, 1, -2, 2):
            rotated.x = self.current.x + kick
            rotated.y = self.current.y
            if self.valid(rotated):
                self.current = rotated
                return

    def hard_drop(self):
        while self.move(0, 1):
            self.score += 2
        self.lock_piece()

    def soft_drop(self):
        if self.move(0, 1):
            self.score += 1
        else:
            self.lock_piece()

    def update(self, dt):
        if self.game_over or self.paused:
            return
        self.drop_timer += dt
        if self.drop_timer >= self.drop_speed:
            self.drop_timer = 0
            if not self.move(0, 1):
                self.lock_piece()

    def restart(self):
        self.__init__()


def draw_cell(surface, x, y, color, offset_x=0):
    rect = pygame.Rect(offset_x + x * CELL, y * CELL, CELL, CELL)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, GRID, rect, 1)


def draw_board(surface, game, tick=0):
    board_surface = pygame.Surface((COLS * CELL, ROWS * CELL))
    board_surface.fill(BLACK)

    for y in range(ROWS):
        for x in range(COLS):
            color = game.board[y][x]
            if color:
                draw_cell(board_surface, x, y, color)

    if not game.game_over:
        current_color = piece_display_color(game.current, tick)
        for y, row in enumerate(game.current.matrix):
            for x, cell in enumerate(row):
                if cell:
                    draw_cell(
                        board_surface,
                        game.current.x + x,
                        game.current.y + y,
                        current_color,
                    )

    surface.blit(board_surface, (0, 0))
    pygame.draw.rect(surface, GRAY, (0, 0, COLS * CELL, ROWS * CELL), 2)


def draw_next(surface, piece, font, small_font, tick=0):
    x0 = COLS * CELL + 20
    y0 = 40
    title = font.render("Следующая", True, WHITE)
    surface.blit(title, (x0, y0))

    if piece.is_tricky:
        label = small_font.render("Хитрая X!", True, COLORS[TRICKY_KIND])
        surface.blit(label, (x0, y0 + 28))

    preview_x = x0 + 20
    preview_y = y0 + 56 if piece.is_tricky else y0 + 40
    preview_color = piece_display_color(piece, tick)
    for y, row in enumerate(piece.matrix):
        for x, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(preview_x + x * 24, preview_y + y * 24, 24, 24)
                pygame.draw.rect(surface, preview_color, rect)
                pygame.draw.rect(surface, GRID, rect, 1)


def draw_sidebar(surface, game, font, small_font):
    x0 = COLS * CELL + 20
    lines = [
        ("Счёт", str(game.score)),
        ("Линии", str(game.lines)),
        ("Уровень", str(game.level)),
    ]
    y = 180
    for label, value in lines:
        surface.blit(small_font.render(label, True, GRAY), (x0, y))
        surface.blit(font.render(value, True, WHITE), (x0, y + 22))
        y += 70

    controls = [
        "← → — движение",
        "↑ — поворот",
        "↓ — ускорение",
        "Пробел — сброс",
        "P — пауза",
        "R — заново",
        "Esc — выход",
        "",
        "X — хитрая фигура",
        "редкая, +150 очков",
    ]
    y = 420
    for line in controls:
        surface.blit(small_font.render(line, True, GRAY), (x0, y))
        y += 22


def draw_overlay(surface, text, font):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    label = font.render(text, True, WHITE)
    rect = label.get_rect(center=(COLS * CELL // 2, HEIGHT // 2))
    surface.blit(label, rect)


def main():
    pygame.init()
    pygame.display.set_caption("Тетрис")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28)
    small_font = pygame.font.SysFont("arial", 18)
    big_font = pygame.font.SysFont("arial", 36)

    game = Tetris()
    tick = 0

    while True:
        dt = clock.tick(60)
        tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    game.restart()
                elif event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                elif not game.game_over and not game.paused:
                    if event.key == pygame.K_LEFT:
                        game.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        game.soft_drop()
                    elif event.key == pygame.K_UP:
                        game.rotate()
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()

        game.update(dt)

        screen.fill(BLACK)
        draw_board(screen, game, tick)
        draw_next(screen, game.next_piece, font, small_font, tick)
        draw_sidebar(screen, game, font, small_font)

        if game.paused:
            draw_overlay(screen, "Пауза", big_font)
        if game.game_over:
            draw_overlay(screen, "Игра окончена — R", big_font)

        pygame.display.flip()


if __name__ == "__main__":
    main()
