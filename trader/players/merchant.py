from trader import combat
from trader import encounter
from trader import game
from trader import random
from trader import search
from trader import trade


class MerchantPlayer(game.Player):
    """A player that stays in one place and sells stuff."""

    def __init__(self, verbose=True):
        self._verbose = verbose
        self._prices = {}

    def initGame(self, playerNumber):
        self._beingName = 'MerchantPlayer{0}'.format(playerNumber)
        return self._beingName

    def death(self, game, deathReason):
        pass

    def chooseDestination(self, game):
        return None

    def safeTravelUpdate(self, game, distanceLeft):
        assert(False)

    def voteInitState(self, game, being):
        return encounter.TRADE

    def chooseCombatAction(self, game, being, cmbt):
        return combat.FLEE

    def combatEvents(self, game, events):
        pass

    def arrived(self, game):
        assert(False)

    def nodeEvents(self, game, events):
        pass

    def advertiseTrade(self, game, meBeing):
        for goodName in meBeing.inventory.goods:
            self._prices[goodName] = random.randint(1, 100)
        return self._prices

    def readTradeAdvertisement(self, game, prices):
        pass

    def chooseTradeAction(self, game, meBeing, themBeing):
        return (trade.PASS, None, None, None)

    def evaluateTradeRequest(self, game, meBeing, themBeing, tradeAction, quantity, goodName, price):
        if tradeAction == trade.SELL:
            # I don't have enough money to buy this
            if quantity * price > meBeing.inventory.money:
                return False
        elif tradeAction == trade.BUY:
            # I don't have enough of this good to make a sale
            if goodName not in meBeing.inventory.goods.keys():
                return False
            if quantity > meBeing.inventory.goods[goodName]:
                return False
        return True

    def chooseSearchAction(self, game, meBeing, themBeing):
        return search.PASS

    def evaluateBoardRequest(self, game, meBeing, themBeing):
        return search.SUBMIT

    def evaluateBribeSolicitation(self, game, meBeing, themBeing):
        return (search.PASS, 0)

    def seize(self, game, themInventory):
        assert(False)
        return None

    def searchEvents(self, game, events):
        pass


player = MerchantPlayer()
