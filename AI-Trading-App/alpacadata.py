import pandas as pd
import alpaca_trade_api as tradeapi
import datetime
from datetime import timedelta

# Set up Alpaca API credentials
# Replace with your actual API key and secret
API_KEY = 'PKUS51O4UYY0CVNN043D'
API_SECRET = '9sXWKRHgVJYiKcaT8IHNqXyQ68OY9FgbKWpK8NMm'
BASE_URL = 'https://paper-api.alpaca.markets'  # Use this for paper trading

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def get_historical_data(symbol, timeframe='1Day', start_date=None, end_date=None):

    # Set default dates if not provided
    if end_date is None:
        end_date = datetime.datetime.now()
    else:
        end_date = pd.Timestamp(end_date)
        
    if start_date is None:
        start_date = end_date - timedelta(days=30)  # Default to 30 days
    else:
        start_date = pd.Timestamp(start_date)
    
    # Format for Alpaca API
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get the data
    bars = api.get_bars(
        symbol,
        timeframe,
        start=start_date_str,
        end=end_date_str,
        adjustment='raw'  # 'raw', 'split', 'dividend', 'all'
    ).df
    
    # Reset index to make timestamp a column
    bars = bars.reset_index()
    
    # Rename columns to match typical OHLCV format
    bars = bars.rename(columns={
        'timestamp': 'time',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume'
    })
    
    # Add symbol column
    bars['symbol'] = symbol
    
    return bars

# Example usage for a single symbol
aapl_data = get_historical_data(
    symbol='AAPL',
    timeframe='15Min',
    start_date='2023-10-01',
    end_date='2023-10-15'
)

print(f"Retrieved {len(aapl_data)} bars for AAPL")
print(aapl_data.head())

# Retrieve data for multiple stocks
def get_historical_data_for_many(symbols, timeframe='1Day', start_date=None, end_date=None):
    
    
    # Dictionary of DataFrames with historical price data
    
    data_dict = {}
    
    for symbol in symbols:
        try:
            data = get_historical_data(symbol, timeframe, start_date, end_date)
            data_dict[symbol] = data
            print(f"Retrieved {len(data)} bars for {symbol}")
        except Exception as e:
            print(f"Error retrieving data for {symbol}: {e}")
    
    return data_dict

# Example usage for multiple symbols
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
all_data = get_historical_data_for_many(
    symbols=symbols,
    timeframe='1Day',
    start_date='2025-02-01',
    end_date='2025-03-02'
)

# Create a consolidated dataframe with closing prices
if all_data:
    # Combine all dataframes
    all_dfs = []
    for symbol, df in all_data.items():
        all_dfs.append(df)
    
    if all_dfs:
        combined_df = pd.concat(all_dfs)
        
        # Create pivot table with time as index, symbols as columns, close price as values
        pivot_df = combined_df.pivot(index='time', columns='symbol', values='close')
        
        print("\nPivot table of closing prices:")
        print(pivot_df.head())