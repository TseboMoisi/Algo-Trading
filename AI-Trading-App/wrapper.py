import threading # module with tools for concurrent exectuon, async 
from ibapi.wrapper import EWrapper # a component that defines callback methods that get triggered in response to events from the IB servers

class IBWrapper(EWrapper): # define a custom class that inherits from Ewrapper

    def __init__(self): 
        EWrapper.__init__(self) # Initilizes the IBWrapper class using the parent EWrapper class, so that any custom initializations we set later are also applied to our parent class
        self.historical_data = {} # Dictionary to store retrieved market data
        self.streaming_data = {} # Dictionary to store the streaming data
        self.stream_event = threading.Event() # Allows for threads to talk to each other

    
    # A function to store historical data
    def historicalData(self, request_id, bar):
        # request id our unique identifier
        # bar is candle of price data

        # tuple with price data
        bar_data = (
            bar.date,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
        )

        # how to store the data depending on the request
        if request_id not in self.historical_data.keys(): # if statement for whether it is the first data point for this request ID
            self.historical_data[request_id] = [] # if yes then makes a new empty list for this request ID
        self.historical_data[request_id].append(bar_data) # attachtes the bar data to right requests

    # Callback function that is triggered when new bid/ask data comes 
    def tickByTickBidAsk(
            self,
            request_id,
            time,
            bid_price,
            ask_price,
            bid_size,
            ask_size,
            tick_atrrib_last
    ):
        tick_data = ( # Puts our data into a tuple
            time,
            bid_price,
            ask_price,
            bid_size,
            ask_size,
        )
        self.streaming_data[request_id] = tick_data # stores the tuple in our dictionary and used request_id as the key
        self.stream_event.set() # communicates new data is ready for usage