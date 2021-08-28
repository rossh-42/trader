from enum import Enum
import random


class EventProfile:
    """Class that defines under what circumstances something happens."""
    def __init__(self, name, percentChance, dynamicFunc=None, description=None, nodes=(), edges=(), duration=1):
        """
        name - name of the event.
        percentChance - constant percentage chance of this event existing on any given turn.
        dynamicFunc - A function object with args (day, (otherEvents)) that returns
                      percentage chance of this event existing.
        description - A text description of what this event is.
        nodes - A tuple of node names where this event will exist.
        edges - A tuple of edges (nodeName1, nodeName2) where this event will exist.
        duration - How many days this event will last when it happens.  Must be non-zero.
        """
        self.name = str(name)
        self.percentChance = float(percentChance)
        self.dynamicFunc = dynamicFunc
        self.description = str(description)
        self.nodes = nodes
        self.edges = edges
        assert(duration != 0)  # That don't make no sense
        self.duration = int(duration)
        self._startDay = None

    def isHappening(self, day, otherEvents):
        """Calculate the odds of this event happening now and return a bool."""
        # If this event has happened before
        if self._startDay:
            # and if this event is still happening:
            if day < self._startDay + self.duration:
                return True
        percentChance = self.percentChance
        if self.dynamicFunc:
            percentChance = self.dynamicFunc(day, otherEvents)
        happening = random.randint(1, 100) <= percentChance
        if happening:
            self._startDay = day
        return happening


class CombatProfile:
    """Class that describes an enemy and how often that enemy is encountered."""
    def __init__(self, eventProfile, enemyVessel):
        """
        eventProfile - EventProfile object that defines the likelyhood of combat happening.
        enemyVessel - Vessel object describing the enemy vessel to fight if combat happens.
        """
        self._eventProfile = eventProfile
        self.enemyVessel = enemyVessel

    def isHappening(self, day, otherEvents):
        return self._eventProfile.isHappening(day, otherEvents)


class ItemClassCode(Enum):
    COMMODITY = 1
    WEAPON = 2
    VESSEL = 3
    FUEL = 4


class Item:
    """
    Class that defines a buyable and / or sellable good.
    This includes how the prices for the item change over time as
    well as when certain events are happening.
    """
    def __init__(self, name, price, dynamicFunc=None, classCode=ItemClassCode.COMMODITY):
        """
        name - Name of the commodity.
        price - base price of the commodity.
        dynamicFunc - A function object with args (day, (events)) that returns
                      a price offset to be applied.
        classCode - Type code specifying the most derived class.
        """
        self.name = name
        self.price = price
        self.dynamicFunc = dynamicFunc
        self._classCode = classCode

    def classCode(self):
        return self._classCode

    def getPrice(self, day, events):
        if self.dynamicFunc:
            return self.price + self.dynamicFunc(day, events)
        return self.price


class VesselUpgrade(Item):
    """"""
    def __init__(self, name, offenseMod, defenseMod, capacityMod, maneuverabilityMod,
                 stealthMod, upgradePoints, price, dynamicFunc=None):
        """
        """
        Item.__init__(self, name, price, dynamicFunc, classCode=ItemClassCode.WEAPON)
        self.offenseMod = int(offenseMod)
        self.defenseMod = int(defenseMod)
        self.capacityMod = int(capacityMod)
        self.maneuverabilityMod = int(maneuverabilityMod)
        self.stealthMod = int(stealthMod)
        self.upgradePoints = int(upgradePoints)


class Vessel(Item):
    """
    Class that describes a vessel.
    This includes all its offsensive and defensive weapons as well as its escapability.
    """
    def __init__(self, name, offense, defense, capacity, maneuverability, stealth,
                 upgradePoints, price, dynamicFunc=None):
        """
        name - Name of the vessel.
        offense - Rating of the offensive capability of the ship.  Determines how much damage you do on attacks.
        defense - Rating of the defensive capability of the ship.  Determines how well you mitigate incoming attacks.
        capacity - Units of commodities that it can carry.
        maneuverability - Ability to evade combat, and also used to decide who attacks first.
        stealth - Ability to hide inventory when you are boarded and searched
        upgradePoints - Points available to add upgrades.
        price - See Item.
        dynamicFunc - See Item.
        """
        Item.__init__(self, name, price, dynamicFunc, classCode=ItemClassCode.VESSEL)
        self.offense = int(offense)
        self.defense = int(defense)
        self.capacity = int(capacity)
        self.maneuverability = int(maneuverability)
        self.stealth = int(stealth)
        self.upgradePoints = int(upgradePoints)
        self.upgrades = []

    def addUpgrade(self, upgrade):
        """
        Add a new upgrade to this vessel.
        upgrade - A VesselUpgrade object.
        """

        # We better have enough upgrade points to do this
        assert(self.upgradePoints >= upgrade.upgradePoints)

        self.upgrades += [upgrade]
        self.offense += upgrade.offenseMod
        self.defense += upgrade.defenseMod
        self.capacity += upgrade.capacityMod
        self.maneuverability += upgrade.maneuverabilityMod
        self.stealth += upgrade.stealthMod
        self.upgradePoints -= upgrade.upgradePoints
