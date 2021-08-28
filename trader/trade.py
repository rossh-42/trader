# TradeAction
BUY = 1
SELL = 2
DONE = 3
PASS = 4

# TradeEvent
TRANSACTION = 1
REFUSAL = 2
LEAVE = 3
JOIN = 4


class Trade:
    """Manage a trade session between multiple beings."""
    def __init__(self, game, beings):
        """
        game - The game object.
        beings - collection of Being objects to particpate in the trading.
        """
        assert(len(beings) == 2)
        self.beings = {}
        for being in beings:
            self.beings[being.name] = being
        self._keepGoing = True
        self._game = game

        self._eventLog = []
        for being in beings:
            self._eventLog.append(JoinTradeEvent(being.name))

    def keepGoing(self):
        """Returns true iff there is more transacting to be done."""
        return self._keepGoing

    def eventLog(self):
        """Return the full event log for this trade session."""
        return self._eventLog

    def _recordEvent(self, event, roundEvents):
        """
        Record a trade event.
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

    def isValidGoodsTransaction(self, buyerBeing, sellerBeing, goodName, quantity, price):
        if buyerBeing.inventory.money < price * quantity:
            return False
        if sellerBeing.inventory.goods[goodName] < quantity:
            return False
        return True

    def moveGoodsDockMoney(self, buyerBeing, sellerBeing, goodName, quantity, price):
        assert(self.isValidGoodsTransaction(buyerBeing, sellerBeing, goodName, quantity, price))

        buyerBeing.inventory.money -= price * quantity
        sellerBeing.inventory.money += price * quantity
        if goodName in buyerBeing.inventory.goods:
            buyerBeing.inventory.goods[goodName] += quantity
        else:
            buyerBeing.inventory.goods[goodName] = quantity
        sellerBeing.inventory.goods[goodName] -= quantity

    def doRound(self, commands):
        """
        Do a single round of trading and return a list of TradeEvents that happened.
        commands - Dictionary from being name -> (TradeAction, quantity, goodName).
        Returns the trade events generated (in order) during the round.
        """

        tradeEvents = []  # TradeEvents for this round

        for initiator in commands:
            (tradeAction, quantity, goodName, price) = commands[initiator]
            if tradeAction == BUY:
                buyerBeing = self.beings[initiator]
                sellerBeing = self._getOtherBeing(initiator)

                # Make sure this transaction is valid
                if not self.isValidGoodsTransaction(buyerBeing, sellerBeing, goodName, quantity, price):
                    self._recordEvent(TransactionTradeEvent(buyerBeing.name,
                                                            sellerBeing.name,
                                                            price,
                                                            goodName,
                                                            quantity), tradeEvents)
                    continue

                # Call into the other being's player object to make the offer
                accepted = sellerBeing.player.evaluateTradeRequest(self._game,
                                                                   sellerBeing,
                                                                   buyerBeing,
                                                                   SELL,
                                                                   quantity,
                                                                   goodName,
                                                                   price)

                if accepted:
                    # If accepted move inventory, dock money, record event
                    self.moveGoodsDockMoney(buyerBeing,
                                            sellerBeing,
                                            goodName,
                                            quantity,
                                            price)
                    self._recordEvent(TransactionTradeEvent(buyerBeing.name,
                                                            sellerBeing.name,
                                                            price,
                                                            goodName,
                                                            quantity), tradeEvents)
                else:
                    # If not accepted just record the event
                    self._recordEvent(RefusalTradeEvent(buyerBeing.name,
                                                        sellerBeing.name,
                                                        price,
                                                        goodName,
                                                        quantity), tradeEvents)
            elif tradeAction == SELL:
                sellerBeing = self.beings[initiator]
                buyerBeing = self._getOtherBeing(initiator)

                # Make sure this transaction is valid
                if not self.isValidGoodsTransaction(buyerBeing, sellerBeing, goodName, quantity, price):
                    self._recordEvent(TransactionTradeEvent(buyerBeing.name,
                                                            sellerBeing.name,
                                                            price,
                                                            goodName,
                                                            quantity), tradeEvents)
                    continue

                # Call into the other being's player object to make the offer
                accepted = buyerBeing.player.evaluateTradeRequest(self._game,
                                                                  buyerBeing,
                                                                  sellerBeing,
                                                                  BUY,
                                                                  quantity,
                                                                  goodName,
                                                                  price)

                if accepted:
                    # If accepted move inventory, dock money, record event
                    self.moveGoodsDockMoney(buyerBeing,
                                            sellerBeing,
                                            goodName,
                                            quantity,
                                            price)
                    self._recordEvent(TransactionTradeEvent(buyerBeing.name,
                                                            sellerBeing.name,
                                                            price,
                                                            goodName,
                                                            quantity), tradeEvents)
                else:
                    # If not accepted just record the event
                    self._recordEvent(RefusalTradeEvent(buyerBeing.name,
                                                        sellerBeing.name,
                                                        price,
                                                        goodName,
                                                        quantity), tradeEvents)
            elif tradeAction == PASS:
                pass
            elif tradeAction == DONE:
                self._recordEvent(LeaveTradeEvent(initiator), tradeEvents)
                self._keepGoing = False
                break
            else:
                assert(False)

        return tradeEvents


class TradeEvent:
    """Base class for all events possible in trade."""
    def __init__(self, eventCode):
        """
        eventCode - TradeEvent that identifies the most derived class.
        """
        self.eventCode = int(eventCode)


class TransactionTradeEvent(TradeEvent):
    """A successful transaction has taken place"""
    def __init__(self, buyer, seller, price, good, quantity):
        """
        buyer - The buyer in the transaction.
        seller - The seller in the transaction.
        price - The price paid per unit.
        good - The name of the good.
        quantity - The quantity of the good.
        """
        TradeEvent.__init__(self, TRANSACTION)
        self.buyer = str(buyer)
        self.seller = str(seller)
        self.price = int(price)
        self.good = str(good)
        self.quantity = int(quantity)

    def __str__(self):
        return 'TRANSACTION\nbuyer={0}\nseller={1}\nprice={2}\ngood={3}\nquantity={4}'.format(self.buyer,
                                                                                              self.seller,
                                                                                              self.price,
                                                                                              self.good,
                                                                                              self.quantity)


class RefusalTradeEvent(TradeEvent):
    """An offer has been refused."""
    def __init__(self, buyer, seller, price, good, quantity):
        """
        buyer - The buyer in the transaction.
        seller - The seller in the transaction.
        price - The price paid per unit.
        good - The name of the good.
        quantity - The quantity of the good.
        """
        TradeEvent.__init__(self, TRANSACTION)
        self.buyer = str(buyer)
        self.seller = str(seller)
        self.price = int(price)
        self.good = str(good)
        self.quantity = int(quantity)

    def __str__(self):
        return 'REFUSAL\nbuyer={0}\nseller={1}\nprice={2}\ngood={3}\nquantity={4}'.format(self.buyer,
                                                                                          self.seller,
                                                                                          self.price,
                                                                                          self.good,
                                                                                          self.quantity)


class LeaveTradeEvent(TradeEvent):
    """A being is leaving the trading session."""
    def __init__(self, beingName):
        """beingName - Name of the being leaving the trading session."""
        TradeEvent.__init__(self, LEAVE)
        self.beingName = str(beingName)

    def __str__(self):
        return 'LEAVE {0}'.format(self.beingName)


class JoinTradeEvent(TradeEvent):
    """A being is joining the trading session."""
    def __init__(self, beingName):
        """beingName - Name of the being joining the trading session."""
        TradeEvent.__init__(self, JOIN)
        self.beingName = str(beingName)

    def __str__(self):
        return 'JOIN {0}'.format(self.beingName)
