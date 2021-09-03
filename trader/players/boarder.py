import random
from trader.game import Game, Being
from trader.encounter import EncounterStateCode
from trader import search
from trader.players.randomPlayer import RandomPlayer


class Boarder(RandomPlayer):
    """A player that always tries to board."""

    def __init__(self, verbose: bool = True):
        RandomPlayer.__init__(self, verbose)

    def initGame(self, playerNumber: int):
        self._beingName = 'Boarder{0}'.format(playerNumber)
        self._stdInPlayer._beingName = self._beingName
        return self._beingName

    def voteInitState(self, game: Game, being: Being):
        return EncounterStateCode.SEARCH

    def chooseSearchAction(self, game: Game, meBeing: Being, themBeing: Being):
        return random.choice((search.SearchAction.PASS, search.SearchAction.BOARD))

    def evaluateBoardRequest(self, game: Game, meBeing: Being, themBeing: Being):
        return search.SearchAction.SUBMIT

    def evaluateBribeSolicitation(self, game: Game, meBeing: Being, themBeing: Being):
        return (search.SearchAction.PASS, 0)
