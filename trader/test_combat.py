import pytest
from trader.combat import Combat, CombatEventCode, CombatAction
from trader.profiles import Vessel
from trader.profiles import VesselUpgrade


@pytest.fixture
def vessels():
    gun = VesselUpgrade(name='gun',
                        offenseMod=10,
                        defenseMod=0,
                        capacityMod=0,
                        maneuverabilityMod=0,
                        stealthMod=0,
                        upgradePoints=2,
                        price=100)
    shield = VesselUpgrade(name='shield',
                           offenseMod=0,
                           defenseMod=10,
                           capacityMod=0,
                           maneuverabilityMod=0,
                           stealthMod=0,
                           upgradePoints=2,
                           price=100)

    v1 = Vessel(name='v1',
                offense=0,
                defense=0,
                capacity=50,
                maneuverability=50,
                stealth=0,
                upgradePoints=10,
                price=50)
    v1.addUpgrade(gun)
    v1.addUpgrade(shield)

    v2 = Vessel(name='v2',
                offense=0,
                defense=0,
                capacity=50,
                maneuverability=101,
                stealth=0,
                upgradePoints=10,
                price=50)
    v2.addUpgrade(gun)
    v2.addUpgrade(shield)

    return (v1, v2)


def _assert_post_constructor_stuff(c):
    assert len(c._vesselPairs) == 2
    assert c._vesselPairs[0][0] == 'being2'  # Sorted by maneuverability OK
    assert c._vesselPairs[1][0] == 'being1'
    assert c._life['being1'] == 10  # Life initialized OK
    assert c._life['being2'] == 10
    assert len(c.eventLog()) == 2  # event log initialized OK
    assert c.eventLog()[0].eventCode == CombatEventCode.JOIN
    assert c.eventLog()[1].eventCode == CombatEventCode.JOIN
    assert not c.winner()


def test_one_fighter_one_fleer(vessels):
    v1, v2 = vessels
    c = Combat({'being1': v1, 'being2': v2})
    _assert_post_constructor_stuff(c)
    while c.keepGoing():
        c.doRound({'being1': CombatAction.FIGHT,
                   'being2': CombatAction.FLEE})
    lastEvent = c.eventLog()[-1:][0]
    assert lastEvent.eventCode == CombatEventCode.VICTORY
    eventBeforeLast = c.eventLog()[-2:][0]
    assert eventBeforeLast.eventCode in (CombatEventCode.DEATH,
                                         CombatEventCode.ESCAPE)
    assert c.winner() == 'being1'


def test_two_fighters(vessels):
    v1, v2 = vessels
    c = Combat({'being1': v1, 'being2': v2})
    _assert_post_constructor_stuff(c)
    while c.keepGoing():
        c.doRound({'being1': CombatAction.FIGHT,
                   'being2': CombatAction.FIGHT})
    lastEvent = c.eventLog()[-1:][0]
    assert lastEvent.eventCode == CombatEventCode.VICTORY
    eventBeforeLast = c.eventLog()[-2:][0]
    assert eventBeforeLast.eventCode == CombatEventCode.DEATH
    twoEventsBeforeLast = c.eventLog()[-3:][0]
    assert twoEventsBeforeLast.eventCode == CombatEventCode.DAMAGE
    for event in c.eventLog():
        assert event.eventCode != CombatEventCode.ESCAPE
        assert event.eventCode != CombatEventCode.FAIL_TO_ESCAPE
    assert c.winner() in ('being1', 'being2')


def test_two_fleers(vessels):
    v1, v2 = vessels
    c = Combat({'being1': v1, 'being2': v2})
    _assert_post_constructor_stuff(c)
    while c.keepGoing():
        c.doRound({'being1': CombatAction.FLEE,
                   'being2': CombatAction.FLEE})
    lastEvent = c.eventLog()[-1:][0]
    assert lastEvent.eventCode == CombatEventCode.VICTORY
    eventBeforeLast = c.eventLog()[-2:][0]
    assert eventBeforeLast.eventCode == CombatEventCode.ESCAPE
    for event in c.eventLog():
        assert event.eventCode != CombatEventCode.DAMAGE
    assert c.winner() in ('being1', 'being2')
