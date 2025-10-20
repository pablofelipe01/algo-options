"""
Actualización diaria automática de datos de opciones
Ejecutar a las 5 PM cada día (después del cierre del mercado)
"""
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import time
import logging

# Configurar logging específico para updates diarios
log_file = f"logs/daily_update_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar API key
load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')


def extract_today(ticker: str, min_dte: int = 15, max_dte: int = 60):
    """
    Extrae snapshot de opciones para HOY
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Calcular rango de vencimientos
    target_dt = pd.to_datetime(today)
    min_exp = (target_dt + timedelta(days=min_dte)).strftime("%Y-%m-%d")
    max_exp = (target_dt + timedelta(days=max_dte)).strftime("%Y-%m-%d")
    
    # Request
    url = f"https://api.polygon.io/v3/snapshot/options/{ticker}"
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
                logger.error(f"{ticker} - Error {response.status_code}")
                break
            
            data = response.json()
            
            if 'results' not in data or len(data['results']) == 0:
                break
            
            # Procesar resultados
            for result in data['results']:
                details = result.get('details', {})
                day = result.get('day', {})
                greeks = result.get('greeks', {})
                
                exp_date = pd.to_datetime(details.get('expiration_date'))
                dte = (exp_date - target_dt).days
                
                record = {
                    'date': today,
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
            logger.error(f"{ticker} página {page}: {e}")
            break
    
    df = pd.DataFrame(all_data)
    
    if len(df) > 0:
        with_data = df[df['close'].notna()]
        logger.info(f"{ticker}: {len(df)} contratos, {len(with_data)} con datos")
    
    return df


def update_all_tickers():
    """
    Actualiza todos los tickers y agrega a archivos existentes
    """
    tickers = ['SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GLD', 'SLV']
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    logger.info("="*60)
    logger.info(f"ACTUALIZACIÓN DIARIA - {today}")
    logger.info("="*60)
    
    results_summary = []
    
    for idx, ticker in enumerate(tickers, 1):
        logger.info(f"[{idx}/{len(tickers)}] Procesando {ticker}...")
        
        try:
            # Extraer datos de hoy
            today_df = extract_today(ticker)
            
            if len(today_df) == 0:
                logger.warning(f"{ticker}: Sin datos hoy")
                continue
            
            # Cargar datos existentes
            file_path = Path("data/historical") / f"{ticker}_60days.parquet"
            
            if file_path.exists():
                existing_df = pd.read_parquet(file_path)
                
                # Verificar si ya existe esta fecha
                if today in existing_df['date'].values:
                    logger.info(f"{ticker}: Fecha {today} ya existe, saltando...")
                    continue
                
                # Combinar: mantener últimos 60 días
                combined = pd.concat([existing_df, today_df], ignore_index=True)
                
                # Eliminar fechas muy antiguas (mantener últimos 90 días para buffer)
                cutoff_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
                combined = combined[combined['date'] >= cutoff_date]
                
                logger.info(f"{ticker}: Agregado. Total registros: {len(combined):,}")
            else:
                # Primer día, crear archivo
                combined = today_df
                logger.info(f"{ticker}: Archivo creado. Registros: {len(combined):,}")
            
            # Guardar
            combined.to_parquet(file_path, compression='snappy', index=False)
            
            # Resumen
            with_data = today_df[today_df['close'].notna()]
            results_summary.append({
                'ticker': ticker,
                'date': today,
                'contracts': len(today_df),
                'with_data': len(with_data),
                'volume': with_data['volume'].sum() if len(with_data) > 0 else 0
            })
            
        except Exception as e:
            logger.error(f"{ticker}: Error - {e}")
            continue
    
    # Resumen final
    logger.info("\n" + "="*60)
    logger.info("RESUMEN ACTUALIZACIÓN")
    logger.info("="*60)
    
    summary_df = pd.DataFrame(results_summary)
    if len(summary_df) > 0:
        logger.info(f"Tickers actualizados: {len(summary_df)}")
        logger.info(f"Total contratos: {summary_df['contracts'].sum():,}")
        logger.info(f"Volumen total: {summary_df['volume'].sum():,.0f}")
    
    logger.info("="*60)
    logger.info("✅ Actualización completada")


if __name__ == "__main__":
    # Verificar que no es fin de semana
    today = datetime.now()
    if today.weekday() >= 5:  # Sábado=5, Domingo=6
        logger.info(f"Hoy es {today.strftime('%A')} - Mercado cerrado, saltando actualización")
    else:
        update_all_tickers()