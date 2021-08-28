import argparse
from collections import Counter
import random
from trader import combat
from trader.encounter import Encounter
from trader.profiles import Vessel
from trader.profiles import VesselUpgrade
from typing import Optional


random.seed()


def readCustomWorld(filename: str) -> dict:
    worldGlobals: dict = {}
    with open(filename) as f:
        code = compile(f.read(), filename, 'exec')
        exec(code, worldGlobals)
    return worldGlobals


class Game:
    """
    This class encapsulates the entire game.
    It is created with essentials for defining the game like the player and the world.
    The main application loop makes the game go by repeatedly calling doTurn.
    It also serves as the primary interface for Player objects to interact with the game.
    """

    def __init__(self, players, customWorld=None):
        """
        players - Player objects.
        customWorld - Name of a Python script that defines a custom world.
        """
        self.day = 0  # And on the first day Ross initialized to zero...
        worldGlobals = {}
        if not customWorld:
            customWorld = 'trader/world.py'
        # execfile(customWorld, worldGlobals)
        worldGlobals = readCustomWorld(customWorld)
        self.graph = worldGlobals['graph']
        self.eventProfiles = worldGlobals['events']
        self.items = worldGlobals['items']
        self.globalEvents = []

        self.beings = []
        playerNumber = 1
        for p in players:
            beingName = p.initGame(playerNumber)
            # Most of these defaults should be part of the world definition
            playerVessel = Vessel(name='starter ship',
                                  offense=0,
                                  defense=0,
                                  capacity=50,
                                  maneuverability=10,
                                  stealth=0,
                                  upgradePoints=10,
                                  price=100)
            playerVessel.addUpgrade(VesselUpgrade(name='gun',
                                                  offenseMod=10,
                                                  defenseMod=0,
                                                  capacityMod=0,
                                                  maneuverabilityMod=0,
                                                  stealthMod=0,
                                                  upgradePoints=5,
                                                  price=100))
            playerVessel.addUpgrade(VesselUpgrade(name='shield',
                                                  offenseMod=0,
                                                  defenseMod=10,
                                                  capacityMod=0,
                                                  maneuverabilityMod=0,
                                                  stealthMod=0,
                                                  upgradePoints=5,
                                                  price=100))
            g = Counter()
            g['fuel'] = 1000
            inv = Inventory(vessel=playerVessel, goods=g, money=1000)
            being = Being(game=self,
                          name=beingName,
                          player=p,
                          inventory=inv,
                          initialLocation=list(self.graph)[random.randint(0, len(self.graph)-1)])
            self.beings.append(being)
            playerNumber += 1

        self.nodeEventNames = {}  # Dictionary of nodeName -> list of event names happening there now
        self.edgeEventNames = {}  # Dictionary of (nodeName0, nodeName1) -> list of event names happening there now

        self.encounters = []

        # This doesn't do anything now, but I leave it in to validate the DOT generating stuff
        # self.generateDotFile()

    def getBeingByName(self, name):
        """
        Return a Being object given a name.
        name - Name of the Being object we're looking for.
        Will return None if no Being object with that name was found.
        """
        for being in self.beings:
            if being.name == name:
                return being
        return None

    def generateDotFile(self):
        """
        Return a string the represents the current graph state in DOT syntax.
        This function should probably move to the UI player when such a thing exists.
        Also worth noting is that there are some hard-coded hacks in pygraph that
        this code kind of assumes in terms of picking the right colors, etc.
        """

        # Go through all the nodes and set our current location red
        # (if it's a node)
        for node in self.graph:
            if node == self.currentLocation:
                self.graph.add_node_attribute(node, color='red')
                self.graph.add_node_attribute(node, fontcolor='red')
            else:
                self.graph.add_node_attribute(node, color='white')
                self.graph.add_node_attribute(node, fontcolor='white')

        # Normalize the weights
        weights = []
        for edge in self.graph.edges():
            weights.append(self.graph.edge_weight(edge[0], edge[1]))
        minWeight = float(min(weights))

        # Go through all the edges and set our current location red
        # (if it's an edge)
        for edge in self.graph.edges():
            if self.destination in edge and self.lastDestination in edge:
                self.graph.add_edge_attribute(edge[0], edge[1], ('color', 'red'))
            else:
                self.graph.add_edge_attribute(edge[0], edge[1], ('color', 'white'))
            normalizedWeight = self.graph.edge_weight(edge[0], edge[1]) / minWeight
            self.graph.add_edge_attribute(edge[0], edge[1], ('len', normalizedWeight))

        # Turn this into DOT and return the string
        # return pygraph.graph_to_dot(self.graph)
        assert False, 'This function does not work yet'
        # networkx.drawing.nx_pydot.write_dot(graph, path)

    def possibleDestinations(self, being):
        """
        Return a tuple of possible destinations based on player's current location.
        being - The Being object.
        """
        return tuple(self.graph.neighbors(being.currentLocation))

    def _localSupply(self, nodeName):
        """
        Return a Counter object with the local supply for a particular node and adjacent nodes and edges.
        nodeName - Name of the node.
        """
        retval = Counter()
        nodesToSearch = [nodeName] + self.graph.neighbors(nodeName)
        for node in nodesToSearch:
            for being in self.beings:
                if being.currentLocation == node:
                    retval += being.inventory.goods
                elif being.lastDestination in nodesToSearch and being.destination in nodesToSearch:
                    retval += being.inventory.goods
        return retval

    def _localDemand(self, nodeName):
        """
        Return a Counter object with the local demand for a particular node.
        nodeName - Name of the node.
        """
        demandMod = Counter(0)

        # Each node can set 'demandMod' to modify demand based on environment, culture, or history
        nodeAttrDict = self.getNodeAttrDict(nodeName)
        if 'demandMod' in nodeAttrDict:
            demandMod = nodeAttrDict['demandMod']

        # Events on this node modify demand
        for item in self.items:
            demandMod[item.name] += item.dynamicFunc(self.day, self.nodeEventNames[nodeName])

    def localPrices(self, nodeName):
        """
        Return a Counter object with the local prices for a particular node.
        nodeName - Name of the node.
        """
        supply = self._localSupply(nodeName)
        demand = self._localDemand(nodeName)
        retval = Counter(0)
        for item in self.items:
            itemDemand = (demand[item.name]*10) + 100
            itemSupply = min(supply[item.name], 10)
            # factor = (itemDemand / itemSupply)
            retval[item.name] = item.price * (itemDemand / itemSupply)
        return retval

    def distance(self, node1, node2):
        """Return the distance between two nodes."""
        return int(self.getEdgeAttrDict(node1, node2)['weight'])

    def _calculateAndSetNodeEvents(self, nodeName):
        """
        Calculates and returns a tuple of event names happening on a given node.
        nodeName - Name of a node.
        """
        assert(nodeName)
        nodeAttrDict = self.getNodeAttrDict(nodeName)
        eventNames = []
        events = nodeAttrDict['events']
        for eventProfile in events:
            if eventProfile.isHappening(self.day, eventNames):
                eventNames.append(eventProfile.name)
        for eventProfile in self.eventProfiles:
            if eventProfile.name in self.globalEvents:
                if nodeName in eventProfile.nodes:
                    eventNames.append(eventProfile.name)
        self.nodeEventNames[nodeName] = eventNames

    def getCurrentNodeEvents(self, being):
        assert(being.currentLocation != '')
        assert(being.lastDestination == '')
        assert(being.destination == '')
        return self.nodeEventNames[being.currentLocation]

    def _calculateAndSetEdgeEvents(self, edgeName):
        """
        Calculate and return the names of events happening on this edge.
        edgeName - Tuple of two node names that define an edge.
        """
        assert(edgeName[0])
        assert(edgeName[1])
        eventNames = []
        for eventProfile in self.eventProfiles:
            if eventProfile.name in self.globalEvents:
                currentEdge = sorted([edgeName[0], edgeName[1]])
                for edge in eventProfile.edges:
                    if currentEdge == sorted(edge):
                        eventNames.append(eventProfile.name)
        canonicalEdgeName = tuple(sorted([edgeName[0], edgeName[1]]))
        self.edgeEventNames[canonicalEdgeName] = eventNames

    def getCurrentEdgeEvents(self, being):
        assert(being.currentLocation == '')
        assert(being.lastDestination != '')
        assert(being.destination != '')
        canonicalEdgeName = tuple(sorted([being.lastDestination, being.destination]))
        return self.edgeEventNames[canonicalEdgeName]

    def getNodeEventDescription(self, eventName, being):
        """
        Get the description for an event that is happening (or could happen)
        for the node the player is currently at.  It is assumed that this event
        is registered as possible for the current location.
        eventName - Name of the event you want the description for.
        being - The Being object (from which we'll get the location).
        returns - A string describing the event.
        """
        nodeAttrDict = self.getNodeAttrDict(being.currentLocation)
        eventProfiles = nodeAttrDict['events']
        for eventProfile in eventProfiles:
            if eventProfile.name == eventName:
                return eventProfile.description
        for eventProfile in self.eventProfiles:
            if eventProfile.name == eventName:
                return eventProfile.description
        assert(False)  # This event can't happen at this node!

    def encounterCheck(self, being):
        """
        Check to see if a being has come across an encounter.
        being - Being object that is doing the check.
        """
        if being.isDead():  # Skip the dead
            return

        if being.currentLocation != '':  # Node
            for otherBeing in self.beings:
                if otherBeing.name == being.name:
                    continue  # Skip yourself
                if otherBeing.isDead():
                    continue  # Skip the dead
                if otherBeing.currentLocation == being.currentLocation:
                    self.createEncounter(being, otherBeing)
                    return
        else:  # Edge
            for otherBeing in self.beings:
                if otherBeing.name == being.name:
                    continue  # Skip yourself
                if otherBeing.isDead():
                    continue  # Skip the dead
                if sorted([otherBeing.lastDestination, otherBeing.destination]) == sorted([being.lastDestination, being.destination]):  # noqa: E501
                    # These two are on the same edge, check their distances
                    if otherBeing.destination == being.destination:  # same direction
                        if being._state._distance == otherBeing._state._distance:
                            self.createEncounter(being, otherBeing)
                            return
                    else:  # opposing directions
                        distance = self.distance(being.lastDestination, being.destination)
                        if being._state._distance + otherBeing._state._distance == distance:
                            self.createEncounter(being, otherBeing)
                            return

    def createEncounter(self, being1, being2):
        """
        Create an encounter between two beings.
        being1 - Being object.
        being2 - Being object.
        """

        # If either of these beings are already in an encounter bug out
        for encounter in self.encounters:
            for being in encounter._beings:
                if being.name == being1 or being.name == being2:
                    return

        # Call each player to get initState
        initStates = {}
        initStates[being1.name] = being1.player.voteInitState(self, being2)
        initStates[being2.name] = being2.player.voteInitState(self, being1)

        # Create the encounter and put it in the collection
        self.encounters.append(Encounter(self,
                                         [being1, being2],
                                         initStates))

    def getNodeAttrDict(self, node):
        """
        Get the attributes from a node from the graph and make them a dictionary.
        node - The name of the node you want attributes for.
        """
        return self.graph.nodes[node]
        # attrList = self.graph.node_attributes(node)
        # for attr in attrList:
        #     if type(attr) == type({}):
        #         return attr
        # return {}

    def getEdgeAttrDict(self, node1, node2):
        """
        Get the attributes from an edge from the graph and make them a dictionary.
        node1 - The name of the first node.
        node2 - The name of the second node.
        """
        return self.graph.get_edge_data(node1, node2)
        # attrList = self.graph.edge_attributes((node1, node2))
        # for attr in attrList:
        #     if type(attr) == type({}):
        #         retval = attr
        #         retval['wt'] = self.graph.edge_weight((node1, node2))
        #         return retval

        # retval = {}
        # retval['wt'] = self.graph.edge_weight(node1, node2)
        # return retval

    def _calculateAndSetGlobalEvents(self):
        """Calculate the global events and record their names."""
        self.globalEvents = []
        for eventProfile in self.eventProfiles:
            if eventProfile.isHappening(self.day, self.globalEvents):
                self.globalEvents += [eventProfile.name]

    def doTurn(self):
        """Process one turn of the game engine."""
        self.day += 1

        # Calculate and set all the events
        self._calculateAndSetGlobalEvents()
        for node in self.graph.nodes():
            self._calculateAndSetNodeEvents(node)
        for edge in self.graph.edges():
            self._calculateAndSetEdgeEvents(edge)

        for being in self.beings:
            # print('\nTURN: {0}'.format(being.name))
            being.doTurn(self)
            self.encounterCheck(being)

        # Resolve all the encounters
        for encounter in self.encounters:
            while True:
                keepGoing = encounter.doTurn()
                if not keepGoing:
                    break
        self.encounters = []

        return True


class Player:
    """The interface you must define to create a new player."""

    def initGame(self, playerNumber):
        """
        Call to each player to start a game.
        playerNumber - Number that is used to uniquify each player name.
        returns Name of the being that represents the player.
        """
        raise NotImplementedError("initGame is virtual and must be overridden.")

    def chooseDestination(self, game):
        """
        Choose a new destination node.  This must be a neighbor node to your current location.
        game - Game object.
        Returns the name of the new destination node.
        """
        raise NotImplementedError("chooseDestination is virtual and must be overridden.")

    def safeTravelUpdate(self, game, distanceLeft):
        """
        You have safely and uneventfully travelled for one day.
        game - Game object.
        """
        raise NotImplementedError("safeTravelUpdate is virtual and must be overridden.")

    def voteInitState(self, game, being):
        """
        Vote on what state to begin an encounter in.
        being - The other being you are about to encounter.
        Return one of (encounter.EncounterStateCode.COMBAT,
                       encounter.EncounterStateCode.TRADE,
                       encounter.EncounterStateCode.SEARCH).
        """
        raise NotImplementedError("voteInitState is virtual and must be overridden.")

    def chooseCombatAction(self, game, being, cmbt):
        """
        You have been confronted by an enemy and must choose a response.
        game - Game object.
        being - Being object of the enemy.
        cmbt - Combat object with the status of the combat.
        Returns a CombatAction
        """
        raise NotImplementedError("chooseCombatAction is virtual and must be overridden.")

    def combatEvents(self, game, events):
        """
        A series of updates for ongoing combat.
        game - Game object.
        events - List of objects of type CombatEvent.
        """
        raise NotImplementedError("combatEvents is virtual and must be overridden.")

    def arrived(self, game):
        """
        You have arrived at your destination node.
        game - the Game object.
        """
        raise NotImplementedError("arrived is virtual and must be overridden.")

    def nodeEvents(self, game, events):
        """
        Tell the player which events are happening at the node they are currently at.
        game - the Game object.
        events - A tuple of event names that are currently happening.
        For a full description of the event the player can call Game::getNodeEventDescription.
        """
        raise NotImplementedError("nodeEvents is virtual and must be overridden.")

    def advertiseTrade(self, game, meBeing):
        """
        Ask the player to advertise the sell prices for all goods in his inventory.
        game - the Game object.
        meBeing - Being object representing you.
        Returns a dictionary from goodName -> sellPrice.
        """
        raise NotImplementedError("advertiseTrade is virtual and must be overridden.")

    def readTradeAdvertisement(self, game, prices):
        """
        Receive advertisments about another player's inventory and prices.
        game - the Game object.
        prices - a dictionary from goodName -> sellPrice.
        """
        raise NotImplementedError("readTradeAdvertisement is virtual and must be overridden.")

    def chooseTradeAction(self, game, meBeing, themBeing):
        """
        You have an opportunity to trade commodities, weapons, or vessels.
        game - the Game object.
        meBeing - Being object representing you.
        themBeing - Being object representing your counterpart.
        Returns a tuple of (TradeAction, quantity, goodName, price).
        """
        raise NotImplementedError("chooseTradeAction is virtual and must be overridden.")

    def evaluateTradeRequest(self, game, meBeing, themBeing, tradeAction, quantity, goodName, price):
        """
        You have an opportunity to trade commodities, weapons, or vessels.
        game - the Game object.
        meBeing - Being object representing you.
        themBeing - Being object representing your counterpart.
        tradeAction - One of TradeAction
        quantity - How much of the good.
        goodName - Name of the good.
        price - Price per unit being offered.
        Returns True or False.
        """
        raise NotImplementedError("evaluateTradeRequest is virtual and must be overridden.")

    def tradeEvents(self, game, events):
        """
        A series of updates for ongoing trade.
        game - Game object.
        events - List of objects of type TradeEvent.
        """
        raise NotImplementedError("tradeEvents is virtual and must be overridden.")

    def chooseSearchAction(self, game, meBeing, themBeing):
        """
        game - the Game object.
        meBeing - Being object representing you.
        themBeing - Being object representing your counterpart.
        Returns one of (search.BOARD, search.SOLICIT_BRIBE, search.PASS, search.FIGHT)
        """
        raise NotImplementedError("chooseSearchAction is virtual and must be overridden.")

    def evaluateBoardRequest(self, game, meBeing, themBeing):
        """
        Evaluate a request to board your vessel.
        game - the Game object.
        meBeing - Being object representing you.
        themBeing - Being object representing your counterpart.
        Returns one of (search.PASS, search.FIGHT, search.SUBMIT).
        """
        raise NotImplementedError("evaluateBoardRequest is virtual and must be overridden.")

    def evaluateBribeSolicitation(self, game, meBeing, themBeing):
        """
        Evaluate a solicitation of a bribe.
        game - the Game object.
        meBeing - Being object representing you.
        themBeing - Being object representing your counterpart.
        Returns a tuple of  ( (search.PASS, search.FIGHT, search.SUBMIT), bribeAmount )
        """
        raise NotImplementedError("evaluateBribeSolicitation is virtual and must be overridden.")

    def seize(self, game, themInventory):
        """
        You have successfully boarded another vessel and can seize what you like from their inventory.
        game - the Game object.
        themInventory - Inventory of the vessel you have boarded.
        Returns a being.Inventory object of the stuff you are seizing.
        """
        raise NotImplementedError("seize is virtual and must be overridden.")

    def searchEvents(self, game, events):
        """
        A series of updates for ongoing search encounter.
        game - Game object.
        events - List of objects of type SearchEvent.
        """
        raise NotImplementedError("searchEvents is virtual and must be overridden.")

    def death(self, game, deathReason):
        """
        You are dead.
        game - Game object.
        deathReason - Code for the reason you are dead.
        """
        raise NotImplementedError("death is virtual and must be overridden.")


class Inventory:
    """
    """
    def __init__(self,
                 goods: Counter = Counter(),
                 vessel: Optional[Vessel] = None,
                 money: int = 0):
        self.goods = goods
        self.vessel = vessel
        self.money = int(money)

    def __str__(self):
        return 'goods={0}\nvessel={1}\nmoney={2}'.format(self.goods,
                                                         self.vessel,
                                                         self.money)

    def add(self, otherInventory: 'Inventory'):
        """
        Add another inventory into this inventory (EXCEPT the vessel).
        otherInventory - The other inventory we are adding.
        """
        self.goods += otherInventory.goods
        self.money += otherInventory.money

    def subtract(self, otherInventory: 'Inventory'):
        """
        Subtract another inventory into this inventory (EXCEPT the vessel).
        otherInventory - The other inventory we are subtracting.
        """
        self.goods -= otherInventory.goods
        self.money -= otherInventory.money


class Being:
    """
    """
    def __init__(self, game: Game, name: str, player: Player,
                 inventory: Optional[Inventory] = None, initialLocation: str = ''):
        self.name = name
        self.player = player
        if inventory:
            self.inventory = inventory
        else:
            self.inventory = Inventory()
        self.destination = ''
        self.lastDestination = ''
        self.currentLocation = initialLocation
        self._state = NodeBeingState(self, game)
        self._dead = False

    def __str__(self):
        return 'name={0}\nplayer={1}\ninventory={2}\ndestination={3}\nlastDestination={4}\ncurrentLocation={5}\nstate={6}\n'.format(self.name, self.player, self.inventory, self.destination, self.lastDestination, self.currentLocation, self._state)  # noqa: E501

    def doTurn(self, game: Game):
        return self._state.doTurn(game)

    def embarking(self, game: Game, newDestination: str):
        """
        This is called to change this Being state to travelling and select a destination.
        game - The Game object.
        newDestination - The name of the destination the being is travelling to.
        """
        self._state = TravelBeingState(self, game.distance(self.currentLocation, newDestination))
        self.lastDestination = self.currentLocation
        self.destination = newDestination
        self.currentLocation = ''

    def arrived(self, game: Game):
        """
        This is called to change this Being state from travelling to node.
        game - The Game object.
        """
        self.currentLocation = self.destination
        self.lastDestination = ''
        self.destination = ''
        self._state = NodeBeingState(self, game)
        self.player.arrived(game)

    def makeDead(self):
        self._state = DeadBeingState(self)
        self._dead = True

    def isDead(self):
        return self._dead


class BeingState:
    """A base class for all being state objects."""

    def doTurn(self, game: Game):
        """
        Do the next action for this being state.
        game - Game object.
        Returns True iff the being is still alive.
        """
        raise NotImplementedError("doTurn is virtual and must be overridden.")


class NodeBeingState(BeingState):
    """State where a being is at a node."""
    def __init__(self, being: Being, game: Game):
        self._being = being

    def _playerHasEnoughFuelToGetAnywhere(self, game: Game):
        """Return True iff the player has enough fuel to get to any destination."""
        for destination in game.possibleDestinations(self._being):
            distToDest = game.distance(self._being.currentLocation, destination)
            if self._being.inventory.goods['fuel'] >= distToDest:
                return True
        return False

    def doTurn(self, game: Game):
        nodeEvents = game.getCurrentNodeEvents(self._being)
        self._being.player.nodeEvents(game, nodeEvents)

        # Does the player have enough fuel to get anywhere?
        if not self._playerHasEnoughFuelToGetAnywhere(game):
            self._being.player.death(game, combat.OUT_OF_FUEL)
            return False

        # Now let's go to the next destination
        newDestination = self._being.player.chooseDestination(game)
        if newDestination:
            assert(newDestination in game.possibleDestinations(self._being))
            assert(self._being.inventory.goods['fuel'] >= game.distance(self._being.currentLocation, newDestination))
            self._being.embarking(game, newDestination)
        else:
            # TODO: Maybe charge rent for staying in the same place?
            pass
        return True


class TravelBeingState(BeingState):
    """State where a being is travelling between nodes."""
    def __init__(self, being: Being, distance: int):
        self._being = being
        self._distance = distance

    def doTurn(self, game: Game):
        # edgeEvents = game.getCurrentEdgeEvents(self._being)

        # No combat happened, so let's just travel one unit towards the destination
        self._being.inventory.goods['fuel'] -= 1
        self._distance -= 1
        if self._distance == 0:
            self._being.arrived(game)
        else:
            if self._being.inventory.goods['fuel'] == 0:
                self._being.player.death(game, combat.OUT_OF_FUEL)
                return False
            self._being.player.safeTravelUpdate(game, self._distance)
        return True


class DeadBeingState(BeingState):
    """State where a being is dead."""
    def __init__(self, being: Being):
        self._being = being

    def doTurn(self, game: Game):
        return False


if __name__ == '__main__':
    # Command line arguments and options setup

    parser = argparse.ArgumentParser(description='Trader version 1.0')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    parser.add_argument('-w', '--world', type=str, default='',
                        help='use a custom world')
    args = parser.parse_args()

    from players.stdInPlayer import StdInPlayer
    from players.randomPlayer import RandomPlayer
    from players.merchant import MerchantPlayer
    g = Game([StdInPlayer(),
              RandomPlayer(verbose=False),
              RandomPlayer(verbose=False),
              RandomPlayer(verbose=False),
              MerchantPlayer()],
             args.world)
    keepGoing = True
    while keepGoing:
        keepGoing = g.doTurn()
