from trader.game import Game
from trader.players.randomPlayer import RandomPlayer
import unittest


RANDOM_PLAYER_RUNS = 100
NUM_DAYS = 500


class TestRandomPlayer(unittest.TestCase):
    def test_random_player(self):
        for x in range(RANDOM_PLAYER_RUNS):
            p1 = RandomPlayer(verbose=False)
            p2 = RandomPlayer(verbose=False)
            p3 = RandomPlayer(verbose=False)
            g = Game([p1, p2, p3])
            keepGoing = True
            day = 0
            while keepGoing:
                keepGoing = g.doTurn()
                day += 1
                self.assertEqual(day, g.day)
                if day > NUM_DAYS:
                    keepGoing = False


if __name__ == '__main__':
    unittest.main()
