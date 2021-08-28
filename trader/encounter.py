from enum import Enum
from trader.combat import Combat, CombatEventCode
from trader.search import Search, SearchAction, SearchEventCode
from trader.trade import Trade


class EncounterState:
    """A base class for all encounter state objects."""

    def doTurn(self, encounter):
        """
        Do the next action for this encounter state.
        encounter - Encounter object.
        Returns An EncounterState to say the next state to go to or END_ENCOUNTER to end the whole thing.
        """
        raise NotImplementedError("doTurn is virtual and must be overridden.")

    def state(self):
        """Return an EncounterState that describes this state."""
        raise NotImplementedError("state is virtual and must be overridden.")

    def eventLog(self):
        """Return an event log for all events that have occurred in this state."""
        raise NotImplementedError("eventLog is virtual and must be overridden.")


class EncounterStateCode(Enum):
    COMBAT = 101
    TRADE = 102
    SEARCH = 103
    END_ENCOUNTER = 104


class CombatEncounterState(EncounterState):
    def state(self):
        return EncounterStateCode.COMBAT

    def __init__(self, beings):
        combatants = {}
        for being in beings:
            combatants[being.name] = being.inventory.vessel
        self.cmbt = Combat(combatants)
        self.beings = beings
        self.roundEvents = None

    def doTurn(self, encounter):
        commands = {}

        # Get combat actions from each player
        for being in self.beings:
            combatAction = being.player.chooseCombatAction(encounter._game, being, self.cmbt)
            commands[being.name] = combatAction

        # Do the round
        self.roundEvents = self.cmbt.doRound(commands)

        # Report the events for the round to each player
        for being in self.beings:
            being.player.combatEvents(None, self.roundEvents)

        # For each event in the last round...
        for event in self.roundEvents:
            # ...if that event was a death...
            if event.eventCode == CombatEventCode.DEATH:
                # ...go looking through the Being objects...
                for being in self.beings:
                    # ...and when we find a name match...
                    if being.name == event.being:
                        # ...make him dead.
                        being.makeDead()

        if self.cmbt.keepGoing():
            return EncounterStateCode.COMBAT
        return EncounterStateCode.END_ENCOUNTER

    def eventLog(self):
        return self.cmbt.eventLog()

    def roundEvents(self):
        return self.roundEvents


class TradeEncounterState(EncounterState):
    def state(self):
        return EncounterStateCode.TRADE

    def __init__(self, game, beings):
        self.trade = Trade(game, beings)
        self.beings = beings
        assert(len(self.beings) == 2)
        self.roundEvents = None
        self._firstTime = True

    def doTurn(self, encounter):

        if self._firstTime:
            prices = self.beings[0].player.advertiseTrade(encounter._game, self.beings[0])
            self.beings[1].player.readTradeAdvertisement(encounter._game, prices)
            prices = self.beings[1].player.advertiseTrade(encounter._game, self.beings[1])
            self.beings[0].player.readTradeAdvertisement(encounter._game, prices)
            self._firstTime = False

        commands = {}

        tradeAction = self.beings[0].player.chooseTradeAction(encounter._game, self.beings[0], self.beings[1])
        commands[self.beings[0].name] = tradeAction

        tradeAction = self.beings[1].player.chooseTradeAction(encounter._game, self.beings[1], self.beings[0])
        commands[self.beings[1].name] = tradeAction

        self.roundEvents = self.trade.doRound(commands)
        if self.trade.keepGoing():
            return EncounterStateCode.TRADE
        return EncounterStateCode.END_ENCOUNTER

    def eventLog(self):
        return self.trade.eventLog()

    def roundEvents(self):
        return self.roundEvents


class SearchAndSeizureEncounterState(EncounterState):
    def state(self):
        return EncounterStateCode.SEARCH

    def __init__(self, game, beings):
        self.search = Search(game, beings)
        self.beings = beings
        assert(len(self.beings) == 2)
        self.roundEvents = None

    def doTurn(self, encounter):
        commands = {}

        searchAction = self.beings[0].player.chooseSearchAction(encounter._game, self.beings[0], self.beings[1])
        commands[self.beings[0].name] = searchAction

        searchAction = self.beings[1].player.chooseSearchAction(encounter._game, self.beings[1], self.beings[0])
        commands[self.beings[1].name] = searchAction

        if commands[self.beings[0].name] == SearchAction.PASS and commands[self.beings[1].name] == SearchAction.PASS:
            return EncounterStateCode.END_ENCOUNTER

        self.roundEvents = self.search.doRound(commands)

        lastEvent = self.eventLog()[-1:][0]
        if lastEvent == SearchEventCode.EVENT_FIGHT:
            return EncounterStateCode.COMBAT
        return EncounterStateCode.SEARCH

    def eventLog(self):
        return self.search.eventLog()

    def roundEvents(self):
        return self.roundEvents


class Encounter:
    """
    A multi-state encounter between beings.
    """
    def __init__(self, game, beings, initStates):
        """
        game - Game object
        beings - A list of Being objects.
        initStates - A dictionary being name -> EncounterState
        """
        self._game = game
        self._beings = beings
        self._state = TradeEncounterState(game, self._beings)
        for being in beings:
            if initStates[being.name] == EncounterStateCode.SEARCH:
                self._state = SearchAndSeizureEncounterState(game, self._beings)
            elif initStates[being.name] == EncounterStateCode.COMBAT:
                self._state = CombatEncounterState(self._beings)
                break

    def doTurn(self):
        nextState = self._state.doTurn(self)
        if nextState != self._state.state():
            if nextState == EncounterStateCode.SEARCH:
                self._state = SearchAndSeizureEncounterState(self._game, self._beings)
            elif nextState == EncounterStateCode.COMBAT:
                self._state = CombatEncounterState(self._beings)
            elif nextState == EncounterStateCode.END_ENCOUNTER:
                pass
            else:
                assert(False)
        return nextState != EncounterStateCode.END_ENCOUNTER

    def beings(self):
        """Return a list of beings in this encounter."""
        return self._beings

    def state(self):
        """Return an EncounterState that describes this state."""
        return self._state.state()

    def eventLog(self):
        """
        Return the event log for the current state.
        This function currently DOES NOT return events for previous states.
        """
        return self._state.eventLog()

    def roundEvents(self):
        """Return events for the last round only."""
        return self._state.roundEvents()
