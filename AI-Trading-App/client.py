import time
import pandas as pd
from dataclasses import dataclass, field
from ibapi.client import EClient # imports the class responsible for managing the network connection to TWS that we use to send requests/receiving responses

# List of constants we want to set, that represent the candlestick data structure 
TRADE_BAR_PROPERTIES = ["time", "open", "high", "low", "close", "volume"] # The standard properties used to price action

# This represents each price tik
@dataclass # Here we used Python's built-in dataclass to generate methods like __init__
class Tick: # represents a single price tick
    time: int 
    bid_price: float
    ask_price: float 
    bid_size: float 
    ask_size: float 
    timestamp_: pd.Timestamp = field(init=False) # A pandas Timestamp object initalized with 'field(init=False) so that it won't be passed __init__
    def __post_init__(self): # special method that runs after the normal __init__ 
        self.timestamp_ = pd.to_datetime(self.time, unit="s") # makes time a pandas Timestamp
        self.bid_price = float(self.bid_price) # makes sure they are float values
        self.ask_price = float(self.ask_price)
        self.bid_size = int(self.bid_size) # converts from floats to integers
        self.ask_size = int(self.ask_size)

class IBClient(EClient): # custom class that inherits from the Eclient class so that we extend the client functionality

    def __init__(self, wrapper): # the wrapper parameter is expected to be an instance of our IBWrapper class
    
        EClient.__init__(self, wrapper) # initializes the parent class with the wrapper object to connect our client that sends requests, and the wrapper that processes responses

    # function to get historical data
    def get_historical_data(self, request_id, contract, duration, bar_size):
        # self is the class which contains the reqHistorical Data function we use
        # request_id paramaeter is a unique identifier for the data request
        # duration is how much(eg. month's) worth data we must retrieve data

        # API call 
        self.reqHistoricalData(
            reqId=request_id,
            contract=contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="MIDPOINT", # midpoint of bid/ask
            useRTH=1, # regular trading hours
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[],
        )
        
        # wait for it to get historical data
        time.sleep(5)

        bar_sizes = ["day", "D", "week", "W", "month"] # the time interval for each data point

        # Checks what the bar_size is and then applies the suitable format
        if any(x in bar_size for x in bar_sizes): 
            fmt = "%Y%m%d"
        else:
            fmt = "%Y%m%d  %H:%M:%S"

        # Processes the data we requested
        data = self.historical_data[request_id]

        df = pd.DataFrame(data, columns=TRADE_BAR_PROPERTIES)

        # converts the data we request into proper datetime objects for easier analysis and manipulation
        df.set_index(pd.to_datetime(df.time, format=fmt), inplace=True)
    
        df.drop("time", axis=1, inplace=True) # removes the original "time" column for formatting
        df["symbol"] = contract.symbol # adds symbol column
        df.request_id = request_id 
        return df # Returns our fixed up data in the Dataframe


    # function to request data for several contracts
    def get_historical_data_for_many(self, request_id, contracts, duration, bar_size, col_to_use="close"):
            # request_id is an identifier for tracking requests, (starts at e.g. 99, then 100 for next security)
            # col_to_use is parametere we use to specify the data columns we want to include

            dfs = [] # list to store the DataFrames 
            
            # loops through all the securties we want to request DataFrame 
            for contract in contracts:
                data = self.get_historical_data(request_id, contract, duration, bar_size)
                dfs.append(data) # After we call the function we created above, we attach the results to the list of DataFrames
                request_id += 1 # Create a new request id

            # Returns our data changed for analysis
            return (
                pd.concat(df) # Groups together all our dataframes into 1
                .reset_index() # Reset our index after we dropped time in the first function
                .pivot( # Reshapes data
                    index="time", columns="symbol", values=col_to_use 
                )
            )


    # Function to start and stop the streaming data
    def get_streaming_data(self, request_id, contract):

        self.reqTickByTickData( # TWS API method to request tick-by-tick data
            reqId=request_id,
            contract=contract,
            tickType="BidAsk", # return bid and ask price updates
            numberOfTicks=0, # continuously stream data without limits
            ignoreSize=True 
        )

        time.sleep(10) # Wait for the connection be established

        while True: # Infinite loop to continously check for and process incoming data
            if self.stream_event.is_set(): # if a new data event happens
                yield Tick( # we make a Tick object from the streaming data we get (yield doesn't stop for the function unlike return)
                    *self.streaming_data[request_id]) # unpacks the data as arguments to __init__
                self.stream_event.clear() # resets the event flag after processing

    def stop_streaming_data(self, request_id):
        self.cancelTickByTickData(reqId=request_id) # end the data stream