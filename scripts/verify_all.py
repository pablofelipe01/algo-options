"""
Verificación final de la extracción histórica (60 días)
"""
import pandas as pd
from pathlib import Path

def verify_all():
    """
    Verifica todos los archivos extraídos
    """
    print("\n" + "="*60)
    print("VERIFICACIÓN FINAL - EXTRACCIÓN 60 DÍAS")
    print("="*60)
    
    # Buscar todos los archivos
    files = list(Path("data/historical").glob("*_60days.parquet"))
    
    if not files:
        print("\n❌ No se encontraron archivos")
        return
    
    print(f"\nArchivos encontrados: {len(files)}\n")
    
    # Analizar cada ticker
    summary = []
    total_records = 0
    
    for file in sorted(files):
        ticker = file.stem.replace('_60days', '')
        df = pd.read_parquet(file)
        
        with_data = df[df['close'].notna()]
        
        stats = {
            'Ticker': ticker,
            'Registros': len(df),
            'Con_Datos': len(with_data),
            'Pct_Datos': len(with_data) / len(df) * 100 if len(df) > 0 else 0,
            'Fechas': df['date'].nunique(),
            'Vencimientos': df['expiration'].nunique(),
            'DTE_Min': df['dte'].min() if len(df) > 0 else 0,
            'DTE_Max': df['dte'].max() if len(df) > 0 else 0,
            'Volumen_Total': with_data['volume'].sum() if len(with_data) > 0 else 0,
            'Precio_Prom': with_data['close'].mean() if len(with_data) > 0 else 0,
            'IV_Prom': with_data['iv'].mean() * 100 if len(with_data) > 0 else 0,
            'Size_MB': file.stat().st_size / (1024**2)
        }
        
        summary.append(stats)
        total_records += len(df)
        
        # Mostrar por ticker
        print(f"✅ {ticker:6s} | "
              f"{len(df):7,} registros | "
              f"{stats['Fechas']:3} fechas | "
              f"{stats['Pct_Datos']:5.1f}% datos | "
              f"{stats['Size_MB']:6.1f} MB")
    
    # Resumen consolidado
    df_summary = pd.DataFrame(summary)
    
    print("\n" + "="*60)
    print("RESUMEN POR CATEGORÍA")
    print("="*60)
    
    # Índices
    indices = df_summary[df_summary['Ticker'].isin(['SPY', 'QQQ', 'IWM'])]
    if len(indices) > 0:
        print(f"\n📊 ÍNDICES:")
        print(f"  Total registros: {indices['Registros'].sum():,}")
        print(f"  Promedio completitud: {indices['Pct_Datos'].mean():.1f}%")
        print(f"  Volumen total: {indices['Volumen_Total'].sum():,.0f}")
    
    # Stocks
    stocks = df_summary[df_summary['Ticker'].isin(['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN'])]
    if len(stocks) > 0:
        print(f"\n📈 STOCKS:")
        print(f"  Total registros: {stocks['Registros'].sum():,}")
        print(f"  Promedio completitud: {stocks['Pct_Datos'].mean():.1f}%")
        print(f"  Volumen total: {stocks['Volumen_Total'].sum():,.0f}")
    
    # Commodities
    commodities = df_summary[df_summary['Ticker'].isin(['GLD', 'SLV'])]
    if len(commodities) > 0:
        print(f"\n🥇 COMMODITIES:")
        print(f"  Total registros: {commodities['Registros'].sum():,}")
        print(f"  Promedio completitud: {commodities['Pct_Datos'].mean():.1f}%")
        print(f"  Volumen total: {commodities['Volumen_Total'].sum():,.0f}")
    
    # Totales
    print("\n" + "="*60)
    print("TOTALES GENERALES")
    print("="*60)
    print(f"Total registros: {total_records:,}")
    print(f"Total fechas (promedio): {df_summary['Fechas'].mean():.0f}")
    print(f"Completitud promedio: {df_summary['Pct_Datos'].mean():.1f}%")
    print(f"Volumen total: {df_summary['Volumen_Total'].sum():,.0f}")
    print(f"Storage total: {df_summary['Size_MB'].sum():.1f} MB")
    print(f"IV promedio: {df_summary['IV_Prom'].mean():.1f}%")
    
    # Top 5 por volumen
    print("\n🔥 TOP 5 POR VOLUMEN:")
    top5 = df_summary.nlargest(5, 'Volumen_Total')
    for idx, row in top5.iterrows():
        print(f"  {row['Ticker']:6s}: {row['Volumen_Total']:15,.0f}")
    
    # Verificar integridad
    print("\n" + "="*60)
    print("VERIFICACIÓN DE INTEGRIDAD")
    print("="*60)
    
    issues = []
    
    for idx, row in df_summary.iterrows():
        if row['Fechas'] < 5:
            issues.append(f"{row['Ticker']}: Solo {row['Fechas']} fechas (esperadas ~9)")
        if row['Pct_Datos'] < 70:
            issues.append(f"{row['Ticker']}: Solo {row['Pct_Datos']:.1f}% con datos")
    
    if issues:
        print("⚠️  ADVERTENCIAS:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ TODO PERFECTO - Todos los datos son válidos")
    
    print("\n" + "="*60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("="*60 + "\n")
    
    # Guardar resumen
    summary_file = Path("data/historical/SUMMARY.csv")
    df_summary.to_csv(summary_file, index=False)
    print(f"📄 Resumen guardado: {summary_file}\n")


if __name__ == "__main__":
    verify_all()