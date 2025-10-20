#!/usr/bin/env python3
# scripts/demo_quantitative.py
"""
Demostración del Módulo Cuantitativo con Datos Reales
======================================================

Este script demuestra el uso completo del módulo cuantitativo:
1. Carga datos reales de opciones desde archivos parquet
2. Calcula precios teóricos con Black-Scholes
3. Compara griegas de Polygon vs BSM
4. Calcula Probabilidad de Beneficio (PoP)
5. Identifica opciones mal valoradas
6. Genera reportes y visualizaciones

Uso:
    python demo_quantitative.py
    python demo_quantitative.py --ticker SPY
    python demo_quantitative.py --ticker QQQ --dte 45
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from datetime import datetime

# Importar nuestro módulo cuantitativo
from quantitative import (
    black_scholes_price,
    calculate_greeks,
    days_to_years,
    get_risk_free_rate,
    compare_greeks,
    analyze_option_mispricing
)


def load_options_data(ticker: str = "SPY") -> pd.DataFrame:
    """
    Carga datos de opciones desde archivo parquet.
    
    Parámetros:
    -----------
    ticker : str
        Ticker del activo (SPY, QQQ, etc.)
    
    Retorna:
    --------
    pd.DataFrame
        Datos de opciones
    """
    data_dir = Path(__file__).parent.parent / "data" / "historical"
    file_path = data_dir / f"{ticker}_60days.parquet"
    
    if not file_path.exists():
        raise FileNotFoundError(f"No se encuentra: {file_path}")
    
    print(f"📂 Cargando datos: {file_path}")
    df = pd.read_parquet(file_path)
    print(f"   ✓ {len(df):,} contratos cargados")
    
    # Inferir precio del subyacente desde opciones ATM
    df = infer_underlying_price(df)
    
    return df


def infer_underlying_price(df: pd.DataFrame) -> pd.DataFrame:
    """
    Infiere el precio del subyacente desde opciones ATM.
    
    Estrategia:
    1. Buscar calls con delta cercano a 0.5 (ATM)
    2. El strike de esas calls es aproximadamente el precio del subyacente
    3. Alternativamente, usar strike + precio de call ATM
    
    Parámetros:
    -----------
    df : pd.DataFrame
        Datos de opciones
    
    Retorna:
    --------
    pd.DataFrame
        Datos con columna 'underlying_price' agregada
    """
    print(f"   📊 Infiriendo precio del subyacente...")
    
    # Agrupar por fecha para calcular precio subyacente por día
    df['underlying_price'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        date_df = df[date_mask]
        
        # Método 1: Buscar calls ATM (delta cercano a 0.5)
        calls_atm = date_df[
            (date_df['type'] == 'call') & 
            (date_df['delta'].notna()) &
            (date_df['delta'] > 0.45) & 
            (date_df['delta'] < 0.55)
        ]
        
        if len(calls_atm) > 0:
            # Usar el strike promedio de las calls ATM como proxy del precio
            underlying_price = calls_atm['strike'].median()
        else:
            # Método 2: Usar puts ATM (delta cercano a -0.5)
            puts_atm = date_df[
                (date_df['type'] == 'put') & 
                (date_df['delta'].notna()) &
                (date_df['delta'] > -0.55) & 
                (date_df['delta'] < -0.45)
            ]
            
            if len(puts_atm) > 0:
                underlying_price = puts_atm['strike'].median()
            else:
                # Método 3: Usar el punto medio del rango de strikes
                underlying_price = date_df['strike'].median()
        
        df.loc[date_mask, 'underlying_price'] = underlying_price
    
    # Imprimir estadísticas
    unique_prices = df.groupby('date')['underlying_price'].first()
    print(f"   ✓ Precio subyacente inferido:")
    print(f"      Rango: ${unique_prices.min():.2f} - ${unique_prices.max():.2f}")
    print(f"      Promedio: ${unique_prices.mean():.2f}")
    
    return df


def filter_liquid_options(df: pd.DataFrame, min_volume: int = 10, min_oi: int = 50) -> pd.DataFrame:
    """
    Filtra opciones líquidas para análisis confiable.
    
    Parámetros:
    -----------
    df : pd.DataFrame
        Datos de opciones
    min_volume : int
        Volumen mínimo
    min_oi : int
        Open Interest mínimo
    
    Retorna:
    --------
    pd.DataFrame
        Opciones líquidas
    """
    liquid = df[
        (df['volume'] >= min_volume) &
        (df['oi'] >= min_oi) &
        (df['delta'].notna()) &
        (df['iv'].notna()) &
        (df['iv'] > 0) &
        (df['underlying_price'].notna())
    ].copy()
    
    print(f"   ✓ Opciones líquidas: {len(liquid):,} ({len(liquid)/len(df)*100:.1f}%)")
    
    return liquid


def calculate_bsm_for_option(row: pd.Series, r: float) -> dict:
    """
    Calcula precio BSM y griegas para una opción.
    
    Parámetros:
    -----------
    row : pd.Series
        Fila del DataFrame con datos de la opción
    r : float
        Tasa libre de riesgo
    
    Retorna:
    --------
    dict
        Resultados BSM
    """
    S = row['underlying_price']
    K = row['strike']
    T = days_to_years(row['dte'])
    sigma = row['iv']
    option_type = row['type']
    
    # Calcular precio BSM
    bsm_price = black_scholes_price(S, K, T, r, sigma, option_type)
    
    # Calcular griegas BSM
    greeks = calculate_greeks(S, K, T, r, sigma)
    bsm_greeks = greeks[option_type]
    
    return {
        'bsm_price': bsm_price,
        'bsm_delta': bsm_greeks['delta'],
        'bsm_gamma': bsm_greeks['gamma'],
        'bsm_vega': bsm_greeks['vega'],
        'bsm_theta': bsm_greeks['theta'],
        'bsm_rho': bsm_greeks['rho']
    }


def analyze_options_sample(df: pd.DataFrame, sample_size: int = 100) -> pd.DataFrame:
    """
    Analiza una muestra de opciones comparando BSM vs mercado.
    
    Parámetros:
    -----------
    df : pd.DataFrame
        Datos de opciones líquidas
    sample_size : int
        Tamaño de la muestra a analizar
    
    Retorna:
    --------
    pd.DataFrame
        Análisis completo
    """
    print(f"\n📊 Analizando muestra de {sample_size} opciones...")
    
    # Tomar muestra aleatoria
    sample = df.sample(n=min(sample_size, len(df)), random_state=42).copy()
    
    # Obtener tasa libre de riesgo
    r = get_risk_free_rate()
    
    # Calcular BSM para cada opción
    bsm_results = []
    errors = 0
    for idx, row in sample.iterrows():
        try:
            bsm = calculate_bsm_for_option(row, r)
            bsm_results.append(bsm)
        except Exception as e:
            errors += 1
            bsm_results.append({
                'bsm_price': None,
                'bsm_delta': None,
                'bsm_gamma': None,
                'bsm_vega': None,
                'bsm_theta': None,
                'bsm_rho': None
            })
    
    if errors > 0:
        print(f"   ⚠️  {errors} errores en cálculos BSM")
    
    # Agregar resultados BSM al DataFrame
    bsm_df = pd.DataFrame(bsm_results, index=sample.index)
    sample = pd.concat([sample, bsm_df], axis=1)
    
    # Calcular diferencias
    sample['price_diff'] = sample['close'] - sample['bsm_price']
    sample['price_diff_pct'] = (sample['price_diff'] / sample['bsm_price']) * 100
    sample['delta_diff'] = sample['delta'] - sample['bsm_delta']
    sample['gamma_diff'] = sample['gamma'] - sample['bsm_gamma']
    sample['vega_diff'] = sample['vega'] - sample['bsm_vega']
    sample['theta_diff'] = sample['theta'] - sample['bsm_theta']
    
    valid_count = sample['bsm_price'].notna().sum()
    print(f"   ✓ Análisis completado: {valid_count}/{len(sample)} opciones válidas")
    
    return sample


def generate_summary_report(analysis: pd.DataFrame) -> None:
    """
    Genera reporte resumen del análisis.
    
    Parámetros:
    -----------
    analysis : pd.DataFrame
        DataFrame con análisis completo
    """
    print("\n" + "=" * 70)
    print("REPORTE DE ANÁLISIS CUANTITATIVO")
    print("=" * 70)
    
    # Filtrar solo filas con datos válidos
    valid = analysis.dropna(subset=['bsm_price', 'price_diff_pct'])
    
    if len(valid) == 0:
        print("⚠️  No hay datos válidos para generar el reporte")
        return
    
    # 1. Estadísticas de Precios
    print("\n1️⃣  COMPARACIÓN DE PRECIOS (Mercado vs BSM)")
    print("-" * 70)
    print(f"   Opciones analizadas: {len(valid)}")
    print(f"   Precio promedio mercado: ${valid['close'].mean():.4f}")
    print(f"   Precio promedio BSM: ${valid['bsm_price'].mean():.4f}")
    print(f"   Diferencia promedio: ${valid['price_diff'].mean():.4f} ({valid['price_diff_pct'].mean():+.2f}%)")
    print(f"   Desv. Est. diferencia: {valid['price_diff_pct'].std():.2f}%")
    print(f"   Rango diferencia: {valid['price_diff_pct'].min():.2f}% a {valid['price_diff_pct'].max():.2f}%")
    
    # 2. Opciones mal valoradas (threshold 10%)
    mispriced = valid[abs(valid['price_diff_pct']) > 10]
    print(f"\n   🎯 Opciones potencialmente mal valoradas (>10% diferencia):")
    print(f"      Total: {len(mispriced)} ({len(mispriced)/len(valid)*100:.1f}%)")
    
    if len(mispriced) > 0:
        overvalued = mispriced[mispriced['price_diff_pct'] > 0]
        undervalued = mispriced[mispriced['price_diff_pct'] < 0]
        print(f"      - Sobrevaluadas (mercado > BSM): {len(overvalued)}")
        print(f"      - Subvaluadas (mercado < BSM): {len(undervalued)}")
    
    # 3. Comparación de Griegas
    print("\n2️⃣  COMPARACIÓN DE GRIEGAS (Polygon vs BSM)")
    print("-" * 70)
    
    greeks = ['delta', 'gamma', 'vega', 'theta']
    for greek in greeks:
        diff_col = f'{greek}_diff'
        if diff_col in valid.columns:
            mean_diff = valid[diff_col].mean()
            std_diff = valid[diff_col].std()
            print(f"   {greek.capitalize():8s}: Δ promedio = {mean_diff:+.6f}, σ = {std_diff:.6f}")
    
    # 4. Análisis por Moneyness
    print("\n3️⃣  ANÁLISIS POR MONEYNESS")
    print("-" * 70)
    
    valid['moneyness'] = valid['strike'] / valid['underlying_price']
    valid['moneyness_category'] = pd.cut(
        valid['moneyness'],
        bins=[0, 0.95, 1.05, float('inf')],
        labels=['ITM', 'ATM', 'OTM']
    )
    
    for category in ['ITM', 'ATM', 'OTM']:
        cat_data = valid[valid['moneyness_category'] == category]
        if len(cat_data) > 0:
            print(f"   {category:3s}: {len(cat_data):3d} opciones | "
                  f"Δ precio: {cat_data['price_diff_pct'].mean():+6.2f}% | "
                  f"Δ delta: {cat_data['delta_diff'].mean():+.4f}")
    
    # 5. Análisis por Tipo
    print("\n4️⃣  ANÁLISIS POR TIPO DE OPCIÓN")
    print("-" * 70)
    
    for opt_type in ['call', 'put']:
        type_data = valid[valid['type'] == opt_type]
        if len(type_data) > 0:
            print(f"   {opt_type.upper():4s}: {len(type_data):3d} opciones | "
                  f"Δ precio: {type_data['price_diff_pct'].mean():+6.2f}% | "
                  f"Δ delta: {type_data['delta_diff'].mean():+.4f}")
    
    # 6. Top 10 Discrepancias
    print("\n5️⃣  TOP 10 MAYORES DISCREPANCIAS EN PRECIO")
    print("-" * 70)
    
    top_discrepancies = valid.nlargest(10, 'price_diff_pct')[
        ['ticker', 'type', 'strike', 'dte', 'close', 'bsm_price', 'price_diff_pct']
    ]
    
    print(f"\n   {'Ticker':<8} {'Tipo':<6} {'Strike':<8} {'DTE':<5} {'Mercado':<10} {'BSM':<10} {'Diff %':<10}")
    print("   " + "-" * 70)
    for _, row in top_discrepancies.iterrows():
        print(f"   {row['ticker']:<8} {row['type']:<6} ${row['strike']:<7.2f} {row['dte']:<5.0f} "
              f"${row['close']:<9.2f} ${row['bsm_price']:<9.2f} {row['price_diff_pct']:+9.2f}%")
    
    print("\n" + "=" * 70)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Demo del módulo cuantitativo')
    parser.add_argument('--ticker', default='SPY', help='Ticker a analizar (default: SPY)')
    parser.add_argument('--sample', type=int, default=100, help='Tamaño de muestra (default: 100)')
    parser.add_argument('--dte', type=int, default=None, help='Filtrar por DTE específico')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("DEMOSTRACIÓN: Módulo de Modelado Cuantitativo")
    print("=" * 70)
    print(f"\n🎯 Ticker: {args.ticker}")
    print(f"📊 Tamaño de muestra: {args.sample}")
    if args.dte:
        print(f"📅 DTE: {args.dte} días")
    
    try:
        # 1. Cargar datos
        df = load_options_data(args.ticker)
        
        # 2. Filtrar opciones líquidas
        liquid = filter_liquid_options(df)
        
        # 3. Filtrar por DTE si se especifica
        if args.dte:
            liquid = liquid[liquid['dte'] == args.dte]
            print(f"   ✓ Opciones con DTE={args.dte}: {len(liquid)}")
        
        if len(liquid) == 0:
            print("⚠️  No hay opciones líquidas disponibles con los filtros especificados")
            return
        
        # 4. Analizar muestra
        analysis = analyze_options_sample(liquid, args.sample)
        
        # 5. Generar reporte
        generate_summary_report(analysis)
        
        # 6. Guardar resultados (opcional)
        output_dir = Path(__file__).parent.parent / "data" / "analysis"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"quantitative_analysis_{args.ticker}_{timestamp}.csv"
        
        analysis.to_csv(output_file, index=False)
        print(f"\n💾 Resultados guardados en: {output_file}")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Asegúrate de haber ejecutado extract_historical.py primero")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()