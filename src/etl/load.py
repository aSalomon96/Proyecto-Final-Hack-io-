import pandas as pd
import psycopg2
from psycopg2 import sql
from tqdm import tqdm
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def get_connection():
    """Establece conexión a la base de datos PostgreSQL."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def upsert_empresas(filepath):
    """Carga o actualiza la tabla empresas."""
    df = pd.read_csv(filepath)
    
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO empresas (ticker, name, sector, industry)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ticker) DO UPDATE
        SET name = EXCLUDED.name,
            sector = EXCLUDED.sector,
            industry = EXCLUDED.industry;
    """

    print("\n🏢 Cargando tabla de EMPRESAS...")
    for _, row in tqdm(df.iterrows(), total=len(df)):
        cursor.execute(insert_query, (
            row['Ticker'], row['Name'], row['Sector'], row['Industry']
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Empresas: {len(df)} registros insertados/actualizados.")

def upsert_precios_historicos(filepath):
    """Carga o actualiza precios históricos (solo los nuevos)."""
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(date) FROM precios_historicos;")
    max_date_db = cursor.fetchone()[0]

    if max_date_db is not None:
        df = df[df['Date'] > pd.to_datetime(max_date_db)]

    if df.empty:
        print("ℹ️ No hay nuevos precios históricos para cargar.")
        conn.close()
        return

    insert_query = """
        INSERT INTO precios_historicos (date, ticker, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date, ticker) DO NOTHING;
    """

    print("\n📈 Cargando tabla de PRECIOS HISTORICOS...")
    for _, row in tqdm(df.iterrows(), total=len(df)):
        cursor.execute(insert_query, (
            row['Date'], row['Ticker'], row['Open'], row['High'],
            row['Low'], row['Close'], row['Volume']
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Precios históricos: {len(df)} registros insertados.")

def upsert_fundamentales(filepath):
    """Carga o actualiza los datos fundamentales."""
    df = pd.read_csv(filepath)
    
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO indicadores_fundamentales (ticker, per, roe, eps_growth_yoy, deuda_patrimonio,
                                           margen_neto, dividend_yield, market_cap, ranking_marketcap)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (ticker) DO UPDATE SET
        per = EXCLUDED.per,
        roe = EXCLUDED.roe,
        eps_growth_yoy = EXCLUDED.eps_growth_yoy,
        deuda_patrimonio = EXCLUDED.deuda_patrimonio,
        margen_neto = EXCLUDED.margen_neto,
        dividend_yield = EXCLUDED.dividend_yield,
        market_cap = EXCLUDED.market_cap,
        ranking_marketcap = EXCLUDED.ranking_marketcap;
    """
    print("\n📊 Cargando tabla de FUNDAMENTALES...")
    for _, row in tqdm(df.iterrows(), total=len(df)):
        cursor.execute(insert_query, (
            row['Ticker'], row['PER'], row['ROE'], row['EPS Growth YoY'],
            row['Deuda/Patrimonio'], row['Margen Neto'], row['Dividend Yield'],
            row['Market Cap'], row['Ranking MarketCap']
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Fundamentales: {len(df)} registros actualizados/insertados.")

def upsert_indicadores_tecnicos(filepath):
    """Carga o actualiza indicadores técnicos (solo nuevos)."""
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(date) FROM indicadores_tecnicos;")
    max_date_db = cursor.fetchone()[0]

    if max_date_db is not None:
        df = df[df['Date'] > pd.to_datetime(max_date_db)]

    if df.empty:
        print("ℹ️ No hay nuevos indicadores técnicos para cargar.")
        conn.close()
        return

    insert_query = """
        INSERT INTO indicadores_tecnicos (date, ticker, sma_20, sma_50, ema_20, 
                                          rsi_14, macd, macd_signal, macd_hist,
                                          atr_14, obv, bb_middle, bb_upper, bb_lower, volatility_20)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date, ticker) DO NOTHING;
    """

    print("\n📉 Cargando tabla de INDICADORES TÉCNICOS...")
    for _, row in tqdm(df.iterrows(), total=len(df)):
        cursor.execute(insert_query, (
            row['Date'], row['Ticker'], row['SMA_20'], row['SMA_50'], row['EMA_20'],
            row['RSI_14'], row['MACD'], row['MACD_Signal'], row['MACD_Hist'],
            row['ATR_14'], row['OBV'], row['BB_Middle'], row['BB_Upper'],
            row['BB_Lower'], row['Volatility_20']
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Indicadores técnicos: {len(df)} registros insertados.")

if __name__ == "__main__":
    tqdm.pandas()
    
    upsert_empresas("../../data/clean_data/empresas_ready.csv")
    upsert_precios_historicos("../../data/clean_data/precios_historicos_ready.csv")
    upsert_fundamentales("../../data/clean_data/indicadores_fundamentales_ready.csv")
    upsert_indicadores_tecnicos("../../data/clean_data/indicadores_tecnicos_ready.csv")

    print("\n🎯 ¡Carga completa sin errores!\n")
