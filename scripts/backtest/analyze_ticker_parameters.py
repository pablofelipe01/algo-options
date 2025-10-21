"""
Análisis de Parámetros Óptimos por Ticker
Determina profit targets, stop losses y DTEs ideales basados en características de cada ticker.

Autor: Sistema de Trading Algorítmico
Fecha: Fase 2 - TODO #5
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Configuración de visualización
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (18, 12)
plt.rcParams['font.size'] = 10

# ============================================================================
# CARGA DE DATOS
# ============================================================================

def load_backtest_data():
    """Carga los datos del backtest optimizado."""
    data_path = Path(__file__).parent.parent.parent / "data" / "analysis" / "ml_dataset_10_tickers.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(f"No se encontró: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Convertir fechas
    df['entry_date'] = pd.to_datetime(df['entry_date'])
    df['exit_date'] = pd.to_datetime(df['exit_date'])
    
    return df

def load_historical_data(ticker):
    """Carga datos históricos de un ticker para analizar IV."""
    data_path = Path(__file__).parent.parent.parent / "data" / "historical" / f"{ticker}_60days.parquet"
    
    if not data_path.exists():
        return None
    
    df = pd.read_parquet(data_path)
    df['date'] = pd.to_datetime(df['date'])
    
    return df


# ============================================================================
# ANÁLISIS DE VOLATILIDAD
# ============================================================================

def analyze_ticker_volatility(tickers):
    """
    Analiza la volatilidad implícita promedio de cada ticker.
    
    Returns:
        DataFrame con métricas de volatilidad por ticker
    """
    results = []
    
    print("\n📊 ANÁLISIS DE VOLATILIDAD POR TICKER")
    print("="*70)
    
    for ticker in tickers:
        hist_data = load_historical_data(ticker)
        
        if hist_data is None:
            print(f"  ⚠️  {ticker}: Sin datos históricos")
            continue
        
        # Calcular métricas de IV
        iv_mean = hist_data['iv'].mean()
        iv_median = hist_data['iv'].median()
        iv_std = hist_data['iv'].std()
        iv_min = hist_data['iv'].min()
        iv_max = hist_data['iv'].max()
        
        # Clasificar volatilidad
        if iv_mean >= 0.40:
            vol_category = "High"
        elif iv_mean >= 0.25:
            vol_category = "Medium"
        else:
            vol_category = "Low"
        
        results.append({
            'ticker': ticker,
            'iv_mean': iv_mean,
            'iv_median': iv_median,
            'iv_std': iv_std,
            'iv_min': iv_min,
            'iv_max': iv_max,
            'vol_category': vol_category
        })
        
        print(f"  {ticker:<6} | IV Mean: {iv_mean:.3f} | Vol Category: {vol_category}")
    
    df_vol = pd.DataFrame(results)
    return df_vol


# ============================================================================
# ANÁLISIS DE PERFORMANCE POR TICKER
# ============================================================================

def analyze_ticker_performance(df_trades):
    """
    Analiza la performance de cada ticker en el backtest.
    
    Returns:
        DataFrame con métricas por ticker
    """
    print("\n📈 ANÁLISIS DE PERFORMANCE POR TICKER")
    print("="*70)
    
    ticker_stats = []
    
    for ticker in df_trades['ticker'].unique():
        ticker_trades = df_trades[df_trades['ticker'] == ticker]
        
        # Métricas básicas
        total_trades = len(ticker_trades)
        win_rate = (ticker_trades['profitable'].sum() / total_trades) * 100
        avg_return = ticker_trades['return_pct'].mean()
        total_pnl = ticker_trades['pnl'].sum()
        avg_days_held = ticker_trades['days_held'].mean()
        
        # Análisis de cierres
        profit_targets = len(ticker_trades[ticker_trades['status'] == 'closed_profit'])
        stop_losses = len(ticker_trades[ticker_trades['status'] == 'closed_loss'])
        expirations = len(ticker_trades[ticker_trades['status'] == 'closed_end'])
        
        early_closure_rate = ((profit_targets + stop_losses) / total_trades) * 100
        
        # Retornos por tipo de cierre
        profit_target_returns = ticker_trades[ticker_trades['status'] == 'closed_profit']['return_pct'].mean()
        stop_loss_returns = ticker_trades[ticker_trades['status'] == 'closed_loss']['return_pct'].mean()
        expiration_returns = ticker_trades[ticker_trades['status'] == 'closed_end']['return_pct'].mean()
        
        # Días promedio por tipo de cierre
        profit_days = ticker_trades[ticker_trades['status'] == 'closed_profit']['days_held'].mean()
        loss_days = ticker_trades[ticker_trades['status'] == 'closed_loss']['days_held'].mean()
        expiration_days = ticker_trades[ticker_trades['status'] == 'closed_end']['days_held'].mean()
        
        ticker_stats.append({
            'ticker': ticker,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'total_pnl': total_pnl,
            'avg_days_held': avg_days_held,
            'profit_targets': profit_targets,
            'stop_losses': stop_losses,
            'expirations': expirations,
            'early_closure_rate': early_closure_rate,
            'profit_target_returns': profit_target_returns,
            'stop_loss_returns': stop_loss_returns,
            'expiration_returns': expiration_returns,
            'profit_days': profit_days,
            'loss_days': loss_days,
            'expiration_days': expiration_days
        })
        
        print(f"\n{ticker}:")
        print(f"  Trades: {total_trades} | Win Rate: {win_rate:.1f}% | PnL: ${total_pnl:,.0f}")
        print(f"  Early Closures: {early_closure_rate:.1f}% ({profit_targets} profit, {stop_losses} loss)")
        print(f"  Avg Return: {avg_return:.1f}% | Avg Days: {avg_days_held:.1f}")
    
    return pd.DataFrame(ticker_stats)


# ============================================================================
# RECOMENDACIONES DE PARÁMETROS
# ============================================================================

def generate_ticker_recommendations(df_vol, df_perf):
    """
    Genera recomendaciones de parámetros por ticker basado en volatilidad y performance.
    
    Returns:
        DataFrame con recomendaciones
    """
    print("\n🎯 GENERANDO RECOMENDACIONES DE PARÁMETROS")
    print("="*70)
    
    # Merge volatility y performance
    df_merged = pd.merge(df_perf, df_vol, on='ticker', how='left')
    
    recommendations = []
    
    for _, row in df_merged.iterrows():
        ticker = row['ticker']
        vol_category = row.get('vol_category', 'Medium')
        early_closure_rate = row.get('early_closure_rate', 0)
        profit_target_returns = row.get('profit_target_returns', 0)
        avg_days_held = row.get('avg_days_held', 40)
        
        # PROFIT TARGET basado en volatilidad y historial de cierres
        if vol_category == "High":
            # Alta volatilidad: cerrar rápido para capturar movimientos
            profit_target_pct = 25
            reasoning_pt = "Alta volatilidad → cerrar rápido para capturar theta"
        elif vol_category == "Medium":
            profit_target_pct = 35
            reasoning_pt = "Volatilidad media → balance entre theta y protección"
        else:  # Low
            profit_target_pct = 50
            reasoning_pt = "Baja volatilidad → permitir mayor decay de theta"
        
        # Ajustar si el ticker tiene buenos resultados con early closures
        if early_closure_rate > 70 and profit_target_returns > 200:
            profit_target_pct -= 5  # Ser más agresivo
            reasoning_pt += " | Alto éxito en cierres anticipados"
        
        # STOP LOSS basado en volatilidad
        if vol_category == "High":
            # Alta volatilidad: stop loss más amplio para evitar whipsaws
            stop_loss_pct = 200
            reasoning_sl = "Alta volatilidad → stop loss amplio anti-whipsaw"
        elif vol_category == "Medium":
            stop_loss_pct = 150
            reasoning_sl = "Volatilidad media → stop loss balanceado"
        else:  # Low
            stop_loss_pct = 100
            reasoning_sl = "Baja volatilidad → stop loss ajustado"
        
        # DTE ÓPTIMO basado en categoría y días promedio
        # Clasificar ticker por tipo
        if ticker in ['SPY', 'QQQ', 'IWM']:
            ticker_type = "ETF"
            dte_min = 49
            dte_max = 56
            reasoning_dte = "ETF → Long DTE (49-56) para estabilidad"
        elif ticker in ['GLD', 'SLV']:
            ticker_type = "Commodity"
            dte_min = 56
            dte_max = 60
            reasoning_dte = "Commodity → Extra Long DTE (56-60) para volatilidad baja"
        else:  # Tech stocks
            ticker_type = "Tech"
            dte_min = 42
            dte_max = 49
            reasoning_dte = "Tech → Medium-Long DTE (42-49) para capturar ciclos"
        
        recommendations.append({
            'ticker': ticker,
            'ticker_type': ticker_type,
            'vol_category': vol_category,
            'profit_target_pct': profit_target_pct,
            'stop_loss_pct': stop_loss_pct,
            'dte_min': dte_min,
            'dte_max': dte_max,
            'reasoning_pt': reasoning_pt,
            'reasoning_sl': reasoning_sl,
            'reasoning_dte': reasoning_dte
        })
        
        print(f"\n{ticker} ({ticker_type}, {vol_category} Vol):")
        print(f"  Profit Target: {profit_target_pct}%")
        print(f"    → {reasoning_pt}")
        print(f"  Stop Loss: {stop_loss_pct}%")
        print(f"    → {reasoning_sl}")
        print(f"  DTE Range: {dte_min}-{dte_max} días")
        print(f"    → {reasoning_dte}")
    
    return pd.DataFrame(recommendations)


# ============================================================================
# VISUALIZACIONES
# ============================================================================

def create_visualizations(df_vol, df_perf, df_recommendations):
    """Crea visualizaciones comprehensivas."""
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Volatilidad por Ticker
    ax1 = fig.add_subplot(gs[0, 0])
    if df_vol is not None and len(df_vol) > 0:
        colors = df_vol['vol_category'].map({'High': 'red', 'Medium': 'orange', 'Low': 'green'})
        bars = ax1.bar(df_vol['ticker'], df_vol['iv_mean'], color=colors, alpha=0.7, edgecolor='black')
        ax1.set_title('Implied Volatility by Ticker', fontweight='bold')
        ax1.set_xlabel('Ticker')
        ax1.set_ylabel('IV Mean')
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.tick_params(axis='x', rotation=45)
        
        # Leyenda
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', label='High Vol (≥0.40)'),
            Patch(facecolor='orange', label='Medium Vol (0.25-0.40)'),
            Patch(facecolor='green', label='Low Vol (<0.25)')
        ]
        ax1.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    # 2. PnL por Ticker
    ax2 = fig.add_subplot(gs[0, 1])
    if df_perf is not None and len(df_perf) > 0:
        colors = ['green' if x > 0 else 'red' for x in df_perf['total_pnl']]
        bars = ax2.bar(df_perf['ticker'], df_perf['total_pnl'], color=colors, alpha=0.7, edgecolor='black')
        ax2.set_title('Total PnL by Ticker', fontweight='bold')
        ax2.set_xlabel('Ticker')
        ax2.set_ylabel('PnL ($)')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.tick_params(axis='x', rotation=45)
        ax2.axhline(y=0, color='black', linewidth=1)
        
        # Valores encima de barras
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}', ha='center', va='bottom' if height > 0 else 'top',
                    fontsize=8)
    
    # 3. Early Closure Rate por Ticker
    ax3 = fig.add_subplot(gs[0, 2])
    if df_perf is not None and len(df_perf) > 0:
        bars = ax3.bar(df_perf['ticker'], df_perf['early_closure_rate'], 
                      color='#2E86AB', alpha=0.7, edgecolor='black')
        ax3.set_title('Early Closure Rate by Ticker', fontweight='bold')
        ax3.set_xlabel('Ticker')
        ax3.set_ylabel('Early Closure Rate (%)')
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.tick_params(axis='x', rotation=45)
        
        # Línea de referencia
        ax3.axhline(y=50, color='red', linestyle='--', linewidth=1, label='50% threshold')
        ax3.legend(fontsize=8)
    
    # 4. Profit Target Recommendations
    ax4 = fig.add_subplot(gs[1, 0])
    if df_recommendations is not None and len(df_recommendations) > 0:
        colors_rec = df_recommendations['vol_category'].map({
            'High': 'red', 'Medium': 'orange', 'Low': 'green'
        })
        bars = ax4.bar(df_recommendations['ticker'], df_recommendations['profit_target_pct'],
                      color=colors_rec, alpha=0.7, edgecolor='black')
        ax4.set_title('Recommended Profit Targets', fontweight='bold')
        ax4.set_xlabel('Ticker')
        ax4.set_ylabel('Profit Target (%)')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.tick_params(axis='x', rotation=45)
        
        # Valores
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}%', ha='center', va='bottom', fontsize=8)
    
    # 5. Stop Loss Recommendations
    ax5 = fig.add_subplot(gs[1, 1])
    if df_recommendations is not None and len(df_recommendations) > 0:
        bars = ax5.bar(df_recommendations['ticker'], df_recommendations['stop_loss_pct'],
                      color=colors_rec, alpha=0.7, edgecolor='black')
        ax5.set_title('Recommended Stop Losses', fontweight='bold')
        ax5.set_xlabel('Ticker')
        ax5.set_ylabel('Stop Loss (%)')
        ax5.grid(True, alpha=0.3, axis='y')
        ax5.tick_params(axis='x', rotation=45)
        
        # Valores
        for bar in bars:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}%', ha='center', va='bottom', fontsize=8)
    
    # 6. DTE Range Recommendations
    ax6 = fig.add_subplot(gs[1, 2])
    if df_recommendations is not None and len(df_recommendations) > 0:
        x_pos = np.arange(len(df_recommendations))
        dte_ranges = df_recommendations['dte_max'] - df_recommendations['dte_min']
        
        bars = ax6.bar(x_pos, dte_ranges, bottom=df_recommendations['dte_min'],
                      color='#A23B72', alpha=0.7, edgecolor='black')
        ax6.set_title('Recommended DTE Ranges', fontweight='bold')
        ax6.set_xlabel('Ticker')
        ax6.set_ylabel('DTE Range (days)')
        ax6.set_xticks(x_pos)
        ax6.set_xticklabels(df_recommendations['ticker'], rotation=45)
        ax6.grid(True, alpha=0.3, axis='y')
        
        # Anotaciones
        for i, row in df_recommendations.iterrows():
            mid_point = row['dte_min'] + (row['dte_max'] - row['dte_min']) / 2
            ax6.text(i, mid_point, f"{row['dte_min']}-{row['dte_max']}",
                    ha='center', va='center', fontsize=8, fontweight='bold')
    
    # 7. Returns por Tipo de Cierre (agregado)
    ax7 = fig.add_subplot(gs[2, 0])
    if df_perf is not None and len(df_perf) > 0:
        avg_profit_returns = df_perf['profit_target_returns'].mean()
        avg_loss_returns = df_perf['stop_loss_returns'].mean()
        avg_exp_returns = df_perf['expiration_returns'].mean()
        
        categories = ['Profit\nTargets', 'Stop\nLosses', 'Expirations']
        values = [avg_profit_returns, avg_loss_returns, avg_exp_returns]
        colors_bar = ['green', 'red', 'gray']
        
        bars = ax7.bar(categories, values, color=colors_bar, alpha=0.7, edgecolor='black')
        ax7.set_title('Avg Returns by Closure Type', fontweight='bold')
        ax7.set_ylabel('Average Return (%)')
        ax7.grid(True, alpha=0.3, axis='y')
        ax7.axhline(y=0, color='black', linewidth=1)
        
        # Valores
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax7.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}%', ha='center', va='bottom' if val > 0 else 'top',
                    fontsize=9, fontweight='bold')
    
    # 8. Days Held por Tipo de Cierre (agregado)
    ax8 = fig.add_subplot(gs[2, 1])
    if df_perf is not None and len(df_perf) > 0:
        avg_profit_days = df_perf['profit_days'].mean()
        avg_loss_days = df_perf['loss_days'].mean()
        avg_exp_days = df_perf['expiration_days'].mean()
        
        categories = ['Profit\nTargets', 'Stop\nLosses', 'Expirations']
        values = [avg_profit_days, avg_loss_days, avg_exp_days]
        colors_bar = ['green', 'red', 'gray']
        
        bars = ax8.bar(categories, values, color=colors_bar, alpha=0.7, edgecolor='black')
        ax8.set_title('Avg Days Held by Closure Type', fontweight='bold')
        ax8.set_ylabel('Days')
        ax8.grid(True, alpha=0.3, axis='y')
        
        # Valores
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax8.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 9. Resumen de Recomendaciones (texto)
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')
    
    if df_recommendations is not None and len(df_recommendations) > 0:
        summary_text = "RESUMEN DE RECOMENDACIONES\n"
        summary_text += "="*35 + "\n\n"
        
        # Agrupar por categoría de volatilidad
        for vol_cat in ['High', 'Medium', 'Low']:
            vol_group = df_recommendations[df_recommendations['vol_category'] == vol_cat]
            if len(vol_group) > 0:
                tickers_str = ', '.join(vol_group['ticker'].tolist())
                pt_avg = vol_group['profit_target_pct'].mean()
                sl_avg = vol_group['stop_loss_pct'].mean()
                
                summary_text += f"{vol_cat} Volatility:\n"
                summary_text += f"  Tickers: {tickers_str}\n"
                summary_text += f"  Profit Target: {pt_avg:.0f}%\n"
                summary_text += f"  Stop Loss: {sl_avg:.0f}%\n\n"
        
        # Agrupar por tipo
        summary_text += "\nPor Tipo de Activo:\n"
        for asset_type in ['ETF', 'Tech', 'Commodity']:
            type_group = df_recommendations[df_recommendations['ticker_type'] == asset_type]
            if len(type_group) > 0:
                tickers_str = ', '.join(type_group['ticker'].tolist())
                dte_min_avg = type_group['dte_min'].mean()
                dte_max_avg = type_group['dte_max'].mean()
                
                summary_text += f"\n{asset_type}:\n"
                summary_text += f"  {tickers_str}\n"
                summary_text += f"  DTE: {dte_min_avg:.0f}-{dte_max_avg:.0f} días\n"
        
        ax9.text(0.05, 0.95, summary_text, transform=ax9.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # Título general
    fig.suptitle('Análisis de Parámetros Dinámicos por Ticker', 
                fontsize=16, fontweight='bold', y=0.995)
    
    return fig


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("🎯 ANÁLISIS DE PARÁMETROS DINÁMICOS POR TICKER")
    print("="*70)
    
    # 1. Cargar datos del backtest
    print("\n📁 Cargando datos del backtest...")
    df_trades = load_backtest_data()
    print(f"   ✅ Cargados {len(df_trades)} trades de {df_trades['ticker'].nunique()} tickers")
    
    # 2. Obtener lista de tickers únicos
    tickers = sorted(df_trades['ticker'].unique())
    print(f"\n   Tickers: {', '.join(tickers)}")
    
    # 3. Analizar volatilidad de cada ticker
    df_volatility = analyze_ticker_volatility(tickers)
    
    # 4. Analizar performance de cada ticker
    df_performance = analyze_ticker_performance(df_trades)
    
    # 5. Generar recomendaciones
    df_recommendations = generate_ticker_recommendations(df_volatility, df_performance)
    
    # 6. Guardar resultados CSV en data/analysis/
    data_dir = Path(__file__).parent.parent.parent / "data" / "analysis"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "ticker_parameters_recommendations.csv"
    df_recommendations.to_csv(output_path, index=False)
    print(f"\n💾 Recomendaciones guardadas en: {output_path}")
    
    # 7. Crear visualizaciones
    print(f"\n📊 Generando visualizaciones...")
    fig = create_visualizations(df_volatility, df_performance, df_recommendations)
    
    # Guardar gráficos en scripts/visualizations/
    viz_dir = Path(__file__).parent.parent / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    viz_path = viz_dir / "ticker_parameters_analysis.png"
    plt.savefig(viz_path, dpi=150, bbox_inches='tight')
    print(f"   ✅ Gráficos guardados en: {viz_path}")
    
    plt.show()
    
    # 8. Mostrar tabla final de recomendaciones
    print("\n" + "="*70)
    print("📋 TABLA FINAL DE RECOMENDACIONES")
    print("="*70)
    print(df_recommendations[['ticker', 'ticker_type', 'vol_category', 
                             'profit_target_pct', 'stop_loss_pct', 
                             'dte_min', 'dte_max']].to_string(index=False))
    
    print("\n✅ Análisis completado")


if __name__ == "__main__":
    main()
