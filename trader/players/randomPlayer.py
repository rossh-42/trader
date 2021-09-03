from collections import Counter
import random
from trader import combat
from trader import encounter
from trader.game import Inventory, Player
from trader.players.stdInPlayer import StdInPlayer
from trader import search
from trader.trade import TradeAction


class RandomPlayer(Player):
    """A player that makes all game decisions more or less randomly."""

    def __init__(self, verbose=True):
        self._stdInPlayer = StdInPlayer()
        self._verbose = verbose
        self._prices = {}

    def initGame(self, playerNumber):
        self._beingName = 'RandomPlayer{0}'.format(playerNumber)
        self._stdInPlayer._beingName = self._beingName
        return self._beingName

    def death(self, game, deathReason):
        if deathReason == combat.DeathReason.COMBAT:
            if self._verbose:
                print('GAME OVER Day {0} (combat)'.format(game.day))
        elif deathReason == combat.DeathReason.OUT_OF_FUEL:
            if self._verbose:
                print('GAME OVER Day {0} (ran out of fuel)'.format(game.day))
        else:
            assert(False)

    def chooseDestination(self, game):
        being = game.getBeingByName(self._beingName)
        attempts = len(game.graph.nodes()) * 10
        while attempts:
            newDestination = random.choice(game.possibleDestinations(being))
            travelDistance = game.distance(being.currentLocation, newDestination)
            if being.inventory.goods['fuel'] >= travelDistance:
                break
            attempts -= 1
        if attempts == 0:
            assert(False)  # We should have found a destination
        if self._verbose:
            print('{0} {1} -> {2}'.format(self._beingName, being.currentLocation, newDestination))
        return newDestination

    def safeTravelUpdate(self, game, distanceLeft):
        if self._verbose:
            self._stdInPlayer.safeTravelUpdate(game, distanceLeft)

    def voteInitState(self, game, being):
        return random.choice((encounter.EncounterStateCode.COMBAT,
                              encounter.EncounterStateCode.TRADE))  # Need to add encounter.SEARCH here?

    def chooseCombatAction(self, game, being, cmbt):
        return random.choice((combat.CombatAction.FIGHT, combat.CombatAction.FLEE))

    def combatEvents(self, game, events):
        if self._verbose:
            self._stdInPlayer.combatEvents(game, events)

    def arrived(self, game):
        if self._verbose:
            self._stdInPlayer.arrived(game)

    def nodeEvents(self, game, events):
        pass

    def advertiseTrade(self, game, meBeing):
        self._prices = {}
        for goodName in meBeing.inventory.goods:
            self._prices[goodName] = random.randint(1, 100)
        if self._verbose:
            print(self._prices)
        return self._prices

    def readTradeAdvertisement(self, game, prices):
        pass

    def chooseTradeAction(self, game, meBeing, themBeing):
        tradeAction = random.choice((TradeAction.BUY, TradeAction.SELL, TradeAction.BUY,
                                     TradeAction.SELL, TradeAction.DONE))
        if tradeAction == TradeAction.BUY:
            numItems = len(themBeing.inventory.goods)
            if numItems == 0:
                return (TradeAction.DONE, None, None, None)
            goodName = random.choice(list(themBeing.inventory.goods.keys()))
            playerBuyPrice = self._prices[goodName]
            if playerBuyPrice > meBeing.inventory.money:
                return (TradeAction.DONE, None, None, None)
            attempts = 1000
            while attempts:
                quantity = random.randint(1, 100)
                if quantity * playerBuyPrice <= meBeing.inventory.money:
                    break
                attempts -= 1
            if attempts == 0:
                return (TradeAction.DONE, None, None, None)
            return (tradeAction, quantity, goodName, playerBuyPrice)
        elif tradeAction == TradeAction.SELL:
            numItems = len(meBeing.inventory.goods)
            if numItems == 0:
                return (TradeAction.DONE, None, None, None)
            goodName = random.choice(list(meBeing.inventory.goods.keys()))
            playerSellPrice = self._prices[goodName]
            attempts = 1000
            while attempts:
                quantity = random.randint(1, 100)
                if meBeing.inventory.goods[goodName] >= quantity:
                    break
                attempts -= 1
            if attempts == 0:
                return (TradeAction.DONE, None, None, None)
            return (tradeAction, quantity, goodName, playerSellPrice)
        else:
            if self._verbose:
                print('LEAVING TRADE SESSION')
            assert(tradeAction == TradeAction.DONE)
        return (tradeAction, None, None, None)

    def evaluateTradeRequest(self, game, meBeing, themBeing, tradeAction, quantity, goodName, price):
        if tradeAction == TradeAction.SELL:
            # I don't have enough money to buy this
            if quantity * price > meBeing.inventory.money:
                if self._verbose:
                    print('REJECTED: Not enough money to buy')
                return False
        elif tradeAction == TradeAction.BUY:
            # I don't have enough of this good to make a sale
            if goodName not in meBeing.inventory.goods.keys():
                if self._verbose:
                    print('REJECTED: Not enough inventory')
                return False
            if quantity > meBeing.inventory.goods[goodName]:
                if self._verbose:
                    print('REJECTED: Not enough inventory')
                return False

        if self._verbose:
            print('ACCEPTED')
        return True

    def chooseSearchAction(self, game, meBeing, themBeing):
        return random.choice((search.BOARD, search.SOLICIT_BRIBE, search.PASS, search.FIGHT))

    def evaluateBoardRequest(self, game, meBeing, themBeing):
        return random.choice((search.PASS, search.FIGHT, search.SUBMIT))

    def evaluateBribeSolicitation(self, game, meBeing, themBeing):
        answer = random.choice((search.PASS, search.FIGHT, search.SUBMIT))
        bribeAmount = 0
        if answer == search.SUBMIT:
            bribeAmount = random.randint(1, 100)
        return (answer, bribeAmount)

    def seize(self, game, themInventory):
        goodToTake = random.choice(list(themInventory.goods.keys()))
        amountToTake = random.randint(1, 100)
        goods_dict = {goodToTake: amountToTake}
        inventoryToTake = Inventory(goods=Counter(goods_dict))
        return inventoryToTake

    def searchEvents(self, game, events):
        pass


player = RandomPlayer()
