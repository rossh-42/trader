import random
from trader.encounter import EncounterStateCode
from trader.game import Game, Being
from trader.players.randomPlayer import RandomPlayer
from trader.search import SearchAction
from typing import Tuple


class BriberRefuser(RandomPlayer):
    """A player that always tries to bribe but refuses other bribes."""

    def __init__(self, verbose: bool = True):
        RandomPlayer.__init__(self, verbose)

    def initGame(self, playerNumber: int) -> str:
        self._beingName = 'BriberRefuser{0}'.format(playerNumber)
        self._stdInPlayer._beingName = self._beingName
        return self._beingName

    def voteInitState(self, game: Game, being: Being) -> EncounterStateCode:
        return EncounterStateCode.SEARCH

    def chooseSearchAction(self, game: Game, meBeing: Being, themBeing: Being) -> SearchAction:
        return random.choice((SearchAction.PASS, SearchAction.SOLICIT_BRIBE))

    def evaluateBribeSolicitation(self, game: Game, meBeing: Being, themBeing: Being) -> Tuple[SearchAction, int]:
        return (SearchAction.PASS, 0)
