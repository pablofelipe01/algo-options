"""
Extracción histórica: últimos 60 días, múltiples tickers
10 tickers × ~9 fechas = ~90 extracciones
Tiempo estimado: 15-20 minutos
"""
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar API key
load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')


def extract_snapshot(ticker: str, date: str, min_dte: int = 15, max_dte: int = 60):
    """
    Extrae snapshot de opciones para un ticker en una fecha
    """
    # Calcular rango de vencimientos
    target_dt = pd.to_datetime(date)
    min_exp = (target_dt + timedelta(days=min_dte)).strftime("%Y-%m-%d")
    max_exp = (target_dt + timedelta(days=max_dte)).strftime("%Y-%m-%d")
    
    # Request inicial
    url = "https://api.polygon.io/v3/snapshot/options/" + ticker
    params = {
        'apiKey': API_KEY,
        'expiration_date.gte': min_exp,
        'expiration_date.lte': max_exp,
        'limit': 250
    }
    
    all_data = []
    page = 1
    
    while True:
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"{ticker} {date} - Error {response.status_code}")
                break
            
            data = response.json()
            
            if 'results' not in data or len(data['results']) == 0:
                break
            
            # Procesar resultados
            for result in data['results']:
                details = result.get('details', {})
                day = result.get('day', {})
                greeks = result.get('greeks', {})
                
                # Calcular DTE
                exp_date = pd.to_datetime(details.get('expiration_date'))
                dte = (exp_date - target_dt).days
                
                record = {
                    'date': date,
                    'ticker': details.get('ticker'),
                    'underlying': ticker,
                    'type': details.get('contract_type'),
                    'strike': details.get('strike_price'),
                    'expiration': details.get('expiration_date'),
                    'dte': dte,
                    'open': day.get('open'),
                    'high': day.get('high'),
                    'low': day.get('low'),
                    'close': day.get('close'),
                    'volume': day.get('volume'),
                    'vwap': day.get('vwap'),
                    'delta': greeks.get('delta'),
                    'gamma': greeks.get('gamma'),
                    'theta': greeks.get('theta'),
                    'vega': greeks.get('vega'),
                    'iv': result.get('implied_volatility'),
                    'oi': result.get('open_interest'),
                }
                all_data.append(record)
            
            # Siguiente página
            next_url = data.get('next_url')
            if not next_url:
                break
            
            url = next_url + f"&apiKey={API_KEY}"
            params = {}
            page += 1
            time.sleep(0.12)
            
        except Exception as e:
            logger.error(f"{ticker} {date} página {page} - Error: {e}")
            break
    
    df = pd.DataFrame(all_data)
    
    if len(df) > 0:
        with_data = df[df['close'].notna()]
        logger.info(f"{ticker} {date}: {len(df)} contratos, "
                   f"{len(with_data)} con datos ({len(with_data)/len(df)*100:.1f}%)")
    
    return df


def extract_historical(tickers: list, start_date: str, end_date: str):
    """
    Extracción histórica completa
    """
    logger.info("="*60)
    logger.info("INICIO EXTRACCIÓN HISTÓRICA")
    logger.info("="*60)
    logger.info(f"Tickers: {', '.join(tickers)}")
    logger.info(f"Período: {start_date} a {end_date}")
    logger.info("="*60)
    
    # Generar fechas (viernes semanales)
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    date_range = pd.date_range(start=start, end=end, freq='W-FRI')
    
    logger.info(f"Fechas a procesar: {len(date_range)}")
    logger.info(f"Total extracciones: {len(tickers) * len(date_range)}")
    
    # Procesar cada ticker
    for ticker_idx, ticker in enumerate(tickers, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"[{ticker_idx}/{len(tickers)}] PROCESANDO: {ticker}")
        logger.info(f"{'='*60}")
        
        ticker_data = []
        
        for date_idx, sample_date in enumerate(date_range, 1):
            date_str = sample_date.strftime("%Y-%m-%d")
            
            logger.info(f"[{date_idx}/{len(date_range)}] {ticker} - {date_str}")
            
            try:
                df = extract_snapshot(ticker, date_str, min_dte=15, max_dte=60)
                
                if len(df) > 0:
                    ticker_data.append(df)
                    
            except Exception as e:
                logger.error(f"Error en {ticker} {date_str}: {e}")
                continue
        
        # Consolidar y guardar
        if ticker_data:
            combined = pd.concat(ticker_data, ignore_index=True)
            
            output_file = Path("data/historical") / f"{ticker}_60days.parquet"
            combined.to_parquet(output_file, compression='snappy', index=False)
            
            logger.info(f"\n✅ {ticker} COMPLETADO")
            logger.info(f"   Total registros: {len(combined):,}")
            logger.info(f"   Fechas: {combined['date'].nunique()}")
            logger.info(f"   Archivo: {output_file}")
        else:
            logger.warning(f"⚠️ {ticker} - Sin datos")
    
    logger.info(f"\n{'='*60}")
    logger.info("EXTRACCIÓN COMPLETADA")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    # CONFIGURACIÓN
    tickers = [
        # Índices (3)
        'SPY', 'QQQ', 'IWM',
        # Liquid Stocks (5)
        'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN',
        # Commodities (2)
        'GLD', 'SLV'
    ]
    
    # Últimos 60 días
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    
    print("\n" + "="*60)
    print("EXTRACCIÓN HISTÓRICA - 60 DÍAS")
    print("="*60)
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Total: {len(tickers)} tickers")
    print(f"Período: {start_date} a {end_date}")
    print(f"Frecuencia: Semanal (viernes)")
    print(f"DTE: 15-60 días")
    print("="*60)
    print("\n⏱️  Tiempo estimado: 15-20 minutos")
    print("💾 Storage estimado: ~50 MB")
    print("\n")
    
    respuesta = input("¿Iniciar extracción? (y/n): ")
    
    if respuesta.lower() == 'y':
        start_time = datetime.now()
        
        extract_historical(tickers, start_date, end_date)
        
        elapsed = datetime.now() - start_time
        print(f"\n⏱️  Tiempo total: {elapsed}")
        print("\n✅ Proceso completado")
    else:
        print("\n❌ Extracción cancelada")