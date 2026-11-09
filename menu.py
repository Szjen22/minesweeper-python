"""Pygame presentation and application lifecycle."""
import json
import os
from pathlib import Path
import time
import pygame
from game import Board, Status

LEVELS = [('Kezdő', 9, 9, 10), ('Haladó', 16, 16, 40), ('Szakértő', 16, 30, 99)]
BG = '#101923'
PANEL = '#1b2938'
TEXT = '#edf5fa'
MUTED = '#9aafc1'
ACCENT = '#62e3bc'
NUMBERS = ['#b3c3d1', '#61b9ff', '#62e3bc', '#ffad7d', '#c7a0ff', '#ff7f94', '#63dbe4', '#ffffff', '#b9c9db']


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Aknakereső · Jenni Szmolyán')
        self.clock = pygame.time.Clock()
        self.fonts = {size: pygame.font.SysFont('dejavusans,arial', size) for size in (14, 16, 20, 24, 36)}
        self.record_path = Path(os.environ.get('MINESWEEPER_DATA_DIR', Path.home() / '.minesweeper-python')) / 'records.json'
        self.notice = ''
        self.records = self.load_records()
        self.level = 0
        self.reset()

    def load_records(self):
        try:
            data = json.loads(self.record_path.read_text(encoding='utf-8'))
            return {k: v for k, v in data.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0} if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def reset(self):
        _, rows, cols, mines = LEVELS[self.level]
        self.board = Board(rows, cols, mines)
        self.tile = 34 if cols > 16 else 36
        self.width = max(680, cols * self.tile + 64)
        self.height = rows * self.tile + 290
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.origin = ((self.width - cols * self.tile) // 2, 216)
        self.started = None
        self.elapsed = 0.0
        self.recorded = False
        self.flag_mode = False

    def text(self, value, xy, size=16, color=TEXT):
        self.screen.blit(self.fonts[size].render(str(value), True, color), xy)

    def button(self, rect, label, active=False):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, ACCENT if active else ('#34495c' if hover else PANEL), rect, border_radius=9)
        rendered = self.fonts[14].render(label, True, BG if active else TEXT)
        self.screen.blit(rendered, rendered.get_rect(center=rect.center))

    def controls(self):
        return [(pygame.Rect(32 + i * 115, 91, 106, 36), name) for i, (name, *_) in enumerate(LEVELS)]

    def draw(self):
        self.screen.fill(BG)
        self.text('AKNAKERESŐ', (32, 23), 36)
        self.text('Gondolkodj előre. Tisztítsd meg a pályát.', (34, 66), 14, MUTED)
        for i, (rect, name) in enumerate(self.controls()):
            self.button(rect, name, i == self.level)
        self.new_rect = pygame.Rect(self.width - 159, 91, 127, 36)
        self.button(self.new_rect, 'Új játék · R', True)
        self.flag_rect = pygame.Rect(self.width - 159, 146, 127, 48)
        self.button(self.flag_rect, 'Zászló mód · F', self.flag_mode)
        best = self.records.get(str(self.level))
        for x, title, value in [(32, 'HÁTRALÉVŐ AKNA', f'{self.board.mines - self.board.flags:02}'),
                                (201, 'ELTELT IDŐ', f'{int(self.elapsed)//60:02}:{int(self.elapsed)%60:02}'),
                                (365, 'LEGJOBB IDŐ', f'{best:.1f} s' if best is not None else '—')]:
            self.text(title, (x, 144), 14, MUTED)
            self.text(value, (x, 164), 24, ACCENT)
        mx, my = pygame.mouse.get_pos()
        for r, row in enumerate(self.board.cells):
            for c, cell in enumerate(row):
                rect = pygame.Rect(self.origin[0] + c * self.tile, self.origin[1] + r * self.tile, self.tile - 3, self.tile - 3)
                show_mine = cell.mine and self.board.status in (Status.WON, Status.LOST)
                color = '#263949' if cell.revealed else '#3b5369' if rect.collidepoint(mx, my) else '#2d4357'
                if self.board.exploded == (r, c):
                    color = '#a54156'
                pygame.draw.rect(self.screen, color, rect, border_radius=5)
                if show_mine:
                    pygame.draw.circle(self.screen, ACCENT if self.board.status == Status.WON else '#ff9aaa', rect.center, 7)
                elif cell.flagged:
                    x, y = rect.center
                    pygame.draw.line(self.screen, TEXT, (x-5, y-9), (x-5, y+9), 2)
                    pygame.draw.polygon(self.screen, ACCENT, [(x-4, y-9), (x+9, y-4), (x-4, y+1)])
                    if self.board.status == Status.LOST:
                        pygame.draw.line(self.screen, '#ff9aaa', rect.topleft, rect.bottomright, 2)
                elif cell.revealed and cell.adjacent:
                    txt = self.fonts[20].render(str(cell.adjacent), True, NUMBERS[cell.adjacent])
                    self.screen.blit(txt, txt.get_rect(center=rect.center))
        messages = {Status.READY: 'Kezdéshez nyiss meg egy mezőt. Az első lépés biztonságos.',
                    Status.PLAYING: 'Keresd meg az összes biztonságos mezőt!',
                    Status.WON: 'Szép munka! Megtisztítottad a pályát. Új játék: R',
                    Status.LOST: 'Aknára léptél. Próbáld újra! Új játék: R'}
        y = self.height - 63
        self.text(messages[self.board.status], (32, y), 16, ACCENT if self.board.status == Status.WON else TEXT)
        self.text(self.notice or 'Bal klikk: nyitás  ·  Jobb klikk / F: zászló  ·  Középső klikk: szomszédok', (32, y + 29), 14, MUTED)
        pygame.display.flip()

    def update_time(self):
        if self.started is not None and not self.recorded:
            self.elapsed = time.monotonic() - self.started
        if self.board.status in (Status.WON, Status.LOST) and not self.recorded:
            self.recorded = True
            if self.board.status == Status.WON:
                key = str(self.level)
                if self.elapsed < self.records.get(key, float('inf')):
                    self.records[key] = round(self.elapsed, 1)
                    try:
                        self.record_path.parent.mkdir(parents=True, exist_ok=True)
                        temporary = self.record_path.with_suffix('.tmp')
                        temporary.write_text(json.dumps(self.records), encoding='utf-8')
                        temporary.replace(self.record_path)
                    except OSError:
                        self.notice = 'A rekordot nem sikerült menteni.'

    def run(self):
        running = True
        self.draw()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_f:
                        self.flag_mode = not self.flag_mode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        selected = next((i for i, (rect, _) in enumerate(self.controls()) if rect.collidepoint(event.pos)), None)
                        if selected is not None:
                            self.level = selected
                            self.reset()
                            continue
                        if self.new_rect.collidepoint(event.pos):
                            self.reset()
                            continue
                        if self.flag_rect.collidepoint(event.pos):
                            self.flag_mode = not self.flag_mode
                            continue
                    c = (event.pos[0] - self.origin[0]) // self.tile
                    r = (event.pos[1] - self.origin[1]) // self.tile
                    if event.button == 3 or (event.button == 1 and self.flag_mode):
                        self.board.toggle_flag(r, c)
                    elif event.button in (1, 2):
                        if event.button == 2:
                            self.board.chord(r, c)
                        else:
                            self.board.reveal(r, c)
                        if self.started is None and self.board.status != Status.READY:
                            self.started = time.monotonic()
                    self.update_time()
            self.update_time()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
