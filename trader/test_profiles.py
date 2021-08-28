from trader.profiles import EventProfile
from trader.profiles import Item
from trader.profiles import Vessel
from trader.profiles import VesselUpgrade


def test_price_profile():
    class DynamicFuncObj:
        def __init__(self, offset):
            self._offset = offset

        def __call__(self, day, events):
            return self._offset
    for p in range(0, 100, 5):
        for dynamicOffset in range(0, 10, 2):
            g = Item(name='foo', price=p, dynamicFunc=DynamicFuncObj(dynamicOffset))
            x = g.getPrice(0, ())
            assert x == p+dynamicOffset


def test_event_profile_percent_chance():
    for percentChance in range(0, 100, 1):
        e = EventProfile('foo', percentChance)
        count = 0
        for day in range(10000):
            if e.isHappening(day, ()):
                count += 1
        if percentChance == 0:
            assert count == 0
        elif percentChance == 100:
            assert count == 100
        else:
            assert percentChance*80 < count < percentChance*120


def test_event_profile_dynamic_func():
    class DynamicFuncObj:
        def __init__(self, percent):
            self._percent = percent

        def __call__(self, day, events):
            return self._percent
    for dynamicPercent in range(0, 100, 1):
        e = EventProfile('foo', 12, DynamicFuncObj(dynamicPercent))
        count = 0
        for day in range(10000):
            if e.isHappening(day, ()):
                count += 1
        if dynamicPercent == 0:
            assert count == 0
        elif dynamicPercent == 100:
            assert count == 100
        else:
            assert dynamicPercent*80 < count < dynamicPercent*120


def test_event_profile_duration():
    for d in range(1, 11):
        e = EventProfile('foo', percentChance=1, duration=d)
        consecutiveDays = 0
        for day in range(10000):
            if e.isHappening(day, ()):
                consecutiveDays += 1
            else:
                if consecutiveDays != 0:
                    assert consecutiveDays >= d
                    break
                consecutiveDays = 0


def test_vessel_profile():
    v = Vessel(name='foo',
               offense=10,
               defense=10,
               capacity=50,
               maneuverability=50,
               stealth=0,
               upgradePoints=10,
               price=50)
    assert v.capacity == 50
    assert v.maneuverability == 50
    assert v.price == 50
    assert v.offense == 10
    assert v.defense == 10

    v.addUpgrade(VesselUpgrade(name='gun',
                               offenseMod=10,
                               defenseMod=0,
                               capacityMod=0,
                               maneuverabilityMod=0,
                               stealthMod=0,
                               upgradePoints=2,
                               price=100))
    assert v.offense == 20
    assert v.defense == 10

    v.addUpgrade(VesselUpgrade(name='shield',
                               offenseMod=0,
                               defenseMod=10,
                               capacityMod=0,
                               maneuverabilityMod=0,
                               stealthMod=0,
                               upgradePoints=2,
                               price=100))
    assert v.offense == 20
    assert v.defense == 20
