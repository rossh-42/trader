import networkx as nx
from profiles import Item
from profiles import VesselUpgrade
from profiles import Vessel
from profiles import EventProfile


graph = nx.Graph()
standardCommodities = {}


def GunsPriceFunc(day, events):
    offset = 0
    if 'civil_war' in events:
        offset += 20
    if 'mars_earth_war' in events:
        offset += 20
    return offset


standardCommodities['guns'] = Item(name='guns', price=75, dynamicFunc=GunsPriceFunc)


def ButterPriceFunc(day, events):
    offset = 0
    if day % 100 > 90:
        offset += 10
    if 'famine' in events:
        offset += 10
    return offset


standardCommodities['butter'] = Item(name='butter', price=10, dynamicFunc=ButterPriceFunc)
standardCommodities['super gun'] = VesselUpgrade(name='super gun',
                                                 offenseMod=200,
                                                 defenseMod=0,
                                                 capacityMod=0,
                                                 maneuverabilityMod=0,
                                                 stealthMod=0,
                                                 upgradePoints=5,
                                                 price=100)
standardCommodities['super shield'] = VesselUpgrade(name='super shield',
                                                    offenseMod=0,
                                                    defenseMod=200,
                                                    capacityMod=0,
                                                    maneuverabilityMod=0,
                                                    stealthMod=0,
                                                    upgradePoints=5,
                                                    price=100)
standardCommodities['mega ship'] = Vessel(name='mega ship',
                                          offense=20,
                                          defense=20,
                                          capacity=100,
                                          maneuverability=5,
                                          stealth=0,
                                          upgradePoints=20,
                                          price=200)

famineEvent = EventProfile('famine', 50, description='There is a general famine')
civilWarEvent = EventProfile('civil_war', 50, description='The world is in a state of civil war')

marsEarthWarEvent = EventProfile('mars_earth_war',
                                 percentChance=10,
                                 description='Mars and Earth are at war',
                                 duration=50,
                                 nodes=('earth', 'mars'),
                                 edges=(('earth', 'mars')))

events = [marsEarthWarEvent]
items = standardCommodities

graph.add_node('earth', events=[famineEvent, civilWarEvent])
graph.add_node('mars', events=[famineEvent, civilWarEvent])
graph.add_node('venus', events=[famineEvent, civilWarEvent])

edgeAttrDict = {}
graph.add_edge('earth', 'mars', weight=10)
graph.add_edge('mars', 'venus', weight=22)
graph.add_edge('earth', 'venus', weight=10)
