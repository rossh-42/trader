import string
import sys
from trader.combat import Combat, DeathReason, CombatAction, CombatEventCode
from trader.combat import CombatEvent, DamageCombatEvent, DeathCombatEvent, EscapeCombatEvent
from trader.combat import FailToEscapeCombatEvent, JoinCombatEvent, VictoryCombatEvent
from trader.encounter import EncounterStateCode
from trader.game import Game, Being, Player
from trader.trade import TradeAction
from typing import Tuple, Optional, List, Dict


class AbortException(Exception):
    pass


class StdInPlayer(Player):
    def __init__(self):
        self._playerState = ''
        self._buyPrices = {}
        self._sellPrices = {}

    def initGame(self, playerNumber: int) -> str:
        print('Player number = {0}'.format(playerNumber))
        print('Enter your player name:')
        self._beingName = input('>')
        return self._beingName

    def death(self, game: Game, deathReason: DeathReason):
        if deathReason == DeathReason.COMBAT:
            print('DIED IN COMBAT')
        elif deathReason == DeathReason.OUT_OF_FUEL:
            print('DIED - RAN OUT OF FUEL')
        else:
            assert(False)
        sys.exit(0)

    def _getIntInput(self, game: Game, inventory=None):
        """Wrapper function for _getInput that ensures integer input."""
        while True:
            strVal = self._getInput(game, '#>', inventory)
            try:
                retval = int(strVal)
                return retval
            except ValueError:
                print('You must input a valid integer')

    def _getInput(self, game: Game, prompt: str, inventory=None):
        """
        Get a command from stdin and process it if it is any of the standard commands.
        game - The Game object.
        prompt - The prompt to show before getting input.
        inventory - In a trade state this is the inventory currently selected for
                    buying or selling.
        """
        while True:
            command = input(prompt).lower()
            if not self._processStandardCommands(game, command, inventory):
                break
        return command

    def _printStandardCommands(self):
        """Print to stdout the list of standard commands."""
        print('map - Show where you are and the neighest neighbors')
        print('money - Show how much money you have')
        print('tank - Show how much fuel you have')
        print('ship - Show information about your vessel')
        print('inventory - Show information about all your goods')
        print('day - Show whay day it is')
        print('abort - Abort a pending transaction')
        print('quit - Quit the game')
        print('help - Show this command help')

    def _processStandardCommands(self, game: Game, command: str, inventory=None):
        """
        Process any of the standard commands.
        game - The Game object.
        command - The incoming command from stdin.
        inventory - In a trade state this is the inventory currently selected for
                    buying or selling.
        """
        being = game.getBeingByName(self._beingName)
        if command == 'map':
            if being.currentLocation:
                print('You are at {0}'.format(string.capwords(being.currentLocation)))
                for destination in game.possibleDestinations(being):
                    distance = game.distance(being.currentLocation, destination)
                    print('{0} ({1} days)'.format(string.capwords(destination), distance))
            else:
                assert(being.destination)
                assert(being.lastDestination)
                print('You are on the way from {0} to {1}'.format(string.capwords(being.lastDestination),
                                                                  string.capwords(being.destination)))
            return True
        elif command == 'money' or command == 'cash':
            print(being.inventory.money)
            return True
        elif command == 'tank' or command == 'gas':
            print(being.inventory.goods['fuel'])
            return True
        elif command == 'ship':
            print(being.inventory.vessel.name)
            print('capacity = {0}'.format(being.inventory.vessel.capacity))
            print('offense = {0}'.format(being.inventory.vessel.offense))
            print('defense = {0}'.format(being.inventory.vessel.defense))
            print('maneuverability = {0}'.format(being.inventory.vessel.maneuverability))
            print('stealth = {0}'.format(being.inventory.vessel.stealth))
            print('upgrade points = {0}'.format(being.inventory.vessel.upgradePoints))
            for upgrade in being.inventory.vessel.upgrades:
                print('upgrade: {0}'.format(upgrade.name))
                print('  offense+{0}'.format(upgrade.offenseMod))
                print('  defense+{0}'.format(upgrade.defenseMod))
                print('  maneuverabilityMod+{0}'.format(upgrade.maneuverabilityMod))
                print('  stealth+{0})'.format(upgrade.stealthMod))
            return True
        elif command == 'inventory':
            for good in being.inventory.goods:
                print('{0} ({1})'.format(good, being.inventory.goods[good]))
            return True
        elif command == 'help':
            if self._playerState == 'chooseDestination':
                for destination in game.possibleDestinations(being):
                    print(destination)
                self._printStandardCommands()
            elif self._playerState == 'chooseTradeAction':
                print('merchant - Show what the merchant is selling')
                print('inventory - Show your inventory')
                print('buy - Buy something from the merchant')
                print('sell - Sell something to the merchant')
                print('done - Finish transacting with the merchant')
                self._printStandardCommands()
            elif self._playerState == 'chooseGood':
                assert(inventory)
                for goodName in inventory:
                    print(goodName)
                self._printStandardCommands()
            elif self._playerState == 'chooseQuantity':
                print('<Number from 0-100>')
                self._printStandardCommands()
            elif self._playerState == 'chooseYesNo':
                print('yes (y)')
                print('no (n)')
            elif self._playerState == 'voteInitState':
                print('combat')
                print('trade')
                self._printStandardCommands()
            elif self._playerState == 'chooseCombatAction':
                print('fight')
                print('flee')
                self._printStandardCommands()
            elif self._playerState == 'advertiseTrade':
                print('<Number from 0-100>')
                self._printStandardCommands()
            else:
                print(self._playerState)
                assert(False)
            return True
        elif command == 'date' or command == 'day':
            print('Day {0}'.format(game.day))
            return True
        elif command == 'abort':
            raise AbortException
        elif command == 'quit' or command == 'exit':
            sys.exit(0)
        return False

    def chooseDestination(self, game: Game) -> Optional[str]:
        being = game.getBeingByName(self._beingName)
        self._playerState = 'chooseDestination'
        while True:
            try:
                print('Choose destination:')
                for destination in game.possibleDestinations(being):
                    print(destination)
                newDestination = self._getInput(game, '0>')
                if newDestination not in game.possibleDestinations(being):
                    print('Not a valid destination')
                    continue
                travelDistance = game.distance(being.currentLocation, newDestination)
                if being.inventory.goods['fuel'] < travelDistance:
                    print('Not enough fuel to fuel to reach {0}'.format(string.capwords(newDestination)))
                    continue
                break
            except AbortException:
                print('You can\'t abort this, you must choose a destination')
        print('{0} -> {1}'.format(string.capwords(being.currentLocation),
                                  string.capwords(newDestination)))
        self._playerState = ''
        return newDestination

    def safeTravelUpdate(self, game: Game, distanceLeft: int):
        print('Day {0}'.format(game.day))
        print('Safe travel: {0} days left'.format(distanceLeft))

    def voteInitState(self, game: Game, being: Being) -> EncounterStateCode:
        while True:
            try:
                self._playerState = 'voteInitState'
                print('Encountered {0}'.format(being.name))
                print('(combat, trade)')
                action = self._getInput(game, '->')
                if action == 'combat':
                    self._playerState = ''
                    return EncounterStateCode.COMBAT
                elif action == 'trade':
                    self._playerState = ''
                    return EncounterStateCode.TRADE
                else:
                    print('Invalid encounter state')
            except AbortException:
                print('You can\'t abort this, you must choose!')

    def chooseCombatAction(self, game: Game, being: Being, cmbt: Combat) -> CombatAction:
        while True:
            try:
                self._playerState = 'chooseCombatAction'
                print('Choose a combat command (fight, flee)')
                action = self._getInput(game, 'X>')
                if action == 'fight':
                    self._playerState = ''
                    return CombatAction.FIGHT
                elif action == 'flee':
                    self._playerState = ''
                    return CombatAction.FLEE
                else:
                    print('Invalid combat command')
            except AbortException:
                print('You can\'t abort this, you must fight!')

    def combatEvents(self, game: Game, events: List[CombatEvent]):
        for event in events:
            if event.eventCode == CombatEventCode.DAMAGE:
                damage_event: DamageCombatEvent = event  # type: ignore
                print('{0} does {1} points of damage to {2}'.format(damage_event.attacker, damage_event.damage, damage_event.defender))
            elif event.eventCode == CombatEventCode.DEATH:
                death_event: DeathCombatEvent = event  # type: ignore
                print('{0} dies'.format(death_event.being))
            elif event.eventCode == CombatEventCode.ESCAPE:
                escape_event: EscapeCombatEvent = event  # type: ignore
                print('{0} escapes'.format(escape_event.being))
            elif event.eventCode == CombatEventCode.FAIL_TO_ESCAPE:
                fail_event: FailToEscapeCombatEvent = event  # type: ignore
                print('{0} fails to escape'.format(fail_event.being))
            elif event.eventCode == CombatEventCode.JOIN:
                join_event: JoinCombatEvent = event  # type: ignore
                print('{0} joins combat'.format(join_event.being))
            elif event.eventCode == CombatEventCode.VICTORY:
                victory_event: VictoryCombatEvent = event  # type: ignore
                print('{0} wins!'.format(victory_event.being))
            else:
                assert(False)

    def arrived(self, game: Game):
        being = game.getBeingByName(self._beingName)
        print('Day {0}'.format(game.day))
        print('You have arrived safely')
        print('Welcome to {0}'.format(string.capwords(being.currentLocation)))

    def _printNodeGoodsList(self, goods: Dict[str, int]):
        """
        Print out a list of goods.
        goods - Dictionary goodName -> (sellPrice, buyPrice).
        """
        assert(goods)
        for goodName in goods:
            print('{0}'.format(goodName))

    def nodeEvents(self, game: Game, events: Tuple[str]):
        being = game.getBeingByName(self._beingName)
        print('{0} News:'.format(string.capwords(being.currentLocation)))
        for event in events:
            description = game.getNodeEventDescription(event, being)
            print('* {0}'.format(description))

    def advertiseTrade(self, game: Game, meBeing: Being) -> Dict[str, int]:
        self._sellPrices = {}
        self._playerState = 'advertiseTrade'
        for goodName in meBeing.inventory.goods:
            print('What price would you sell {0} for?:'.format(goodName))
            sellPrice = self._getIntInput(game)
            self._sellPrices[goodName] = sellPrice
        self._playerState = ''
        return self._sellPrices

    def readTradeAdvertisement(self, game: Game, prices: Dict[str, int]):
        for goodName in prices:
            print('{0}: {1}'.format(goodName, prices[goodName]))
        self._buyPrices = prices

    def chooseTradeAction(self, game: Game, meBeing: Being, themBeing: Being) -> Tuple[TradeAction, Optional[int], Optional[str], Optional[int]]:  # noqa: E501
        meBeing = game.getBeingByName(self._beingName)
        self._playerState = 'chooseTradeAction'
        self._printNodeGoodsList(themBeing.inventory.goods)
        retval: Tuple[TradeAction, Optional[int], Optional[str], Optional[int]] = (TradeAction.DONE, None, None, None)
        while True:
            try:
                print('Choose a trade command (buy, sell, done)')
                action = self._getInput(game, '$>', themBeing.inventory.goods)
                if action == 'done':
                    retval = (TradeAction.DONE, 0, '', 0)
                    break
                elif action == 'merchant':
                    self._printNodeGoodsList(themBeing.inventory.goods)
                elif action == 'buy':
                    while True:
                        # Get a good name from the player and validate it
                        self._playerState = 'chooseGood'
                        print('Choose a good to buy:')
                        self._printNodeGoodsList(themBeing.inventory.goods)
                        goodName = self._getInput(game, '$>', themBeing.inventory.goods)
                        if goodName not in themBeing.inventory.goods:
                            print('You must input a valid good name:')
                            self._printNodeGoodsList(themBeing.inventory.goods)
                            continue
                        break

                    print(themBeing.inventory.goods)
                    playerBuyPrice = self._buyPrices[goodName]
                    print('{0} costs {1} per unit'.format(goodName,
                                                          playerBuyPrice))

                    while True:
                        # Get a quantity from the player and validate it
                        self._playerState = 'chooseQuantity'
                        print('How much:')
                        quantity = self._getIntInput(game, themBeing.inventory.goods)
                        if playerBuyPrice * quantity > meBeing.inventory.money:
                            print('Insufficient funds')
                            continue
                        break

                    # This all checks out, return this.
                    print('BUY {0} {1} for {2}'.format(quantity, goodName, playerBuyPrice*quantity))
                    retval = (TradeAction.BUY, quantity, goodName, playerBuyPrice)
                    break
                elif action == 'sell':
                    while True:
                        # Get a good name from the player and validate it
                        self._playerState = 'chooseGood'
                        print('Choose a good to sell:')
                        goodName = self._getInput(game, '$>', themBeing.inventory.goods)
                        if goodName not in meBeing.inventory.goods:
                            print('You don\'t have any of that good')
                            self._printNodeGoodsList(meBeing.inventory.goods)
                            continue
                        break

                    playerSellPrice = self._sellPrices[goodName]
                    print('{0} sells for {1} per unit'.format(goodName, playerSellPrice))

                    while True:
                        # Get a quantity from the player and validate it
                        self._playerState = 'chooseQuantity'
                        print('How much:')
                        quantity = self._getIntInput(game, themBeing.inventory.goods)
                        if meBeing.inventory.goods[goodName] < quantity:
                            print('Insufficent inventory')
                            continue
                        break

                    # This all checks out, return this.
                    print('SELL {0} {1} for {2}'.format(quantity, goodName, playerSellPrice*quantity))
                    retval = (TradeAction.SELL, quantity, goodName, playerSellPrice)
                    break
                else:
                    print('Invalid trade command')
            except AbortException:
                pass
        self._playerState = ''
        return retval

    def evaluateTradeRequest(self, game: Game, meBeing: 'Being', themBeing: 'Being', tradeAction: TradeAction,
                             quantity: int, goodName: str, price: int) -> bool:
        print('Trade offer from {0}'.format(themBeing.name))
        assert(tradeAction in (TradeAction.BUY, TradeAction.SELL))
        tradeActionString = 'buy' if tradeAction == TradeAction.BUY else 'sell'
        print('Would you like to {0} {1} {2} for {3}?'.format(tradeActionString, quantity, goodName, price))
        while True:
            self._playerState = 'chooseYesNo'
            action = self._getInput(game, '$>')
            if action in ('yes', 'y', 'no', 'n'):
                break
            else:
                print('You must enter "yes" or "no"')
        self._playerState = ''
        return action in ('yes', 'y')


player = StdInPlayer()
