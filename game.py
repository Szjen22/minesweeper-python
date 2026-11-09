"""UI-independent Minesweeper rules. Coordinates are (row, column)."""
from dataclasses import dataclass
from enum import Enum
import random


class Status(Enum):
    READY = 'ready'
    PLAYING = 'playing'
    WON = 'won'
    LOST = 'lost'


@dataclass
class Cell:
    mine: bool = False
    revealed: bool = False
    flagged: bool = False
    adjacent: int = 0


class Board:
    def __init__(self, rows: int = 9, cols: int = 9, mines: int = 10,
                 rng: random.Random | None = None):
        if rows < 2 or cols < 2 or not 1 <= mines < rows * cols:
            raise ValueError('Invalid board dimensions or mine count')
        self.rows, self.cols, self.mines = rows, cols, mines
        self.cells = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.status = Status.READY
        self.exploded: tuple[int, int] | None = None
        self.rng = rng or random.Random()

    def neighbors(self, row, col):
        for r in range(max(0, row - 1), min(self.rows, row + 2)):
            for c in range(max(0, col - 1), min(self.cols, col + 2)):
                if (r, c) != (row, col):
                    yield r, c

    def _place(self, row, col):
        excluded = {(row, col), *self.neighbors(row, col)}
        if self.rows * self.cols - len(excluded) < self.mines:
            excluded = {(row, col)}
        choices = [(r, c) for r in range(self.rows) for c in range(self.cols)
                   if (r, c) not in excluded]
        for r, c in self.rng.sample(choices, self.mines):
            self.cells[r][c].mine = True
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].adjacent = sum(self.cells[y][x].mine
                                               for y, x in self.neighbors(r, c))
        self.status = Status.PLAYING

    @property
    def flags(self):
        return sum(cell.flagged for row in self.cells for cell in row)

    def toggle_flag(self, row, col):
        if not self._valid(row, col) or self.status in (Status.WON, Status.LOST):
            return
        cell = self.cells[row][col]
        if not cell.revealed and (cell.flagged or self.flags < self.mines):
            cell.flagged = not cell.flagged

    def _valid(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def reveal(self, row, col):
        if not self._valid(row, col) or self.status in (Status.WON, Status.LOST):
            return
        cell = self.cells[row][col]
        if cell.flagged or cell.revealed:
            return
        if self.status == Status.READY:
            self._place(row, col)
        pending = [(row, col)]
        while pending:
            r, c = pending.pop()
            cell = self.cells[r][c]
            if cell.revealed or cell.flagged:
                continue
            cell.revealed = True
            if cell.mine:
                self.exploded = (r, c)
                self.status = Status.LOST
                return
            if cell.adjacent == 0:
                pending.extend(self.neighbors(r, c))
        if all(cell.revealed or cell.mine for line in self.cells for cell in line):
            self.status = Status.WON

    def chord(self, row, col):
        """Reveal neighbors when the adjacent flag count matches the number."""
        if not self._valid(row, col):
            return
        cell = self.cells[row][col]
        neighbors = list(self.neighbors(row, col))
        if cell.revealed and cell.adjacent and sum(
                self.cells[r][c].flagged for r, c in neighbors) == cell.adjacent:
            for r, c in neighbors:
                self.reveal(r, c)
