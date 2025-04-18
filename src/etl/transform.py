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
    log("Transformando datos de empresas...")
    df = pd.read_csv(input_file)

    columnas_finales = ["Ticker", "Name", "Sector", "Industry"]
    df = df[columnas_finales]

    df.to_csv(output_file, index=False)
    log(f"Empresas listas guardadas en: {output_file}")

def transformar_precios_historicos(input_file, output_file):
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

def calcular_resumen_inversion(
    precios_tecnicos_file=DIR_READY + "indicadores_tecnicos_ready.csv",
    fundamentales_file=DIR_READY + "indicadores_fundamentales_ready.csv",
    precios_historicos_file=DIR_READY + "precios_historicos_ready.csv",
    output_file=DIR_READY + "resumen_inversion_ready.csv"
):
    log("Calculando resumen de inversión...")

    # Cargar datasets
    df_tecnicos = pd.read_csv(precios_tecnicos_file)
    df_fundamentales = pd.read_csv(fundamentales_file)
    df_precios = pd.read_csv(precios_historicos_file)

    # Tomar último registro por ticker
    df_ultimos_tecnicos = df_tecnicos.sort_values('Date').groupby('Ticker').tail(1)
    df_ultimos_precios = df_precios.sort_values('Date').groupby('Ticker').tail(1)[['Ticker', 'Close']]

    # Merge
    df = pd.merge(df_ultimos_tecnicos, df_fundamentales, on='Ticker', how='inner')
    df = pd.merge(df, df_ultimos_precios, on='Ticker', how='left')

    resultados = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        ticker = row['Ticker']

        ### Análisis Técnico ###
        señales_tec = {}
        
        # SMA vs EMA
        if pd.notna(row['SMA_20']) and pd.notna(row['EMA_20']):
            señales_tec['SMA_vs_EMA'] = 'COMPRAR' if row['SMA_20'] > row['EMA_20'] else 'VENDER'

        # MACD
        if pd.notna(row['MACD']) and pd.notna(row['MACD_Signal']):
            señales_tec['MACD'] = 'COMPRAR' if row['MACD'] > row['MACD_Signal'] else 'VENDER'

        # RSI
        if pd.notna(row['RSI_14']):
            if row['RSI_14'] < 30:
                señales_tec['RSI'] = 'COMPRAR'
            elif row['RSI_14'] > 70:
                señales_tec['RSI'] = 'VENDER'
            else:
                señales_tec['RSI'] = 'MANTENER'

        ### Análisis Fundamental ###
        señales_fund = {}

        # PER
        if pd.notna(row['PER']):
            if row['PER'] < 20:
                señales_fund['PER'] = 'COMPRAR'
            elif row['PER'] > 30:
                señales_fund['PER'] = 'VENDER'
            else:
                señales_fund['PER'] = 'MANTENER'

        # ROE
        if pd.notna(row['ROE']):
            if row['ROE'] > 0.15:
                señales_fund['ROE'] = 'COMPRAR'
            elif row['ROE'] < 0.05:
                señales_fund['ROE'] = 'VENDER'
            else:
                señales_fund['ROE'] = 'MANTENER'

        # EPS Growth YoY
        if pd.notna(row['EPS Growth YoY']):
            if row['EPS Growth YoY'] > 0.10:
                señales_fund['EPS Growth YoY'] = 'COMPRAR'
            elif row['EPS Growth YoY'] < 0:
                señales_fund['EPS Growth YoY'] = 'VENDER'
            else:
                señales_fund['EPS Growth YoY'] = 'MANTENER'

        # Deuda/Patrimonio
        if pd.notna(row['Deuda/Patrimonio']):
            if row['Deuda/Patrimonio'] < 100:
                señales_fund['Deuda/Patrimonio'] = 'COMPRAR'
            elif row['Deuda/Patrimonio'] > 200:
                señales_fund['Deuda/Patrimonio'] = 'VENDER'
            else:
                señales_fund['Deuda/Patrimonio'] = 'MANTENER'

        ### Estado de Bollinger Bands (solo informativo)
        estado_bb = np.nan
        if pd.notna(row['BB_Upper']) and pd.notna(row['BB_Lower']) and pd.notna(row['Close']):
            if row['Close'] > row['BB_Upper']:
                estado_bb = "Sobrecompra"
            elif row['Close'] < row['BB_Lower']:
                estado_bb = "Sobreventa"
            else:
                estado_bb = "Normal"

        ### Cálculo Porcentajes ###
        tec_buy = list(señales_tec.values()).count('COMPRAR')
        tec_total = len(señales_tec)

        fund_buy = list(señales_fund.values()).count('COMPRAR')
        fund_total = len(señales_fund)

        pct_tecnico_buy = round(tec_buy / tec_total * 100, 2) if tec_total > 0 else np.nan
        pct_fundamental_buy = round(fund_buy / fund_total * 100, 2) if fund_total > 0 else np.nan

        ### Decisión Final ###
        if pct_tecnico_buy >= 66 and pct_fundamental_buy >= 66:
            decision = "COMPRAR"
        elif pct_tecnico_buy <= 33 and pct_fundamental_buy <= 33:
            decision = "VENDER"
        else:
            decision = "MANTENER"

        ### Resultado ###
        resultados.append({
            "Ticker": ticker,
            "%_Tecnico_Buy": pct_tecnico_buy,
            "%_Fundamental_Buy": pct_fundamental_buy,
            "Decision_Final": decision,
            "Estado_BollingerBands": estado_bb,
            "SMA_vs_EMA": señales_tec.get('SMA_vs_EMA', np.nan),
            "MACD": señales_tec.get('MACD', np.nan),
            "RSI": señales_tec.get('RSI', np.nan),
            "PER": señales_fund.get('PER', np.nan),
            "ROE": señales_fund.get('ROE', np.nan),
            "EPS Growth YoY": señales_fund.get('EPS Growth YoY', np.nan),
            "Deuda/Patrimonio": señales_fund.get('Deuda/Patrimonio', np.nan)
        })

    # Guardar CSV
    df_resultado = pd.DataFrame(resultados)
    df_resultado.to_csv(output_file, index=False)

    log(f"✅ Resumen de inversión listo: {output_file}")


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

    calcular_resumen_inversion()

