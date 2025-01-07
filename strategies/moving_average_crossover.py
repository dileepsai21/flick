# strategies/moving_average_crossover.py

import pandas as pd
import talib

def moving_average_crossover(df):
    # Ensure you're working with a copy of the DataFrame to avoid the warning
    df = df.copy()  # Explicitly make a copy to avoid SettingWithCopyWarning

    # Calculate short-term and long-term moving averages
    df.loc[:, 'sma_short'] = talib.SMA(df['close'], timeperiod=10)  # 10-period short-term moving average
    df.loc[:, 'sma_long'] = talib.SMA(df['close'], timeperiod=30)   # 30-period long-term moving average

    # Generate the trading signal based on the crossover of the moving averages
    if df['sma_short'].iloc[-1] > df['sma_long'].iloc[-1]:  # If short-term moving average is above long-term
        return 'buy'
    elif df['sma_short'].iloc[-1] < df['sma_long'].iloc[-1]:  # If short-term moving average is below long-term
        return 'sell'
    else:
        return 'hold'  # If they are the same, hold the position
