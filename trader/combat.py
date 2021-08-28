from enum import Enum
import itertools
import random


class CombatEventCode(Enum):
    DAMAGE = 1
    DEATH = 2
    ESCAPE = 3
    FAIL_TO_ESCAPE = 4
    JOIN = 5
    VICTORY = 6


class DeathReason(Enum):
    COMBAT = 1
    OUT_OF_FUEL = 2


class CombatAction(Enum):
    FIGHT = 1
    FLEE = 2


class Combat:
    """Manage a combat session between multiple vessels."""
    # TODO: Add some concept of groups of friendlies???
    def __init__(self, vessels):
        """
        vessels - dictionary of being names to Vessel objects to participate in the combat.
        """
        for vessel in vessels:
            assert(vessel)

        def maneuverability(v):
            return v[1].maneuverability
        # This sorting ensures that attack order is determined by maneuverability.
        self._vesselPairs = sorted(vessels.items(), key=maneuverability, reverse=True)

        # Life (hit points) is initialized to be the same as the defense rating
        self._life = {}
        for vesselPair in self._vesselPairs:
            (beingName, vessel) = vesselPair
            self._life[beingName] = vessel.defense

        # Initialize the event log
        self._eventLog = []
        for vesselPair in self._vesselPairs:
            (beingName, vessel) = vesselPair
            self._eventLog.append(JoinCombatEvent(beingName))

    def keepGoing(self):
        """Returns true iff there is more than one combatant left."""
        numCombatants = 0
        for beingName in self._life:
            if self._life[beingName] > 0:
                numCombatants += 1
        return numCombatants > 1

    def winner(self):
        """
        Return the being name of the combat victor.
        (or None if that hasn't been determined yet.)
        """
        if self.keepGoing():
            return None
        for beingName in self._life:
            if self._life[beingName] > 0:
                return beingName
        assert(False)
        return None

    def eventLog(self):
        """Return the full event log for this combat."""
        return self._eventLog

    def _recordEvent(self, event, roundEvents):
        """
        Record a combat event.
        event - The new event being recorded.
        roundEvents - Collection of events for this round we'll add to.
        """
        roundEvents += [event]
        self._eventLog += [event]

    def doRound(self, commands):
        """
        Do a single round of combat and return a list of CombatEvents that happened.
        commands - Dictionary from being name -> CombatAction.
        Returns the combat events generated (in order) during the round.
        """

        combatEvents = []  # CombatEvents for this round

        # Find out which of the combatants want to flee
        fleers = []
        for beingName in commands:
            if commands[beingName] == CombatAction.FLEE:
                fleers += [beingName]

        # If anybody wants to try to flee...
        if len(fleers) > 0:
            # ...everybody does an escape roll and only the best roll escapes.
            bestEscapeRoll = [0, '']
            for vesselPair in self._vesselPairs:
                (beingName, vessel) = vesselPair
                escapeRoll = random.randint(0, vessel.maneuverability)
                if escapeRoll > bestEscapeRoll[0]:
                    bestEscapeRoll = [escapeRoll, beingName]
            if bestEscapeRoll[1] in fleers:
                self._life[bestEscapeRoll[1]] = 0
                fleers.remove(bestEscapeRoll[1])
                self._recordEvent(EscapeCombatEvent(bestEscapeRoll[1]), combatEvents)
                if not self.keepGoing():
                    self._recordEvent(VictoryCombatEvent(self.winner()), combatEvents)
                    return combatEvents
            for fleer in fleers:
                if fleer != bestEscapeRoll[1]:
                    self._recordEvent(FailToEscapeCombatEvent(fleer), combatEvents)

        # Fight!
        for attackPair in itertools.permutations(self._vesselPairs, 2):
            (attackBeingName, attackVessel) = attackPair[0]
            (defendBeingName, defendVessel) = attackPair[1]
            if self._life[attackBeingName] == 0 or self._life[defendBeingName] == 0:
                continue  # life of zero means you're already dead or were able to flee
            if attackBeingName in fleers:
                continue  # If this attacker tried to flee and failed they don't get to attack
            attackRoll = random.randint(0, attackVessel.offense)
            defendRoll = random.randint(0, defendVessel.defense)
            if attackRoll > defendRoll:
                damage = attackRoll - defendRoll
                self._life[defendBeingName] -= damage
                self._recordEvent(DamageCombatEvent(attackBeingName, defendBeingName, damage),
                                  combatEvents)
                if self._life[defendBeingName] <= 0:
                    self._recordEvent(DeathCombatEvent(defendBeingName), combatEvents)
                    self._life[defendBeingName] = 0

        if not self.keepGoing():
            self._recordEvent(VictoryCombatEvent(self.winner()), combatEvents)
        return combatEvents


class CombatEvent:
    """Base class for all events possible in combat."""
    def __init__(self, eventCode):
        """
        eventCode - CombatEvent that identifies the most derived class.
        """
        self.eventCode = eventCode


class DamageCombatEvent(CombatEvent):
    """Attacker has inflicted damage on a defender."""
    def __init__(self, attacker, defender, damage):
        """
        attacker - Name of the attacking being.
        defender - Name of the defending being.
        damage - Amount of damage inflicted.
        """
        CombatEvent.__init__(self, CombatEventCode.DAMAGE)
        self.attacker = str(attacker)
        self.defender = str(defender)
        self.damage = int(damage)


class DeathCombatEvent(CombatEvent):
    """A being has been destroyed."""
    def __init__(self, being):
        """
        being - Name of the being destroyed.
        """
        CombatEvent.__init__(self, CombatEventCode.DEATH)
        self.being = str(being)


class EscapeCombatEvent(CombatEvent):
    """A being has successfully escaped combat."""
    def __init__(self, being):
        """
        being - Name of the being that escaped.
        """
        CombatEvent.__init__(self, CombatEventCode.ESCAPE)
        self.being = str(being)


class FailToEscapeCombatEvent(CombatEvent):
    """A being has tried to escape combat and failed."""
    def __init__(self, being):
        """
        being - Name of the being that tried to escape and failed.
        """
        CombatEvent.__init__(self, CombatEventCode.FAIL_TO_ESCAPE)
        self.being = str(being)


class JoinCombatEvent(CombatEvent):
    """A being has joined combat."""
    def __init__(self, being):
        """
        vessel - Name of the vessel that joined.
        """
        CombatEvent.__init__(self, CombatEventCode.JOIN)
        self.being = str(being)


class VictoryCombatEvent(CombatEvent):
    """A being has won combat."""
    def __init__(self, being):
        """
        vessel - Name of the vessel that won.
        """
        CombatEvent.__init__(self, CombatEventCode.VICTORY)
        self.being = str(being)
