import random
from trader import encounter
from trader import search
from trader.players.randomPlayer import RandomPlayer


class Boarder(RandomPlayer):
    """A player that always tries to board."""

    def __init__(self, verbose=True):
        RandomPlayer.__init__(self, verbose)

    def initGame(self, playerNumber):
        self._beingName = 'Boarder{0}'.format(playerNumber)
        self._stdInPlayer._beingName = self._beingName
        return self._beingName

    def voteInitState(self, game, being):
        return encounter.SEARCH

    def chooseSearchAction(self, game, meBeing, themBeing):
        return random.choice((search.SearchAction.PASS, search.SearchAction.BOARD))

    def evaluateBoardRequest(self, game, meBeing, themBeing):
        return search.SearchAction.SUBMIT

    def evaluateBribeSolicitation(self, game, meBeing, themBeing):
        return (search.SearchAction.PASS, 0)
