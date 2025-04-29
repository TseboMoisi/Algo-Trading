import threading # creates a separate thread for the client's message processing loop
import time
from wrapper import IBWrapper
from client import IBClient
from contract import stock, future, option # Import our contracts
from order import limit, market, stop, BUY, SELL # Import our orders

class IBApp(IBWrapper, IBClient): # Inherits both our custom classes, creating a single class that can both send requests and process responses

    def __init__(self, ip, port, client_id):
        IBWrapper.__init__(self) # Initializes the wrapper 
        IBClient.__init__(self, wrapper=self) # Initializes the client functionality, passing itself as the wrapper since the class inherits from IBWrapper
        self.connect(ip, port, client_id) # Creates a connection to the IB servers
        thread = threading.Thread(target=self.run, daemon=True) # makes a separate daemon thread that runs 'self.run()', which is the message processing loop that continously checks for incoming messages from the server
        thread.start()
        time.sleep(2) # allow for time to make the connection


if __name__ == "__main__":

    app = IBApp("127.0.0.1", 7497, client_id=10) # creates an instance of IBApp

    # Create contracts for these securities
    aapl = stock("AAPL", "SMART", "USD")
    gbl = future("GBL", "EUREX", "202403")
    pltr = option("PLTR", "BOX", "20240315", 20, "C")
    es = future("ES", "CME", "202506", "USD", "50")
    es.localSymbol = "ESZ5"
    for tick in app.get_streaming_data(99, es):
        print(tick)

    # Historical data request
    data = app.get_historical_data(
        request_id=99,
        contract=aapl,
        duration='2 D', # Requestings 2 days of historical data
        bar_size='30 secs' # setting the time interval of the data to 30-second bars
    )

    print("Historical data for AAPL:")
    print(data)

    # creates a limit order object
    limit_order = limit(BUY, 100, 190.00)

    time.sleep(30) # waits for 30 seconds while our app runs
    app.disconnect() # ends the connection