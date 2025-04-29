import time
import pandas as pd
import yfinance as yf
from dataclasses import dataclass, field
import threading
from datetime import datetime, timedelta

# List of constants for candlestick data
TRADE_BAR_PROPERTIES = ["time", "open", "high", "low", "close", "volume"]

# This represents each price tick
@dataclass
class Tick:
    time: int
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp_: pd.Timestamp = field(init=False)
    
    def __post_init__(self):
        self.timestamp_ = pd.to_datetime(self.time, unit="s") # chanages self.time to a pandas datetime object and sets the value as seconds
        self.bid_price = float(self.bid_price)
        self.ask_price = float(self.ask_price)
        self.bid_size = int(self.bid_size)
        self.ask_size = int(self.ask_size)

class YahooFinanceClient:
    def __init__(self):
        self.historical_data = {}
        self.streaming_data = {}
        self.stream_event = threading.Event() # makes new event object 
        self.active_streams = {} # Dictionary to store data about active data streams
        self.stop_flag = False # Used to initialize our streaming state as cotinue streaming, when set to true will stop streaming
    
    def get_historical_data(self, request_id, symbol, duration="2d", bar_size="30m"):
        """Get historical data for a symbol
        
        Parameters:
        - request_id: Unique identifier for this request
        - symbol: Stock ticker symbol
        - duration: Time period (e.g., "1d", "5d", "1mo", "3mo", "1y")
        - bar_size: Interval for bars ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")
        """
        # Convert to yfinance format if needed
        if duration.endswith(" D"):
            duration = duration.replace(" D", "d")
        if duration.endswith(" W"):
            duration = duration.replace(" W", "wk")
        if duration.endswith(" M"):
            duration = duration.replace(" M", "mo")
            
        # Convert bar size to yfinance format
        bar_size_map = {
            "1 min": "1m",
            "5 mins": "5m",
            "15 mins": "15m",
            "30 secs": "1m",  # Yahoo doesn't support 30s, default to 1m
            "30 mins": "30m",
            "1 hour": "60m",
            "1 day": "1d",
        }
        interval = bar_size_map.get(bar_size, bar_size)
        
        # Get data from Yahoo Finance - removed 'show_errors' parameter for compatibility
        data = yf.download(
            symbol,
            period=duration,
            interval=interval,
            progress=False
        )
        
        # Format data to match expected format
        data.reset_index(inplace=True)
        data.rename(columns={
            'Date': 'time',
            'Datetime': 'time',
            'High': 'high',
            'Low': 'low',
            'Open': 'open',
            'Close': 'close',
            'Volume': 'volume',
        }, inplace=True)
        
        # Store historical data
        self.historical_data[request_id] = data[['time', 'open', 'high', 'low', 'close', 'volume']].values.tolist()
        
        # Create and return DataFrame
        df = pd.DataFrame(self.historical_data[request_id], columns=TRADE_BAR_PROPERTIES)
        df.set_index(pd.to_datetime(df.time), inplace=True)
        df.drop("time", axis=1, inplace=True)
        df["symbol"] = symbol
        df.request_id = request_id
        return df
    
    def get_historical_data_for_many(self, request_id, symbols, duration, bar_size, col_to_use="close"):
        """Get historical data for multiple symbols"""
        dfs = []
        for symbol in symbols:
            data = self.get_historical_data(request_id, symbol, duration, bar_size)
            dfs.append(data)
            request_id += 1
        
        return (
            pd.concat(dfs)
            .reset_index()
            .pivot(
                index="time", columns="symbol", values=col_to_use
            )
        )
    
    # Function we use to poll as I said before not 'true' streaming
    def _polling_thread(self, request_id, symbol, interval):
        """Background thread that polls for updated data"""
        ticker = yf.Ticker(symbol) # request data for stock based off symbol
        
        while not self.stop_flag and request_id in self.active_streams: # function runs as longs as streaming is on, and the stream is active
            try:
                # Get latest quote
                quote = ticker.history(period="1d", interval="1m").iloc[-1] # gets the market snapshot of latest data
                last_price = quote['Close'] # extract specifically the closing price
                
                # Yahoo doesn't provide bid/ask directly, so we use last price for both
                current_time = int(datetime.now().timestamp())
                
                tick_data = (
                    current_time,
                    last_price,  # bid
                    last_price,  # ask
                    0,  # bid size (not available)
                    0,  # ask size (not available)
                )
                
                self.streaming_data[request_id] = tick_data # Updates our storage with the new tick data
                self.stream_event.set() # communicates new data is available
                
                # Wait for the specified interval
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error polling Yahoo Finance data: {e}")
                time.sleep(interval)  # Still wait before retrying
    
    def get_streaming_data(self, request_id, symbol, polling_interval=5):
        """Generator that yields streaming tick data by polling at regular intervals
        
        Parameters:
        - request_id: Unique identifier for this stream
        - symbol: Stock ticker symbol
        - polling_interval: How often to poll for new data, in seconds
        """
        # Start polling thread
        self.active_streams[request_id] = True
        thread = threading.Thread(
            target=self._polling_thread,
            args=(request_id, symbol, polling_interval),
            daemon=True
        )
        thread.start()
        
        try:
            while not self.stop_flag:
                if self.stream_event.is_set() and request_id in self.streaming_data:
                    yield Tick(*self.streaming_data[request_id])
                    self.stream_event.clear()
                time.sleep(0.1)  # Small sleep to prevent busy waiting
        except KeyboardInterrupt:
            pass
        finally:
            # Clean up
            if request_id in self.active_streams:
                del self.active_streams[request_id]
    
    def stop_streaming_data(self, request_id):
        """Stop streaming for a specific request"""
        if request_id in self.active_streams:
            del self.active_streams[request_id]
    
    def disconnect(self):
        """Stop all streams and clean up"""
        self.stop_flag = True
        self.active_streams.clear()
        time.sleep(1)  # Give threads time to stop