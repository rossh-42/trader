import random
from trader.game import Game, Being
from trader.encounter import EncounterStateCode
from trader.search import SearchAction
from trader.players.randomPlayer import RandomPlayer
from typing import Tuple


class Boarder(RandomPlayer):
    """A player that always tries to board."""

    def __init__(self, verbose: bool = True):
        RandomPlayer.__init__(self, verbose)

    def initGame(self, playerNumber: int) -> str:
        self._beingName = 'Boarder{0}'.format(playerNumber)
        self._stdInPlayer._beingName = self._beingName
        return self._beingName

    def voteInitState(self, game: Game, being: Being) -> EncounterStateCode:
        return EncounterStateCode.SEARCH

    def chooseSearchAction(self, game: Game, meBeing: Being, themBeing: Being) -> SearchAction:
        return random.choice((SearchAction.PASS, SearchAction.BOARD))

    def evaluateBoardRequest(self, game: Game, meBeing: Being, themBeing: Being) -> SearchAction:
        return SearchAction.SUBMIT

    def evaluateBribeSolicitation(self, game: Game, meBeing: Being, themBeing: Being) -> Tuple[SearchAction, int]:
        return (SearchAction.PASS, 0)
