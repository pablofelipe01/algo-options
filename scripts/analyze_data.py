"""
Análisis básico de datos de opciones
Muestra insights clave para trading y backtesting
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def load_ticker_data(ticker: str):
    """Cargar datos de un ticker"""
    file_path = Path("data/historical") / f"{ticker}_60days.parquet"
    if file_path.exists():
        return pd.read_parquet(file_path)
    return None

def analyze_liquidity(df: pd.DataFrame, ticker: str):
    """Análisis de liquidez"""
    print(f"\n{'='*60}")
    print(f"💧 ANÁLISIS DE LIQUIDEZ - {ticker}")
    print(f"{'='*60}")
    
    with_data = df[df['close'].notna()]
    
    if len(with_data) == 0:
        print("Sin datos para analizar")
        return
    
    # Métricas generales
    print(f"\n📊 Métricas Generales:")
    print(f"  Total contratos: {len(df):,}")
    print(f"  Con datos: {len(with_data):,} ({len(with_data)/len(df)*100:.1f}%)")
    print(f"  Volumen total: {with_data['volume'].sum():,.0f}")
    print(f"  Volumen promedio: {with_data['volume'].mean():,.0f}")
    print(f"  OI promedio: {with_data['oi'].mean():,.0f}")
    
    # Top 5 más líquidos
    print(f"\n🔥 TOP 5 MÁS LÍQUIDOS:")
    top5 = with_data.nlargest(5, 'volume')
    for idx, row in top5.iterrows():
        print(f"  {row['ticker']:25s} | Strike ${row['strike']:6.0f} | "
              f"Vol: {row['volume']:8,.0f} | DTE: {row['dte']:2.0f}")
    
    # Liquidez por DTE
    print(f"\n⏰ VOLUMEN POR DTE:")
    dte_vol = with_data.groupby('dte')['volume'].sum().sort_index()
    for dte, vol in dte_vol.head(10).items():
        print(f"  DTE {dte:3.0f}: {vol:12,.0f}")

def analyze_greeks(df: pd.DataFrame, ticker: str):
    """Análisis de griegas"""
    print(f"\n{'='*60}")
    print(f"🎯 ANÁLISIS DE GRIEGAS - {ticker}")
    print(f"{'='*60}")
    
    with_greeks = df[df['delta'].notna()]
    
    if len(with_greeks) == 0:
        print("Sin griegas para analizar")
        return
    
    # Estadísticas de griegas
    print(f"\n📈 Estadísticas:")
    for greek in ['delta', 'gamma', 'theta', 'vega', 'iv']:
        data = with_greeks[greek].dropna()
        if len(data) > 0:
            print(f"  {greek.upper():8s}: min={data.min():7.4f} | "
                  f"max={data.max():7.4f} | mean={data.mean():7.4f} | "
                  f"std={data.std():7.4f}")
    
    # Delta por tipo
    print(f"\n📊 DELTA PROMEDIO POR TIPO:")
    delta_by_type = with_greeks.groupby('type')['delta'].agg(['mean', 'std'])
    print(delta_by_type)
    
    # IV por moneyness (últimos datos)
    latest_date = df['date'].max()
    latest = df[df['date'] == latest_date].copy()
    latest['moneyness'] = latest['strike'] / latest['strike'].median()
    
    print(f"\n💰 IV POR MONEYNESS (última fecha: {latest_date}):")
    bins = [0.9, 0.95, 1.0, 1.05, 1.1]
    labels = ['Deep OTM', 'OTM', 'ATM', 'ITM']
    latest['money_bucket'] = pd.cut(latest['moneyness'], bins=bins, labels=labels)
    iv_by_money = latest.groupby('money_bucket')['iv'].mean() * 100
    for bucket, iv in iv_by_money.items():
        print(f"  {bucket:10s}: {iv:5.1f}%")

def analyze_iv_evolution(df: pd.DataFrame, ticker: str):
    """Análisis de evolución de IV"""
    print(f"\n{'='*60}")
    print(f"📉 EVOLUCIÓN DE IV - {ticker}")
    print(f"{'='*60}")
    
    # IV promedio por fecha
    iv_daily = df.groupby('date')['iv'].mean() * 100
    
    print(f"\n📅 IV Promedio por Fecha:")
    for date, iv in iv_daily.items():
        print(f"  {date}: {iv:5.1f}%")
    
    # Tendencia
    if len(iv_daily) > 1:
        change = iv_daily.iloc[-1] - iv_daily.iloc[0]
        pct_change = (change / iv_daily.iloc[0]) * 100
        trend = "📈 Subiendo" if change > 0 else "📉 Bajando"
        print(f"\n🔍 Tendencia: {trend}")
        print(f"  Cambio: {change:+.1f}% ({pct_change:+.1f}%)")

def analyze_put_call_ratio(df: pd.DataFrame, ticker: str):
    """Análisis de Put/Call Ratio"""
    print(f"\n{'='*60}")
    print(f"📊 PUT/CALL RATIO - {ticker}")
    print(f"{'='*60}")
    
    with_volume = df[df['volume'].notna()]
    
    # Por fecha
    pc_by_date = with_volume.groupby(['date', 'type'])['volume'].sum().unstack(fill_value=0)
    if 'call' in pc_by_date.columns and 'put' in pc_by_date.columns:
        pc_by_date['PC_Ratio'] = pc_by_date['put'] / pc_by_date['call']
        
        print(f"\n📅 Por Fecha:")
        print(pc_by_date[['call', 'put', 'PC_Ratio']].round(2))
        
        # Tendencia
        if len(pc_by_date) > 1:
            avg_ratio = pc_by_date['PC_Ratio'].mean()
            latest_ratio = pc_by_date['PC_Ratio'].iloc[-1]
            print(f"\n🔍 Interpretación:")
            print(f"  Ratio promedio: {avg_ratio:.2f}")
            print(f"  Ratio actual: {latest_ratio:.2f}")
            if latest_ratio > 1.5:
                print(f"  ⚠️  Sesgo BEARISH (mucha compra de puts)")
            elif latest_ratio < 0.7:
                print(f"  ⚠️  Sesgo BULLISH (mucha compra de calls)")
            else:
                print(f"  ✅ Relativamente balanceado")

def analyze_atm_options(df: pd.DataFrame, ticker: str):
    """Análisis de opciones ATM"""
    print(f"\n{'='*60}")
    print(f"🎯 OPCIONES ATM (At-The-Money) - {ticker}")
    print(f"{'='*60}")
    
    # Últimos datos
    latest_date = df['date'].max()
    latest = df[df['date'] == latest_date].copy()
    
    # Calcular moneyness
    median_strike = latest['strike'].median()
    latest['moneyness'] = latest['strike'] / median_strike
    
    # ATM = ±2% del strike medio
    atm = latest[(latest['moneyness'] >= 0.98) & (latest['moneyness'] <= 1.02)]
    atm_data = atm[atm['close'].notna()]
    
    print(f"\n💰 Strike medio: ${median_strike:.0f}")
    print(f"📊 Contratos ATM: {len(atm)}")
    print(f"📈 Con datos: {len(atm_data)}")
    
    if len(atm_data) > 0:
        print(f"\n🔥 Top 5 ATM por volumen:")
        top_atm = atm_data.nlargest(5, 'volume')
        for idx, row in top_atm.iterrows():
            print(f"  {row['type']:4s} ${row['strike']:6.0f} | "
                  f"Vol: {row['volume']:8,.0f} | "
                  f"IV: {row['iv']*100:5.1f}% | "
                  f"Delta: {row['delta']:6.3f}")

def full_analysis(ticker: str):
    """Análisis completo de un ticker"""
    print(f"\n{'█'*60}")
    print(f"█  ANÁLISIS COMPLETO: {ticker}")
    print(f"{'█'*60}")
    
    df = load_ticker_data(ticker)
    
    if df is None:
        print(f"\n❌ No se encontraron datos para {ticker}")
        return
    
    analyze_liquidity(df, ticker)
    analyze_greeks(df, ticker)
    analyze_iv_evolution(df, ticker)
    analyze_put_call_ratio(df, ticker)
    analyze_atm_options(df, ticker)

def multi_ticker_comparison():
    """Comparación entre múltiples tickers"""
    print(f"\n{'='*60}")
    print(f"📊 COMPARACIÓN MULTI-TICKER")
    print(f"{'='*60}")
    
    tickers = ['SPY', 'QQQ', 'AAPL', 'NVDA', 'GLD']
    summary = []
    
    for ticker in tickers:
        df = load_ticker_data(ticker)
        if df is None:
            continue
        
        with_data = df[df['close'].notna()]
        
        if len(with_data) > 0:
            summary.append({
                'Ticker': ticker,
                'Contratos': len(df),
                'Volumen_Total': with_data['volume'].sum(),
                'Vol_Promedio': with_data['volume'].mean(),
                'IV_Promedio': with_data['iv'].mean() * 100,
                'OI_Promedio': with_data['oi'].mean(),
            })
    
    comp_df = pd.DataFrame(summary)
    
    print(f"\n📊 Tabla Comparativa:")
    print(comp_df.to_string(index=False))
    
    print(f"\n🏆 Rankings:")
    print(f"  Mayor volumen: {comp_df.nlargest(1, 'Volumen_Total')['Ticker'].values[0]}")
    print(f"  Mayor IV: {comp_df.nlargest(1, 'IV_Promedio')['Ticker'].values[0]}")
    print(f"  Mayor OI: {comp_df.nlargest(1, 'OI_Promedio')['Ticker'].values[0]}")

def main():
    """Menú principal"""
    print("\n" + "="*60)
    print("  ANÁLISIS DE DATOS DE OPCIONES")
    print("="*60)
    
    while True:
        print("\n📋 OPCIONES:")
        print("  1. Análisis completo de un ticker")
        print("  2. Comparación multi-ticker")
        print("  3. Análisis rápido SPY")
        print("  4. Análisis rápido QQQ")
        print("  5. Salir")
        
        choice = input("\nSelecciona una opción (1-5): ").strip()
        
        if choice == '1':
            ticker = input("Ingresa el ticker (ej: SPY): ").strip().upper()
            full_analysis(ticker)
        elif choice == '2':
            multi_ticker_comparison()
        elif choice == '3':
            full_analysis('SPY')
        elif choice == '4':
            full_analysis('QQQ')
        elif choice == '5':
            print("\n✅ Hasta luego!")
            break
        else:
            print("\n❌ Opción inválida")

if __name__ == "__main__":
    main()