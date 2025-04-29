import time
from yahoo_client import YahooFinanceClient

if __name__ == "__main__":
    # Create Yahoo Finance client
    app = YahooFinanceClient()
    
    # Get historical data
    print("Getting historical data for AAPL...")
    data = app.get_historical_data(
        request_id=99,
        symbol="AAPL",
        duration="2d",
        bar_size="15m"
    )
    
    print("Historical data for AAPL:")
    print(data.head())
    
    # Stream data (by polling)
    print("\nStarting data stream for AAPL (polling every 5 seconds)...")
    try:
        for tick in app.get_streaming_data(99, "AAPL", polling_interval=5):
            print(f"{tick.timestamp_}: AAPL - Bid: ${tick.bid_price:.2f}, Ask: ${tick.ask_price:.2f}")
    except KeyboardInterrupt:
        print("Streaming stopped by user")
    
    # Or get data for multiple symbols
    print("\nGetting data for multiple symbols...")
    multiple_data = app.get_historical_data_for_many(
        request_id=100,
        symbols=["AAPL", "MSFT", "GOOGL"],
        duration="1wk",
        bar_size="1d"
    )
    
    print("Multi-symbol data:")
    print(multiple_data.head())
    
    app.disconnect()