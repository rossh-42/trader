from collections import Counter
import combat


class Inventory:
    """
    """
    def __init__(self, goods=Counter(), vessel=None, money=0):
        self.goods = goods
        self.vessel = vessel
        self.money = int(money)

    def __str__(self):
        return 'goods={0}\nvessel={1}\nmoney={2}'.format(self.goods,
                                                         self.vessel,
                                                         self.money)

    def add(self, otherInventory):
        """
        Add another inventory into this inventory (EXCEPT the vessel).
        otherInventory - The other inventory we are adding.
        """
        self.goods += otherInventory.goods
        self.money += otherInventory.money

    def subtract(self, otherInventory):
        """
        Subtract another inventory into this inventory (EXCEPT the vessel).
        otherInventory - The other inventory we are subtracting.
        """
        self.goods -= otherInventory.goods
        self.money -= otherInventory.money


class Being:
    """
    """
    def __init__(self, game, name, player, inventory=None, initialLocation=''):
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

    def doTurn(self, game):
        return self._state.doTurn(game)

    def embarking(self, game, newDestination):
        """
        This is called to change this Being state to travelling and select a destination.
        game - The Game object.
        newDestination - The name of the destination the being is travelling to.
        """
        self._state = TravelBeingState(self, game.distance(self.currentLocation, newDestination))
        self.lastDestination = self.currentLocation
        self.destination = newDestination
        self.currentLocation = ''

    def arrived(self, game):
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

    def doTurn(self, game):
        """
        Do the next action for this being state.
        game - Game object.
        Returns True iff the being is still alive.
        """
        raise NotImplementedError("doTurn is virtual and must be overridden.")


class NodeBeingState(BeingState):
    """State where a being is at a node."""
    def __init__(self, being, game):
        self._being = being

    def _playerHasEnoughFuelToGetAnywhere(self, game):
        """Return True iff the player has enough fuel to get to any destination."""
        for destination in game.possibleDestinations(self._being):
            distToDest = game.distance(self._being.currentLocation, destination)
            if self._being.inventory.goods['fuel'] >= distToDest:
                return True
        return False

    def doTurn(self, game):
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
    def __init__(self, being, distance):
        self._being = being
        self._distance = distance

    def doTurn(self, game):
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
    def __init__(self, being):
        self._being = being

    def doTurn(self, game):
        return False
