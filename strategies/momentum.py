import pandas as pd

def calculate_momentum(df, period=14):
    """
    Calculate the momentum indicator for a given DataFrame.

    Momentum = Current Close Price - Close Price n periods ago
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data.
        period (int): Number of periods to calculate momentum.

    Returns:
        float: The latest momentum value.
    """
    if len(df) < period:
        return 0  # Not enough data

    df['momentum'] = df['close'] - df['close'].shift(period)
    return df['momentum'].iloc[-1]
