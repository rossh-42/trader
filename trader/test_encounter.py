from trader import combat
from trader.encounter import Encounter, EncounterStateCode
from trader.game import Game
from trader.players.boarder import Boarder
from trader.players.briberrefuser import BriberRefuser
from trader.players.randomPlayer import RandomPlayer
from trader import search
from trader import trade


def test_trade_encounter():
    for x in range(100):
        game = Game([RandomPlayer(verbose=False), RandomPlayer(verbose=False)])
        being1 = game.beings[0]
        being2 = game.beings[1]
        e = Encounter(game, [being1, being2],
                      {'RandomPlayer1': EncounterStateCode.TRADE,
                       'RandomPlayer2': EncounterStateCode.TRADE})
        assert e.state() == EncounterStateCode.TRADE
        while True:
            keepGoing = e.doTurn()
            assert e.state() == EncounterStateCode.TRADE
            if not keepGoing:
                break

        assert e.eventLog()[0].eventCode == trade.JOIN
        assert e.eventLog()[1].eventCode == trade.JOIN
        for eventIndex in range(2, len(e.eventLog())-1):
            assert e.eventLog()[eventIndex].eventCode in (trade.TRANSACTION, trade.REFUSAL)
        lastEvent = e.eventLog()[-1:][0]
        assert lastEvent.eventCode == trade.LEAVE


def test_combat_encounter():
    for x in range(100):
        game = Game([RandomPlayer(verbose=False), RandomPlayer(verbose=False)])
        being1 = game.beings[0]
        being2 = game.beings[1]
        e = Encounter(game, [being1, being2],
                      {'RandomPlayer1': EncounterStateCode.COMBAT,
                       'RandomPlayer2': EncounterStateCode.COMBAT})
        assert e.state() == EncounterStateCode.COMBAT
        while True:
            keepGoing = e.doTurn()
            assert e.state() == EncounterStateCode.COMBAT
            if not keepGoing:
                break

        lastEvent = e.eventLog()[-1:][0]
        assert lastEvent.eventCode == combat.CombatEventCode.VICTORY
        eventBeforeLast = e.eventLog()[-2:][0]
        assert eventBeforeLast.eventCode in (combat.CombatEventCode.DEATH, combat.CombatEventCode.ESCAPE)
        assert len(e.eventLog()) >= 4


def test_board_encounter():
    for x in range(100):
        game = Game([Boarder(verbose=False), Boarder(verbose=False)])
        being1 = game.beings[0]
        being2 = game.beings[1]
        e = Encounter(game, [being1, being2],
                      {'Boarder1': EncounterStateCode.SEARCH,
                       'Boarder2': EncounterStateCode.TRADE})
        assert e.state() == EncounterStateCode.SEARCH
        while True:
            keepGoing = e.doTurn()
            assert e.state() == EncounterStateCode.SEARCH
            if not keepGoing:
                break

        if not e.eventLog():
            continue
        lastEvent = e.eventLog()[-1:][0]
        assert lastEvent.eventCode == search.SearchEventCode.EVENT_SEIZE
        eventBeforeLast = e.eventLog()[-2:][0]
        assert eventBeforeLast.eventCode == search.SearchEventCode.EVENT_BOARD


def test_bribe_refuse_encounter():
    for x in range(100):
        game = Game([BriberRefuser(verbose=False), BriberRefuser(verbose=False)])
        being1 = game.beings[0]
        being2 = game.beings[1]
        e = Encounter(game, [being1, being2],
                      {'BriberRefuser1': EncounterStateCode.SEARCH,
                       'BriberRefuser2': EncounterStateCode.SEARCH})
        assert e.state() == EncounterStateCode.SEARCH
        while True:
            keepGoing = e.doTurn()
            assert e.state() == EncounterStateCode.SEARCH
            if not keepGoing:
                break

        if not e.eventLog():
            continue
        lastEvent = e.eventLog()[-1:][0]
        assert lastEvent.eventCode == search.SearchEventCode.EVENT_BRIBE_REFUSE
        eventBeforeLast = e.eventLog()[-2:][0]
        assert eventBeforeLast.eventCode == search.SearchEventCode.EVENT_SOLICIT_BRIBE
