from ibapi.order import Order # Import the order class from IBAPI

# defining our order actions
BUY = "BUY"
SELL = "SELL"

# function for market order which executes instantly, with whatever the current market price
def market(action, quantity): 
    # BUY/SELL, and number of shares/units to buy or sell

    order = Order()
    order.action = action
    order.orderType = "MKT"
    order.totalQuantity = quantity 
    return order 

# function for limit order 
def limit(action, quantity, limit_price):

    order = Order()
    order.action = action
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = limit_price
    return order 

# function for stop order 
def stop(action, quantity, stop_price):
    
    order = Order()
    order.action = action 
    order.orderType = "STP"
    order.auxPrice = stop_price
    order.totalQuantity = quantity
    return order 