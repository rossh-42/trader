import random
from trader import encounter
from trader.game import Game, Being
from trader.players.randomPlayer import RandomPlayer
from trader import search


class BriberRefuser(RandomPlayer):
    """A player that always tries to bribe but refuses other bribes."""

    def __init__(self, verbose: bool = True):
        RandomPlayer.__init__(self, verbose)

    def initGame(self, playerNumber: int):
        self._beingName = 'BriberRefuser{0}'.format(playerNumber)
        self._stdInPlayer._beingName = self._beingName
        return self._beingName

    def voteInitState(self, game: Game, being: Being):
        return encounter.SEARCH

    def chooseSearchAction(self, game: Game, meBeing: Being, themBeing: Being):
        return random.choice((search.SearchAction.PASS, search.SearchAction.SOLICIT_BRIBE))

    def evaluateBribeSolicitation(self, game: Game, meBeing: Being, themBeing: Being):
        return (search.SearchAction.PASS, 0)
