import ccxt
import pandas as pd
import argparse
import logging
from config.config import API_KEY, API_SECRET
from strategies.moving_average_crossover import moving_average_crossover
from strategies.momentum import calculate_momentum

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Initialize exchange
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
})

positions = {}  # Active positions: {'symbol': {'buy_price': x, 'quantity': y}}

def fetch_data(symbol, timeframe='1m', limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except ccxt.BaseError as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def fetch_symbols(limit=10, strategy='momentum'):
    logger.info(f"Fetching top {limit} symbols based on {strategy} strategy...")
    tickers = exchange.fetch_tickers()

    symbols_data = []
    for symbol, data in tickers.items():
        if symbol.endswith('/USDT'):
            try:
                df = fetch_data(symbol)
                if strategy == 'momentum':
                    momentum_value = calculate_momentum(df)
                    symbols_data.append((symbol, momentum_value))
                elif strategy == 'crossover':
                    signal = moving_average_crossover(df)
                    score = 1 if signal == 'buy' else -1
                    symbols_data.append((symbol, score))
            except Exception as e:
                logger.error(f"Skipping {symbol} due to error: {e}")

    # Sort symbols based on strategy score
    symbols_data.sort(key=lambda x: x[1], reverse=True)
    top_symbols = [s[0] for s in symbols_data[:limit]]
    logger.info(f"Top {limit} symbols selected: {top_symbols}")
    return top_symbols

def buy(symbol, amount):
    price = exchange.fetch_ticker(symbol)['last']
    quantity = amount / price
    logger.info(f"Simulated buy: {symbol}, quantity: {quantity}, price: {price}")
    # Uncomment for live trading
    # return exchange.create_market_buy_order(symbol, quantity)

def sell(symbol, quantity):
    logger.info(f"Simulated sell: {symbol}, quantity: {quantity}")
    # Uncomment for live trading
    # return exchange.create_market_sell_order(symbol, quantity)

def place_sell_order(symbol, buy_price, quantity, target_profit=0.05, stop_loss=0.02):
    sell_price = buy_price * (1 + target_profit)
    stop_price = buy_price * (1 - stop_loss)

    # Example: Simulated orders
    logger.info(f"Placing limit sell order for {symbol} at {sell_price:.2f}")
    logger.info(f"Placing stop-loss order for {symbol} at {stop_price:.2f}")

    # Uncomment for live trading
    # exchange.create_limit_sell_order(symbol, quantity, sell_price)
    # exchange.create_stop_loss_order(symbol, quantity, stop_price)

def trade_logic(symbols, strategy, usdt_budget, sell_mode):
    global positions

    allocation_per_coin = usdt_budget / len(symbols)
    for symbol in symbols:
        df = fetch_data(symbol)
        if df.empty:
            continue

        if symbol in positions:
            if sell_mode == 'realtime':
                if strategy == 'momentum':
                    momentum_value = calculate_momentum(df)
                    if momentum_value < 0:
                        sell(symbol, positions[symbol]['quantity'])
                        logger.info(f"Sold {symbol} in real-time monitoring.")
                        del positions[symbol]
                elif strategy == 'crossover':
                    signal = moving_average_crossover(df)
                    if signal == 'sell':
                        sell(symbol, positions[symbol]['quantity'])
                        logger.info(f"Sold {symbol} in real-time monitoring.")
                        del positions[symbol]
        else:
            if strategy == 'momentum':
                momentum_value = calculate_momentum(df)
                if momentum_value > 0:
                    buy(symbol, allocation_per_coin)
                    buy_price = df['close'].iloc[-1]
                    quantity = allocation_per_coin / buy_price
                    positions[symbol] = {'buy_price': buy_price, 'quantity': quantity}
                    if sell_mode == 'limit':
                        place_sell_order(symbol, buy_price, quantity)
                    logger.info(f"Bought {symbol} with momentum.")
            elif strategy == 'crossover':
                signal = moving_average_crossover(df)
                if signal == 'buy':
                    buy(symbol, allocation_per_coin)
                    buy_price = df['close'].iloc[-1]
                    quantity = allocation_per_coin / buy_price
                    positions[symbol] = {'buy_price': buy_price, 'quantity': quantity}
                    if sell_mode == 'limit':
                        place_sell_order(symbol, buy_price, quantity)
                    logger.info(f"Bought {symbol} with crossover.")

def main():
    parser = argparse.ArgumentParser(description="Crypto Trading Bot")
    parser.add_argument('--strategy', choices=['momentum', 'crossover'], required=True, help="Trading strategy to use.")
    parser.add_argument('--sell-mode', choices=['realtime', 'limit'], required=True, help="Sell mode to use.")
    parser.add_argument('--usdt-budget', type=float, required=True, help="Total USDT budget for trading.")
    parser.add_argument('--top-coins', type=int, default=5, help="Number of top coins to trade.")
    args = parser.parse_args()

    strategy = args.strategy
    sell_mode = args.sell_mode
    usdt_budget = args.usdt_budget
    top_coins = args.top_coins

    symbols = fetch_symbols(limit=top_coins, strategy=strategy)
    trade_logic(symbols, strategy, usdt_budget, sell_mode)

if __name__ == "__main__":
    main()
