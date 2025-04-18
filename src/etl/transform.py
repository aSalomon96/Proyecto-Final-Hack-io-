import pandas as pd
import os
from tqdm import tqdm
from datetime import datetime
import numpy as np

# Directorios
DIR_RAW = "../../data/raw_data/"
DIR_READY = "../../data/clean_data/"
os.makedirs(DIR_READY, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def transformar_empresas(input_file, output_file):
    """Transforma el archivo de empresas, dejando columnas relevantes."""
    log("Transformando datos de empresas...")
    df = pd.read_csv(input_file)

    columnas_finales = ["Ticker", "Name", "Sector", "Industry"]
    df = df[columnas_finales]

    df.to_csv(output_file, index=False)
    log(f"Empresas listas guardadas en: {output_file}")

def transformar_precios_historicos(input_file, output_file):
    """Transforma precios históricos: corrige columnas y formatos."""
    log("Transformando precios historicos (formato tidy)...")
    df = pd.read_csv(input_file)

    df = df.rename(columns={
        "date": "Date",
        "ticker": "Ticker",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume"
    })

    df = df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df['Date'] = pd.to_datetime(df['Date'])
    df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].round(3)

    df.to_csv(output_file, index=False)
    log(f"Precios historicos listos guardados en: {output_file}")

def transformar_indicadores_fundamentales(input_file, output_file):
    """Transforma indicadores fundamentales, agrega ranking de market cap."""
    log("Transformando indicadores fundamentales...")
    df = pd.read_csv(input_file)

    columnas_finales = [
        "Ticker", "Name", "PER", "ROE", "EPS Growth YoY",
        "Deuda/Patrimonio", "Margen Neto", "Dividend Yield", "Market Cap"
    ]

    df = df[columnas_finales]
    df["Ranking MarketCap"] = df["Market Cap"].rank(ascending=False, method='first').astype(int)

    df.to_csv(output_file, index=False)
    log(f"Indicadores fundamentales listos guardados en: {output_file}")

def calcular_rsi(close, window=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_macd(close, short=12, long=26, signal=9):
    ema_short = close.ewm(span=short, adjust=False).mean()
    ema_long = close.ewm(span=long, adjust=False).mean()
    macd = ema_short - ema_long
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def calcular_atr(high, low, close, window=14):
    high_low = high - low
    high_close = (high - close.shift()).abs()
    low_close = (low - close.shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=window).mean()
    return atr

def calcular_obv(close, volume):
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv

def calcular_indicadores_tecnicos(input_file, output_file):
    """Calcula todos los indicadores técnicos sobre precios históricos."""
    log("Calculando indicadores técnicos...")
    df = pd.read_csv(input_file)

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by=['Ticker', 'Date'])

    indicadores = []

    for ticker, group in tqdm(df.groupby('Ticker')):
        group = group.copy()
        group['SMA_20'] = group['Close'].rolling(window=20).mean()
        group['SMA_50'] = group['Close'].rolling(window=50).mean()
        group['EMA_20'] = group['Close'].ewm(span=20, adjust=False).mean()

        group['RSI_14'] = calcular_rsi(group['Close'])
        group['MACD'], group['MACD_Signal'], group['MACD_Hist'] = calcular_macd(group['Close'])

        group['ATR_14'] = calcular_atr(group['High'], group['Low'], group['Close'])
        group['OBV'] = calcular_obv(group['Close'], group['Volume'])

        group['BB_Middle'] = group['Close'].rolling(window=20).mean()
        group['BB_Upper'] = group['BB_Middle'] + 2 * group['Close'].rolling(window=20).std()
        group['BB_Lower'] = group['BB_Middle'] - 2 * group['Close'].rolling(window=20).std()

        group['Volatility_20'] = group['Close'].rolling(window=20).std()

        indicadores.append(group[['Date', 'Ticker', 'SMA_20', 'SMA_50', 'EMA_20',
                                  'RSI_14', 'MACD', 'MACD_Signal', 'MACD_Hist',
                                  'ATR_14', 'OBV', 'BB_Middle', 'BB_Upper', 'BB_Lower',
                                  'Volatility_20']])

    df_indicadores = pd.concat(indicadores)
    df_indicadores.to_csv(output_file, index=False)
    log(f"Indicadores técnicos listos guardados en: {output_file}")

if __name__ == "__main__":
    tqdm.pandas()

    transformar_empresas(
        input_file=DIR_RAW + "top_500_marketcap.csv",
        output_file=DIR_READY + "empresas_ready.csv"
    )

    transformar_precios_historicos(
        input_file=DIR_RAW + "nyse_top500_data.csv",
        output_file=DIR_READY + "precios_historicos_ready.csv"
    )

    transformar_indicadores_fundamentales(
        input_file=DIR_RAW + "nyse_top_500_fundamentals_indicators.csv",
        output_file=DIR_READY + "indicadores_fundamentales_ready.csv"
    )

    calcular_indicadores_tecnicos(
        input_file=DIR_READY + "precios_historicos_ready.csv",
        output_file=DIR_READY + "indicadores_tecnicos_ready.csv"
    )
