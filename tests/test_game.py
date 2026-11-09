import random
import unittest
from game import Board, Status

class BoardTests(unittest.TestCase):
    def test_safe_opening_and_exact_count(self):
        for seed in range(100):
            b = Board(rng=random.Random(seed))
            b.reveal(4, 4)
            self.assertEqual(sum(c.mine for row in b.cells for c in row), 10)
            self.assertTrue(all(not b.cells[r][c].mine for r,c in [(4,4), *b.neighbors(4,4)]))
            for r in range(b.rows):
                for c in range(b.cols):
                    self.assertEqual(b.cells[r][c].adjacent, sum(b.cells[y][x].mine for y,x in b.neighbors(r,c)))

    def test_flags_and_bounds(self):
        b = Board()
        b.toggle_flag(0, 0)
        b.reveal(0, 0)
        self.assertEqual(b.status, Status.READY)
        b.toggle_flag(0, 0)
        b.reveal(0, 0)
        b.toggle_flag(0, 0)
        self.assertFalse(b.cells[0][0].flagged)
        b.reveal(-1, 0)
        b.toggle_flag(100, 100)

    def test_win_and_terminal_state(self):
        b = Board(rng=random.Random(2))
        b.reveal(4, 4)
        for r, row in enumerate(b.cells):
            for c, cell in enumerate(row):
                if not cell.mine:
                    b.reveal(r, c)
        self.assertEqual(b.status, Status.WON)
        mine = next((r,c) for r,row in enumerate(b.cells) for c,cell in enumerate(row) if cell.mine)
        b.reveal(*mine)
        self.assertEqual(b.status, Status.WON)

    def test_loss(self):
        b = Board(rng=random.Random(3))
        b.reveal(4, 4)
        mine = next((r,c) for r,row in enumerate(b.cells) for c,cell in enumerate(row) if cell.mine)
        b.reveal(*mine)
        self.assertEqual(b.status, Status.LOST)
        self.assertEqual(b.exploded, mine)

    def test_dense_board_and_validation(self):
        b = Board(2, 2, 3)
        b.reveal(0, 0)
        self.assertEqual(b.status, Status.WON)
        for args in [(1,9,2), (9,9,81), (9,9,0)]:
            with self.assertRaises(ValueError):
                Board(*args)

    def test_large_empty_area(self):
        b = Board(60, 60, 1, random.Random(1))
        b.reveal(30, 30)
        self.assertGreater(sum(c.revealed for row in b.cells for c in row), 3500)

    def test_chord(self):
        b = Board(rng=random.Random(7))
        b.reveal(4, 4)
        for r,row in enumerate(b.cells):
            for c,cell in enumerate(row):
                if cell.mine:
                    b.toggle_flag(r,c)
        for r,row in enumerate(b.cells):
            for c,cell in enumerate(row):
                if cell.revealed:
                    b.chord(r,c)
        self.assertNotEqual(b.status, Status.LOST)

if __name__ == '__main__':
    unittest.main()
