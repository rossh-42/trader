import random
from trader import encounter
from trader.players.randomPlayer import RandomPlayer
from trader import search


class BriberRefuser(RandomPlayer):
    """A player that always tries to bribe but refuses other bribes."""

    def __init__(self, verbose=True):
        RandomPlayer.__init__(self, verbose)

    def initGame(self, playerNumber):
        self._beingName = 'BriberRefuser{0}'.format(playerNumber)
        self._stdInPlayer._beingName = self._beingName
        return self._beingName

    def voteInitState(self, game, being):
        return encounter.SEARCH

    def chooseSearchAction(self, game, meBeing, themBeing):
        return random.choice((search.SearchAction.PASS, search.SearchAction.SOLICIT_BRIBE))

    def evaluateBribeSolicitation(self, game, meBeing, themBeing):
        return (search.SearchAction.PASS, 0)
