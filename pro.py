import ccxt
import pandas as pd
import argparse
import logging
from config.config import API_KEY, API_SECRET

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Initialize exchange using ccxt
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
})

# Fetch top symbols based on gainers or volatility
def fetch_top_symbols(limit=10, filter_gainers=True, threshold=5.0):
    logger.info(f"Fetching top {limit} {'gainers' if filter_gainers else 'volatile'} symbols...")
    tickers = exchange.fetch_tickers()
    filtered_symbols = []

    for symbol, ticker in tickers.items():
        if ticker['symbol'].endswith('/USDT'):  # Consider only USDT pairs
            price_change_percent = ticker.get('percentage')
            high = ticker.get('high', None)
            low = ticker.get('low', None)

            if high is None or low is None:
                continue

            volatility = (high - low) / low if low else 0

            if filter_gainers and price_change_percent and price_change_percent >= threshold:
                filtered_symbols.append((symbol, price_change_percent))
            elif not filter_gainers and volatility >= threshold / 100:
                filtered_symbols.append((symbol, volatility * 100))

    # Sort based on the criteria
    filtered_symbols.sort(key=lambda x: x[1], reverse=True)
    top_symbols = [symbol for symbol, _ in filtered_symbols[:limit]]
    logger.info(f"Selected symbols: {top_symbols}")
    return top_symbols

# Fetch historical data
def fetch_data(symbol, timeframe='1h', limit=100):
    logger.info(f"Fetching historical data for {symbol}...")
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except ccxt.BaseError as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# Calculate returns based on strategy
def calculate_returns(df):
    if df.empty or len(df) < 30:
        return 0.0

    df['short_ma'] = df['close'].rolling(window=10).mean()
    df['long_ma'] = df['close'].rolling(window=30).mean()

    df['signal'] = 0
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
    df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1

    df['strategy_return'] = df['signal'].shift(1) * df['close'].pct_change()
    total_return = (df['strategy_return'] + 1).prod() - 1

    return total_return

# Backtesting function
def backtest(symbols):
    logger.info(f"Backtesting for symbols: {symbols}")
    results = []

    for symbol in symbols:
        df = fetch_data(symbol, limit=1000)
        if df.empty:
            logger.warning(f"No data for {symbol}. Skipping...")
            continue

        total_return = calculate_returns(df)
        logger.info(f"Total return for {symbol}: {total_return * 100:.2f}%")
        results.append((symbol, total_return))

    results.sort(key=lambda x: x[1], reverse=True)
    for symbol, total_return in results:
        logger.info(f"Symbol: {symbol}, Total Return: {total_return * 100:.2f}%")

    return results

# Main function
def main():
    parser = argparse.ArgumentParser(description="Crypto Trading Bot")
    parser.add_argument('--backtest', action='store_true', help='Run backtest instead of live trading')
    parser.add_argument('--scg', action='store_true', help='Use top gainers')
    parser.add_argument('--scv', action='store_true', help='Use top volatile symbols')
    args = parser.parse_args()

    if args.backtest:
        if args.scg:
            symbols = fetch_top_symbols(limit=10, filter_gainers=True, threshold=5.0)
        elif args.scv:
            symbols = fetch_top_symbols(limit=10, filter_gainers=False, threshold=5.0)
        else:
            logger.error("Please specify either --scg or --scv for backtesting.")
            return
        backtest(symbols)
    else:
        logger.error("Live trading is not implemented in this version.")
        return

if __name__ == "__main__":
    main()
