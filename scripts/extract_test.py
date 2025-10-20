"""
Script de extracción corta para probar
Extrae 1 ticker, 1 fecha reciente
"""
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import time

# Cargar API key
load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY')

def extract_snapshot(ticker: str, date: str, min_dte: int = 15, max_dte: int = 60):
    """
    Extrae snapshot de opciones para un ticker en una fecha
    """
    print(f"\n{'='*60}")
    print(f"EXTRACCIÓN TEST: {ticker} - {date}")
    print(f"{'='*60}")
    
    # Calcular rango de vencimientos
    target_dt = pd.to_datetime(date)
    min_exp = (target_dt + timedelta(days=min_dte)).strftime("%Y-%m-%d")
    max_exp = (target_dt + timedelta(days=max_dte)).strftime("%Y-%m-%d")
    
    print(f"Vencimientos: {min_exp} a {max_exp}")
    
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
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}")
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
        
        print(f"  Página {page}: +{len(data['results'])} contratos")
        
        # Siguiente página
        next_url = data.get('next_url')
        if not next_url:
            break
        
        # Agregar API key al next_url
        url = next_url + f"&apiKey={API_KEY}"
        params = {}
        page += 1
        time.sleep(0.12)
    
    # Crear DataFrame
    df = pd.DataFrame(all_data)
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"RESUMEN")
    print(f"{'='*60}")
    print(f"Total contratos: {len(df)}")
    print(f"Rango DTE: {df['dte'].min()}-{df['dte'].max()}")
    print(f"Vencimientos únicos: {df['expiration'].nunique()}")
    
    with_data = df[df['close'].notna()]
    print(f"Con datos: {len(with_data)} ({len(with_data)/len(df)*100:.1f}%)")
    
    if len(with_data) > 0:
        print(f"Volumen total: {with_data['volume'].sum():,.0f}")
        print(f"Precio promedio: ${with_data['close'].mean():.2f}")
    
    # Guardar
    output_dir = Path("data/historical")
    output_file = output_dir / f"test_{ticker}_{date.replace('-', '')}.parquet"
    df.to_parquet(output_file, compression='snappy', index=False)
    print(f"\n✅ Guardado: {output_file}")
    
    return df


if __name__ == "__main__":
    # Test con SPY, fecha reciente
    test_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    
    print("\n🧪 TEST DE EXTRACCIÓN")
    print(f"Ticker: SPY")
    print(f"Fecha: {test_date}")
    
    df = extract_snapshot('SPY', test_date, min_dte=15, max_dte=60)
    
    print("\n✅ TEST COMPLETADO")