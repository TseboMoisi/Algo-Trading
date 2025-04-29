from ibapi.contract import Contract # imports the Contract class from IBAPI

# futures contracts 
def future(symbol, exchange, contract_month, currency="USD", multiplier=""): 
    # symbol is the futures symbol, for example 'ES' for E-mini S&P 500
    # exchange is which exchange the security is traded on like CME
    # contract month is the expiration month
    # Multiper specifies the contract size

    contract = Contract()
    contract.symbol = symbol
    contract.exchange = exchange
    contract.lastTradeDateorContractMonth = contract_month
    contract.secType = "FUT"
    contract.currency = currency
    if multiplier:
        contract.multiplier = multiplier
    return contract

# stock contract
def stock(symbol, exchange, currency):

    contract = Contract()
    contract.symbol = symbol
    contract.exchange = exchange
    contract.currency = currency
    contract.secType = "STK"
    return contract 

# options contract
def option(symbol, exchange, contract_month, strike, right):
    # strike is the price at which we agree to sell/buy the underlying asset
    # right is the option type C for call option and P for put option

    contract = Contract()
    contract.symbol = symbol 
    contract.exchange = exchange 
    contract.lastTradeDateorContractMonth = contract_month
    contract.strike = strike
    contract.right = right
    contract.secType = "OPT"
    return contract 