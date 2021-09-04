from collections import Counter
import random
from trader.combat import Combat, CombatEvent, CombatAction, DeathReason
from trader import encounter
from trader.game import Inventory, Player, Game, Being
from trader.players.stdInPlayer import StdInPlayer
from trader.search import SearchAction
from trader.trade import TradeAction
from typing import List, Tuple, Dict, Optional


class RandomPlayer(Player):
    """A player that makes all game decisions more or less randomly."""

    def __init__(self, verbose: bool = True):
        self._stdInPlayer = StdInPlayer()
        self._verbose = verbose
        self._prices: Dict[str, int] = {}

    def initGame(self, playerNumber: int):
        self._beingName = 'RandomPlayer{0}'.format(playerNumber)
        self._stdInPlayer._beingName = self._beingName
        return self._beingName

    def death(self, game: Game, deathReason: DeathReason):
        if deathReason == DeathReason.COMBAT:
            if self._verbose:
                print('GAME OVER Day {0} (combat)'.format(game.day))
        elif deathReason == DeathReason.OUT_OF_FUEL:
            if self._verbose:
                print('GAME OVER Day {0} (ran out of fuel)'.format(game.day))
        else:
            assert(False)

    def chooseDestination(self, game: Game):
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

    def safeTravelUpdate(self, game: Game, distanceLeft: int):
        if self._verbose:
            self._stdInPlayer.safeTravelUpdate(game, distanceLeft)

    def voteInitState(self, game: Game, being: Being):
        return random.choice((encounter.EncounterStateCode.COMBAT,
                              encounter.EncounterStateCode.TRADE))  # Need to add encounter.SEARCH here?

    def chooseCombatAction(self, game: Game, being: Being, cmbt: Combat):
        return random.choice((CombatAction.FIGHT, CombatAction.FLEE))

    def combatEvents(self, game: Game, events: List[CombatEvent]):
        if self._verbose:
            self._stdInPlayer.combatEvents(game, events)

    def arrived(self, game: Game):
        if self._verbose:
            self._stdInPlayer.arrived(game)

    def nodeEvents(self, game: Game, events: Tuple[str]):
        pass

    def advertiseTrade(self, game: Game, meBeing: Being):
        self._prices = {}
        for goodName in meBeing.inventory.goods:
            self._prices[goodName] = random.randint(1, 100)
        if self._verbose:
            print(self._prices)
        return self._prices

    def readTradeAdvertisement(self, game: Game, prices: Dict[str, int]):
        pass

    def chooseTradeAction(self, game: Game, meBeing: 'Being', themBeing: 'Being') -> Tuple[TradeAction, Optional[int], Optional[str], Optional[int]]:  # noqa: E501
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

    def evaluateTradeRequest(self, game: Game, meBeing: Being, themBeing: Being, tradeAction: TradeAction,
                             quantity: int, goodName: str, price: int):
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

    def chooseSearchAction(self, game: Game, meBeing: Being, themBeing: Being):
        return random.choice((SearchAction.BOARD, SearchAction.SOLICIT_BRIBE, SearchAction.PASS, SearchAction.FIGHT))

    def evaluateBoardRequest(self, game: Game, meBeing: Being, themBeing: Being):
        return random.choice((SearchAction.PASS, SearchAction.FIGHT, SearchAction.SUBMIT))

    def evaluateBribeSolicitation(self, game: Game, meBeing: Being, themBeing: Being):
        answer = random.choice((SearchAction.PASS, SearchAction.FIGHT, SearchAction.SUBMIT))
        bribeAmount = 0
        if answer == SearchAction.SUBMIT:
            bribeAmount = random.randint(1, 100)
        return (answer, bribeAmount)

    def seize(self, game: Game, themInventory: Inventory):
        goodToTake = random.choice(list(themInventory.goods.keys()))
        amountToTake = random.randint(1, 100)
        goods_dict = {goodToTake: amountToTake}
        inventoryToTake = Inventory(goods=Counter(goods_dict))
        return inventoryToTake

    def searchEvents(self, game: Game, events):
        pass


player = RandomPlayer()
