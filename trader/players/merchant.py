import random
from trader.combat import Combat, CombatEvent, CombatAction, DeathReason
from trader.encounter import EncounterStateCode
from trader.game import Game, Being, Inventory, Player
from trader.search import SearchAction
from trader.trade import TradeAction
from typing import Dict, List


class MerchantPlayer(Player):
    """A player that stays in one place and sells stuff."""

    def __init__(self, verbose: bool = True):
        self._verbose = verbose
        self._prices: Dict[str, int] = {}

    def initGame(self, playerNumber: int):
        self._beingName = 'MerchantPlayer{0}'.format(playerNumber)
        return self._beingName

    def death(self, game: Game, deathReason: DeathReason):
        pass

    def chooseDestination(self, game: Game):
        return None

    def safeTravelUpdate(self, game: Game, distanceLeft: int):
        assert(False)

    def voteInitState(self, game: Game, being: Being):
        return EncounterStateCode.TRADE

    def chooseCombatAction(self, game: Game, being: Being, cmbt: Combat) -> CombatAction:
        return CombatAction.FLEE

    def combatEvents(self, game: Game, events: List[CombatEvent]):
        pass

    def arrived(self, game: Game):
        assert(False)

    def nodeEvents(self, game: Game, events):
        pass

    def advertiseTrade(self, game: Game, meBeing: Being):
        for goodName in meBeing.inventory.goods:
            self._prices[goodName] = random.randint(1, 100)
        return self._prices

    def readTradeAdvertisement(self, game: Game, prices):
        pass

    def chooseTradeAction(self, game: Game, meBeing: Being, themBeing: Being):
        return (TradeAction.PASS, None, None, None)

    def evaluateTradeRequest(self, game: Game, meBeing: Being, themBeing: Being, tradeAction: TradeAction,
                             quantity: int, goodName: str, price: int):
        if tradeAction == TradeAction.SELL:
            # I don't have enough money to buy this
            if quantity * price > meBeing.inventory.money:
                return False
        elif tradeAction == TradeAction.BUY:
            # I don't have enough of this good to make a sale
            if goodName not in meBeing.inventory.goods.keys():
                return False
            if quantity > meBeing.inventory.goods[goodName]:
                return False
        return True

    def chooseSearchAction(self, game: Game, meBeing: Being, themBeing: Being):
        return SearchAction.PASS

    def evaluateBoardRequest(self, game: Game, meBeing: Being, themBeing: Being):
        return SearchAction.SUBMIT

    def evaluateBribeSolicitation(self, game: Game, meBeing: Being, themBeing: Being):
        return (SearchAction.PASS, 0)

    def seize(self, game: Game, themInventory: Inventory):
        assert(False)
        return None

    def searchEvents(self, game: Game, events):
        pass


player = MerchantPlayer()
