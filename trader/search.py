from enum import IntEnum


class SearchAction(IntEnum):
    BOARD = 0
    SOLICIT_BRIBE = 1
    PASS = 2
    FIGHT = 3
    SUBMIT = 4


class SearchEventCode(IntEnum):
    EVENT_BOARD = 0
    EVENT_SOLICIT_BRIBE = 1
    EVENT_FIGHT = 2
    EVENT_SUBMIT = 3
    EVENT_PAY = 4
    EVENT_SEIZE = 5
    EVENT_BOARD_REFUSE = 6
    EVENT_BRIBE_REFUSE = 7


class SearchState(IntEnum):
    STATE_START = 0
    STATE_BOARD = 1
    STATE_SOLICIT_BRIBE = 2
    STATE_SEIZURE = 3
    STATE_COMBAT = 4
    STATE_PASS = 5
    STATE_PAY = 6


XXX = 666

state_table = (  # BOARD                    SOLICIT_BRIDE                    PASS                    FIGHT                     SUBMIT                                              # noqa: E501
                  (SearchState.STATE_BOARD, SearchState.STATE_SOLICIT_BRIBE, SearchState.STATE_PASS, SearchState.STATE_COMBAT, XXX),                        # STATE_START          # noqa: E501
                  (XXX,                     XXX,                             SearchState.STATE_PASS, SearchState.STATE_COMBAT, SearchState.STATE_SEIZURE),  # STATE_BOARD          # noqa: E501
                  (XXX,                     XXX,                             SearchState.STATE_PASS, SearchState.STATE_COMBAT, SearchState.STATE_PAY),      # STATE_SOLICIT_BRIBE  # noqa: E501
                  (XXX,                     XXX,                             XXX,                    XXX,                      XXX),                        # STATE_SEIZURE        # noqa: E501
                  (XXX,                     XXX,                             XXX,                    XXX,                      XXX),                        # STATE_COMBAT         # noqa: E501
                  (XXX,                     XXX,                             XXX,                    XXX,                      XXX),                        # STATE_PASS           # noqa: E501
                  (XXX,                     XXX,                             XXX,                    XXX,                      XXX))                        # STATE_PAY            # noqa: E501


class Search:
    """Manage a search and seizure session between multiple beings."""
    def __init__(self, game, beings):
        """
        game - The game object.
        beings - collection of Being objects to particpate in the search and seizure event.
        """
        assert(len(beings) == 2)
        self.beings = {}
        for being in beings:
            self.beings[being.name] = being
        self._keepGoing = True
        self._game = game

        self._eventLog = []

    def keepGoing(self):
        """Returns true iff there is more transacting to be done."""
        return self._keepGoing

    def eventLog(self):
        """Return the full event log for this search and seizure session."""
        return self._eventLog

    def _recordEvent(self, event, roundEvents):
        """
        Record a search and seizure event.
        event - The new event being recorded.
        roundEvents - Collection of events for this round we'll add to.
        """
        roundEvents += [event]
        self._eventLog += [event]

    def _getOtherBeing(self, beingName):
        """Given a being name return the Being of the other guy."""
        assert(len(self.beings) == 2)
        for being in self.beings:
            if being == beingName:
                continue
            return self.beings[being]
        assert(False)
        return None

    def doRound(self, commands):
        """
        Do a single round of the search encounter and return a list of SearchEvents that happened.
        commands - Dictionary from being name -> SearchAction.
        Returns the search events generated (in order) during the round.
        """
        searchEvents = []  # SearchEvents for this round

        for initiator in commands:
            currentState = SearchState.STATE_START
            searchAction = commands[initiator]
            bribeAmount = 0

            initiatorBeing = self.beings[initiator]
            responderBeing = self._getOtherBeing(initiator)

            while currentState in (SearchState.STATE_START, SearchState.STATE_BOARD, SearchState.STATE_SOLICIT_BRIBE):
                newState = state_table[int(currentState)][int(searchAction)]
                lastState = currentState
                currentState = newState
                assert(newState != XXX)

                if newState == SearchState.STATE_BOARD:
                    self._recordEvent(BoardRequestEvent(initiatorBeing.name,
                                                        responderBeing.name), searchEvents)
                    searchAction = responderBeing.player.evaluateBoardRequest(self._game,
                                                                              responderBeing,
                                                                              initiatorBeing)
                    if searchAction == SearchAction.PASS:
                        self._recordEvent(BoardRequestRefusalEvent(initiatorBeing.name,
                                                                   responderBeing.name), searchEvents)
                    continue
                elif newState == SearchState.STATE_SOLICIT_BRIBE:
                    self._recordEvent(SolicitBribeEvent(initiatorBeing.name,
                                                        responderBeing.name), searchEvents)
                    (searchAction, bribeAmount) = responderBeing.player.evaluateBribeSolicitation(self._game,
                                                                                                  responderBeing,
                                                                                                  initiatorBeing)
                    if searchAction == SearchAction.PASS:
                        self._recordEvent(RefuseBribeEvent(responderBeing.name,
                                                           initiatorBeing.name), searchEvents)
                    continue
                elif newState == SearchState.STATE_SEIZURE:
                    seizeInventory = initiatorBeing.player.seize(self._game, responderBeing.inventory)
                    initiatorBeing.inventory.add(seizeInventory)
                    responderBeing.inventory.subtract(seizeInventory)
                    self._recordEvent(SeizeEvent(initiatorBeing.name,
                                                 responderBeing.name,
                                                 seizeInventory), searchEvents)
                    break
                elif newState == SearchState.STATE_COMBAT:
                    if lastState == SearchState.STATE_START:
                        self._recordEvent(FightEvent(initiatorBeing.name,
                                                     responderBeing.name), searchEvents)
                    else:
                        self._recordEvent(FightEvent(responderBeing.name,
                                                     initiatorBeing.name), searchEvents)
                    break
                elif newState == SearchState.STATE_PASS:
                    break
                elif newState == SearchState.STATE_PAY:
                    self._recordEvent(PayBribeEvent(responderBeing.name,
                                                    responderBeing.name,
                                                    bribeAmount), searchEvents)
                    responderBeing.inventory.money -= bribeAmount
                    initiatorBeing.inventory.money += bribeAmount
                    break
                else:
                    assert(False)

        return searchEvents


class SearchEvent:
    """Base class for all events possible in search and seizure."""
    def __init__(self, eventCode):
        """
        eventCode - SearchEvent that identifies the most derived class.
        """
        self.eventCode = int(eventCode)


class BoardRequestEvent(SearchEvent):
    """A board request has taken place"""
    def __init__(self, boarder, boardee):
        """
        boarder - The being requesting boarding.
        boardee - The being being requested.
        """
        SearchEvent.__init__(self, SearchEventCode.EVENT_BOARD)
        self.boarder = str(boarder)
        self.boardee = str(boardee)

    def __str__(self):
        return 'BOARD REQUEST\nboarder={0}\nboardee={1}'.format(self.boarder,
                                                                self.boardee)


class BoardRequestRefusalEvent(SearchEvent):
    """A board request has been refused"""
    def __init__(self, boarder, boardee):
        """
        boarder - The being requesting boarding.
        boardee - The being being requested.
        """
        SearchEvent.__init__(self, SearchEventCode.EVENT_BOARD_REFUSE)
        self.boarder = str(boarder)
        self.boardee = str(boardee)

    def __str__(self):
        return 'REFUSAL\nboarder={0}\nboardee={1}'.format(self.boarder,
                                                          self.boardee)


class SeizeEvent(SearchEvent):
    """A boarding and subsequent seizure has taken place"""
    def __init__(self, boarder, boardee, seizedInventory):
        """
        boarder - The being requesting boarding.
        boardee - The being being requested.
        seizedInventory - Inventory object of the seized stuff.
        """
        SearchEvent.__init__(self, SearchEventCode.EVENT_SEIZE)
        self.boarder = str(boarder)
        self.boardee = str(boardee)
        self.seizedInventory = seizedInventory

    def __str__(self):
        return 'SEIZE\nboarder={0}\nboardee={1}'.format(self.boarder,
                                                        self.boardee)


class SolicitBribeEvent(SearchEvent):
    """A bribe solicitation has taken place"""
    def __init__(self, solicitor, payor):
        """
        solicitor - The being soliciting a bribe.
        payor - The being who is being asked for money.
        """
        SearchEvent.__init__(self, SearchEventCode.EVENT_SOLICIT_BRIBE)
        self.solicitor = str(solicitor)
        self.payor = str(payor)

    def __str__(self):
        return 'SOLICIT_BRIBE\nsolicitor={0}\npayor={1}'.format(self.solicitor,
                                                                self.payor)


class RefuseBribeEvent(SearchEvent):
    """A bribe solicitation has been refused"""
    def __init__(self, refuser, briber):
        """
        refuser - The being who is refusing to be bribed.
        briber - The being who is doing the bribing.
        """
        SearchEvent.__init__(self, SearchEventCode.EVENT_BRIBE_REFUSE)
        self.refuser = str(refuser)
        self.briber = str(briber)

    def __str__(self):
        return 'REFUSE_BRIBE\nrefuser={0}\nbriber={1}'.format(self.refuser,
                                                              self.briber)


class FightEvent(SearchEvent):
    """A bribe solicitation has taken place"""
    def __init__(self, instigator, defender):
        """
        instigator - The being who wants to initiate combat.
        defender - The other being.
        """
        SearchEvent.__init__(self, SearchEventCode.EVENT_FIGHT)
        self.instigator = str(instigator)
        self.defender = str(defender)

    def __str__(self):
        return 'FIGHT\ninstigator={0}\ndefender={1}'.format(self.instigator,
                                                            self.defender)


class PayBribeEvent(SearchEvent):
    """A bribe has been paid"""
    def __init__(self, payor, briber, amount):
        """
        payor - The being who is paying the bribe.
        briber - The being who is receiving the bribe.
        amount - Amount of money paid.
        """
        SearchEvent.__init__(self, SearchEventCode.EVENT_PAY)
        self.payor = str(payor)
        self.briber = str(briber)
        self.amount = int(amount)

    def __str__(self):
        return 'PAY_BRIBE\npayor={0}\nbriber={1}\namount={2}'.format(self.payor,
                                                                     self.briber,
                                                                     self.amount)
