"""
ANÁLISIS EXPLORATORIO DE RESULTADOS DE BACKTEST
================================================

Este script analiza los resultados del backtest multi-ticker para:
1. Identificar patrones en los mejores trades
2. Comparar performance entre tickers y categorías
3. Responder preguntas específicas (¿por qué GLD superó a SPY?, etc.)
4. Generar visualizaciones profesionales
5. Proveer insights para optimización

Autor: Sistema de Trading Algorítmico
Fecha: 2025-10-20
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuración de estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (20, 12)
plt.rcParams['font.size'] = 10

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Categorización de tickers
TICKER_CATEGORIES = {
    'ETFs': ['SPY', 'QQQ', 'IWM'],
    'Tech': ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN'],
    'Commodities': ['GLD', 'SLV']
}

# Ruta al dataset
CSV_PATH = Path(__file__).parent / 'ml_dataset_10_tickers.csv'

# =============================================================================
# FUNCIONES DE ANÁLISIS
# =============================================================================

def load_and_validate_data(csv_path):
    """Carga y valida el dataset"""
    print("=" * 80)
    print("📊 CARGANDO DATASET")
    print("=" * 80)
    
    df = pd.read_csv(csv_path)
    
    # Convertir fechas
    df['entry_date'] = pd.to_datetime(df['entry_date'])
    df['exit_date'] = pd.to_datetime(df['exit_date'])
    
    # Agregar categoría
    def get_category(ticker):
        for category, tickers in TICKER_CATEGORIES.items():
            if ticker in tickers:
                return category
        return 'Other'
    
    df['category'] = df['ticker'].apply(get_category)
    
    print(f"\n✅ Dataset cargado exitosamente")
    print(f"   - Total de trades: {len(df)}")
    print(f"   - Tickers únicos: {df['ticker'].nunique()}")
    print(f"   - Período: {df['entry_date'].min().date()} → {df['exit_date'].max().date()}")
    print(f"   - Estrategia: {df['strategy'].unique()[0]}")
    
    return df


def basic_statistics(df):
    """Estadísticas descriptivas básicas"""
    print("\n" + "=" * 80)
    print("📈 ESTADÍSTICAS DESCRIPTIVAS")
    print("=" * 80)
    
    # Overview general
    print("\n🎯 RESULTADOS GENERALES:")
    print(f"   - Win Rate: {df['profitable'].mean() * 100:.2f}%")
    print(f"   - Total PnL: ${df['pnl'].sum():,.2f}")
    print(f"   - Retorno promedio: {df['return_pct'].mean():.2f}%")
    print(f"   - Retorno mediano: {df['return_pct'].median():.2f}%")
    print(f"   - Desviación estándar: {df['return_pct'].std():.2f}%")
    print(f"   - Mejor trade: {df['return_pct'].max():.2f}%")
    print(f"   - Peor trade: {df['return_pct'].min():.2f}%")
    
    # Premium stats
    print("\n💰 PRIMAS Y RIESGO:")
    print(f"   - Premium promedio: ${df['premium_collected'].mean():.2f}")
    print(f"   - Riesgo promedio: ${df['max_risk'].mean():.2f}")
    print(f"   - Ratio promedio (Premium/Risk): {(df['premium_collected'] / df['max_risk']).mean():.2%}")
    
    # Timing stats
    print("\n⏱️  TIMING:")
    print(f"   - DTE promedio al entrar: {df['dte_entry'].mean():.1f} días")
    print(f"   - Días sostenidos promedio: {df['days_held'].mean():.1f} días")
    print(f"   - DTE bucket más común: {df['dte_bucket'].mode()[0]}")
    
    # Status
    print("\n🏁 STATUS DE CIERRE:")
    print(df['status'].value_counts().to_string())
    
    return df


def performance_by_ticker(df):
    """Análisis detallado por ticker"""
    print("\n" + "=" * 80)
    print("🏆 PERFORMANCE POR TICKER (Ranking)")
    print("=" * 80)
    
    ticker_stats = df.groupby('ticker').agg({
        'pnl': ['count', 'sum', 'mean'],
        'return_pct': ['mean', 'std', 'median'],
        'profitable': 'mean',
        'premium_collected': 'mean',
        'max_risk': 'mean',
        'days_held': 'mean'
    }).round(2)
    
    ticker_stats.columns = ['Trades', 'Total_PnL', 'Avg_PnL', 
                            'Avg_Return%', 'Std_Return%', 'Median_Return%',
                            'Win_Rate', 'Avg_Premium', 'Avg_Risk', 'Avg_Days']
    
    # Calcular ratio
    ticker_stats['Premium/Risk'] = (ticker_stats['Avg_Premium'] / ticker_stats['Avg_Risk'] * 100).round(2)
    
    # Ordenar por retorno promedio
    ticker_stats = ticker_stats.sort_values('Avg_Return%', ascending=False)
    
    print("\n" + ticker_stats.to_string())
    
    # Top 3
    print("\n" + "🥇" * 40)
    print("TOP 3 PERFORMERS:")
    top3 = ticker_stats.head(3)
    for i, (ticker, row) in enumerate(top3.iterrows(), 1):
        medal = ['🥇', '🥈', '🥉'][i-1]
        print(f"{medal} {ticker}: {row['Avg_Return%']:.2f}% avg return, {row['Trades']:.0f} trades, ${row['Total_PnL']:.2f} total PnL")
    
    return ticker_stats


def performance_by_category(df):
    """Análisis por categoría de activo"""
    print("\n" + "=" * 80)
    print("📦 PERFORMANCE POR CATEGORÍA")
    print("=" * 80)
    
    category_stats = df.groupby('category').agg({
        'pnl': ['count', 'sum', 'mean'],
        'return_pct': ['mean', 'std'],
        'profitable': 'mean',
        'premium_collected': 'mean',
        'max_risk': 'mean'
    }).round(2)
    
    category_stats.columns = ['Trades', 'Total_PnL', 'Avg_PnL_per_Trade',
                              'Avg_Return%', 'Std_Return%', 'Win_Rate',
                              'Avg_Premium', 'Avg_Risk']
    
    category_stats = category_stats.sort_values('Avg_Return%', ascending=False)
    
    print("\n" + category_stats.to_string())
    
    # Insights
    print("\n💡 INSIGHTS POR CATEGORÍA:")
    for category, row in category_stats.iterrows():
        print(f"   - {category}: {row['Avg_Return%']:.2f}% avg return, "
              f"{row['Trades']:.0f} trades, ${row['Avg_PnL_per_Trade']:.2f} avg PnL/trade")
    
    return category_stats


def answer_key_questions(df, ticker_stats):
    """Responde las preguntas específicas del análisis"""
    print("\n" + "=" * 80)
    print("❓ RESPONDIENDO PREGUNTAS CLAVE")
    print("=" * 80)
    
    # Q1: ¿Por qué GLD superó a SPY?
    print("\n1️⃣  ¿POR QUÉ GLD SUPERÓ AMPLIAMENTE A SPY?")
    print("-" * 80)
    
    gld_trades = df[df['ticker'] == 'GLD']
    spy_trades = df[df['ticker'] == 'SPY']
    
    print(f"\n   GLD:")
    print(f"   - Trades: {len(gld_trades)}")
    print(f"   - Avg Return: {gld_trades['return_pct'].mean():.2f}%")
    print(f"   - Avg Premium: ${gld_trades['premium_collected'].mean():.2f}")
    print(f"   - Avg Risk: ${gld_trades['max_risk'].mean():.2f}")
    print(f"   - Premium/Risk: {(gld_trades['premium_collected'] / gld_trades['max_risk']).mean():.2%}")
    print(f"   - DTEs: {gld_trades['dte_entry'].tolist()}")
    print(f"   - Entry dates: {gld_trades['entry_date'].dt.date.tolist()}")
    
    print(f"\n   SPY:")
    print(f"   - Trades: {len(spy_trades)}")
    print(f"   - Avg Return: {spy_trades['return_pct'].mean():.2f}%")
    print(f"   - Avg Premium: ${spy_trades['premium_collected'].mean():.2f}")
    print(f"   - Avg Risk: ${spy_trades['max_risk'].mean():.2f}")
    print(f"   - Premium/Risk: {(spy_trades['premium_collected'] / spy_trades['max_risk']).mean():.2%}")
    print(f"   - DTEs: {spy_trades['dte_entry'].tolist()}")
    print(f"   - Entry dates: {spy_trades['entry_date'].dt.date.tolist()}")
    
    print(f"\n   📊 DIFERENCIA CLAVE:")
    gld_ratio = (gld_trades['premium_collected'] / gld_trades['max_risk']).mean()
    spy_ratio = (spy_trades['premium_collected'] / spy_trades['max_risk']).mean()
    print(f"   - GLD tiene un ratio Premium/Risk de {gld_ratio:.2%}")
    print(f"   - SPY tiene un ratio Premium/Risk de {spy_ratio:.2%}")
    print(f"   - GLD recibe {gld_ratio/spy_ratio:.2f}x más premium relativo al riesgo")
    
    # Q2: ¿Por qué IWM superó a SPY/QQQ?
    print("\n\n2️⃣  ¿POR QUÉ IWM SUPERÓ A SPY/QQQ?")
    print("-" * 80)
    
    iwm_trades = df[df['ticker'] == 'IWM']
    qqq_trades = df[df['ticker'] == 'QQQ']
    
    for ticker_name, ticker_df in [('IWM', iwm_trades), ('SPY', spy_trades), ('QQQ', qqq_trades)]:
        print(f"\n   {ticker_name}:")
        print(f"   - Trades: {len(ticker_df)}")
        print(f"   - Avg Return: {ticker_df['return_pct'].mean():.2f}%")
        print(f"   - Premium/Risk: {(ticker_df['premium_collected'] / ticker_df['max_risk']).mean():.2%}")
    
    # Q3: ¿Qué tienen en común los mejores trades?
    print("\n\n3️⃣  ¿QUÉ TIENEN EN COMÚN LOS MEJORES TRADES?")
    print("-" * 80)
    
    # Top 5 trades
    top5 = df.nlargest(5, 'return_pct')
    print("\n   TOP 5 TRADES:")
    for idx, row in top5.iterrows():
        print(f"   - {row['ticker']}: {row['return_pct']:.2f}% return, "
              f"DTE={row['dte_entry']}, Premium/Risk={row['premium_collected']/row['max_risk']:.2%}")
    
    print("\n   📊 CARACTERÍSTICAS COMUNES:")
    print(f"   - Avg DTE: {top5['dte_entry'].mean():.1f} días")
    print(f"   - Avg Premium/Risk: {(top5['premium_collected'] / top5['max_risk']).mean():.2%}")
    print(f"   - Categorías: {top5['category'].value_counts().to_dict()}")
    print(f"   - Tickers: {top5['ticker'].value_counts().to_dict()}")
    
    # Q4: ¿Por qué ninguna posición cerró anticipadamente?
    print("\n\n4️⃣  ¿POR QUÉ NINGUNA POSICIÓN CERRÓ ANTICIPADAMENTE?")
    print("-" * 80)
    
    status_counts = df['status'].value_counts()
    print(f"\n   Status de cierre:")
    print(f"   {status_counts.to_dict()}")
    
    print(f"\n   💡 OBSERVACIÓN:")
    print(f"   - Todas las posiciones llegaron a vencimiento (closed_end)")
    print(f"   - Esto sugiere que:")
    print(f"     • Los profit targets (25%-50%) pueden ser muy agresivos")
    print(f"     • Los stop losses (100%-200%) son muy amplios")
    print(f"     • O el mercado tuvo bajo movimiento en este período")
    
    # Q5: Análisis por categoría
    print("\n\n5️⃣  ¿QUÉ OPTIMIZAR POR CATEGORÍA DE ACTIVO?")
    print("-" * 80)
    
    for category in ['ETFs', 'Tech', 'Commodities']:
        cat_df = df[df['category'] == category]
        if len(cat_df) > 0:
            print(f"\n   {category}:")
            print(f"   - Trades: {len(cat_df)}")
            print(f"   - Avg Return: {cat_df['return_pct'].mean():.2f}%")
            print(f"   - Std Return: {cat_df['return_pct'].std():.2f}%")
            print(f"   - Avg Premium/Risk: {(cat_df['premium_collected'] / cat_df['max_risk']).mean():.2%}")
            print(f"   - Avg DTE: {cat_df['dte_entry'].mean():.1f} días")


def correlation_analysis(df):
    """Análisis de correlaciones"""
    print("\n" + "=" * 80)
    print("🔗 ANÁLISIS DE CORRELACIONES")
    print("=" * 80)
    
    # Seleccionar columnas numéricas relevantes
    numeric_cols = ['dte_entry', 'days_held', 'premium_collected', 
                    'max_risk', 'pnl', 'return_pct']
    
    corr_matrix = df[numeric_cols].corr()
    
    print("\n📊 CORRELACIONES CON RETURN_PCT:")
    return_corr = corr_matrix['return_pct'].sort_values(ascending=False)
    for col, corr in return_corr.items():
        if col != 'return_pct':
            print(f"   - {col}: {corr:.3f}")
    
    print("\n💡 INSIGHTS:")
    strongest = return_corr.drop('return_pct').abs().idxmax()
    print(f"   - La variable más correlacionada con retorno es: {strongest}")
    print(f"   - Correlación: {return_corr[strongest]:.3f}")
    
    return corr_matrix


def create_visualizations(df, ticker_stats, category_stats, corr_matrix):
    """Genera todas las visualizaciones"""
    print("\n" + "=" * 80)
    print("📊 GENERANDO VISUALIZACIONES")
    print("=" * 80)
    
    fig = plt.figure(figsize=(20, 14))
    
    # 1. PnL por ticker
    ax1 = plt.subplot(3, 3, 1)
    ticker_pnl = df.groupby('ticker')['pnl'].sum().sort_values(ascending=False)
    colors = ['green' if x > 0 else 'red' for x in ticker_pnl]
    ticker_pnl.plot(kind='bar', ax=ax1, color=colors, alpha=0.7)
    ax1.set_title('Total PnL por Ticker', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Ticker')
    ax1.set_ylabel('PnL ($)')
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax1.grid(True, alpha=0.3)
    
    # 2. Box plot: Distribución de retornos por ticker
    ax2 = plt.subplot(3, 3, 2)
    df_sorted = df.sort_values('return_pct', ascending=False)
    ticker_order = df_sorted.groupby('ticker')['return_pct'].mean().sort_values(ascending=False).index
    sns.boxplot(data=df, x='ticker', y='return_pct', order=ticker_order, ax=ax2, palette='Set2')
    ax2.set_title('Distribución de Retornos por Ticker', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Ticker')
    ax2.set_ylabel('Retorno (%)')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # 3. Scatter: DTE vs Return (color por ticker)
    ax3 = plt.subplot(3, 3, 3)
    for ticker in df['ticker'].unique():
        ticker_df = df[df['ticker'] == ticker]
        ax3.scatter(ticker_df['dte_entry'], ticker_df['return_pct'], 
                   label=ticker, alpha=0.7, s=100)
    ax3.set_title('DTE vs Retorno', fontsize=12, fontweight='bold')
    ax3.set_xlabel('DTE al Entrar (días)')
    ax3.set_ylabel('Retorno (%)')
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # 4. Scatter: Premium vs PnL
    ax4 = plt.subplot(3, 3, 4)
    scatter = ax4.scatter(df['premium_collected'], df['pnl'], 
                         c=df['return_pct'], cmap='RdYlGn', s=100, alpha=0.7)
    ax4.set_title('Premium Collected vs PnL', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Premium Collected ($)')
    ax4.set_ylabel('PnL ($)')
    plt.colorbar(scatter, ax=ax4, label='Return (%)')
    ax4.grid(True, alpha=0.3)
    
    # 5. Histogram: Distribución de retornos
    ax5 = plt.subplot(3, 3, 5)
    ax5.hist(df['return_pct'], bins=15, color='steelblue', alpha=0.7, edgecolor='black')
    ax5.axvline(df['return_pct'].mean(), color='red', linestyle='--', 
                linewidth=2, label=f'Mean: {df["return_pct"].mean():.2f}%')
    ax5.axvline(df['return_pct'].median(), color='green', linestyle='--', 
                linewidth=2, label=f'Median: {df["return_pct"].median():.2f}%')
    ax5.set_title('Distribución de Retornos', fontsize=12, fontweight='bold')
    ax5.set_xlabel('Retorno (%)')
    ax5.set_ylabel('Frecuencia')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Bar chart: Retornos por categoría
    ax6 = plt.subplot(3, 3, 6)
    category_returns = df.groupby('category')['return_pct'].mean().sort_values(ascending=False)
    category_returns.plot(kind='bar', ax=ax6, color=['#FFD700', '#C0C0C0', '#CD7F32'], alpha=0.7)
    ax6.set_title('Retorno Promedio por Categoría', fontsize=12, fontweight='bold')
    ax6.set_xlabel('Categoría')
    ax6.set_ylabel('Retorno Promedio (%)')
    ax6.tick_params(axis='x', rotation=45)
    ax6.grid(True, alpha=0.3)
    
    # 7. Heatmap: Correlaciones
    ax7 = plt.subplot(3, 3, 7)
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                center=0, ax=ax7, cbar_kws={'label': 'Correlación'})
    ax7.set_title('Matriz de Correlaciones', fontsize=12, fontweight='bold')
    
    # 8. Timeline: Trades por fecha de entrada
    ax8 = plt.subplot(3, 3, 8)
    entry_counts = df.groupby('entry_date').size()
    entry_counts.plot(kind='bar', ax=ax8, color='steelblue', alpha=0.7)
    ax8.set_title('Número de Trades por Fecha de Entrada', fontsize=12, fontweight='bold')
    ax8.set_xlabel('Fecha')
    ax8.set_ylabel('Número de Trades')
    ax8.tick_params(axis='x', rotation=45)
    ax8.grid(True, alpha=0.3)
    
    # 9. Premium/Risk ratio por ticker
    ax9 = plt.subplot(3, 3, 9)
    df['premium_risk_ratio'] = df['premium_collected'] / df['max_risk'] * 100
    premium_ratio = df.groupby('ticker')['premium_risk_ratio'].mean().sort_values(ascending=False)
    premium_ratio.plot(kind='bar', ax=ax9, color='darkgreen', alpha=0.7)
    ax9.set_title('Premium/Risk Ratio por Ticker (%)', fontsize=12, fontweight='bold')
    ax9.set_xlabel('Ticker')
    ax9.set_ylabel('Ratio (%)')
    ax9.tick_params(axis='x', rotation=45)
    ax9.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar
    output_path = Path(__file__).parent / 'analysis_results.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualizaciones guardadas en: {output_path}")
    
    plt.show()


def generate_summary_report(df, ticker_stats, category_stats):
    """Genera reporte resumen con conclusiones"""
    print("\n" + "=" * 80)
    print("📝 REPORTE RESUMEN Y CONCLUSIONES")
    print("=" * 80)
    
    print("\n🎯 HALLAZGOS PRINCIPALES:")
    print("-" * 80)
    
    # Top performer
    top_ticker = ticker_stats.index[0]
    top_return = ticker_stats.iloc[0]['Avg_Return%']
    print(f"\n1. MEJOR TICKER: {top_ticker}")
    print(f"   - Retorno promedio: {top_return:.2f}%")
    print(f"   - Razón: Alto ratio Premium/Risk ({ticker_stats.iloc[0]['Premium/Risk']:.2f}%)")
    
    # Mejor categoría
    top_category = category_stats.index[0]
    top_cat_return = category_stats.iloc[0]['Avg_Return%']
    print(f"\n2. MEJOR CATEGORÍA: {top_category}")
    print(f"   - Retorno promedio: {top_cat_return:.2f}%")
    print(f"   - Trades: {category_stats.iloc[0]['Trades']:.0f}")
    
    # Patrón de cierre
    print(f"\n3. PATRÓN DE CIERRE:")
    print(f"   - {df['status'].value_counts().to_dict()}")
    print(f"   - PROBLEMA: Ningún trade cerró anticipadamente")
    print(f"   - ACCIÓN: Revisar profit targets y stop losses")
    
    # Mejor DTE
    dte_performance = df.groupby('dte_entry')['return_pct'].mean().sort_values(ascending=False)
    print(f"\n4. MEJOR DTE:")
    print(f"   - DTE {dte_performance.index[0]}: {dte_performance.iloc[0]:.2f}% avg return")
    
    print("\n" + "=" * 80)
    print("💡 RECOMENDACIONES PARA OPTIMIZACIÓN")
    print("=" * 80)
    
    print("\n1. SISTEMA DE SCORING:")
    print("   - Aumentar peso de Premium/Risk ratio (actualmente 5%)")
    print("   - Considerar categoría de activo en el score")
    print("   - Agregar factor de spread width")
    
    print("\n2. PARÁMETROS POR CATEGORÍA:")
    print("   - Commodities: targets más agresivos (tienen mejor performance)")
    print("   - ETFs: mantener conservador")
    print("   - Tech: balance intermedio")
    
    print("\n3. PROFIT TARGETS / STOP LOSSES:")
    print("   - CRÍTICO: Revisar por qué ninguno cerró anticipadamente")
    print("   - Considerar targets más realistas (15%-30%)")
    print("   - Revisar si el backtester está checando correctamente")
    
    print("\n4. PRÓXIMOS PASOS:")
    print("   ✓ Grid search de profit targets")
    print("   ✓ Optimizar pesos del scoring system")
    print("   ✓ Implementar reglas diferenciadas por categoría")
    print("   ✓ Analizar por qué GLD/Commodities superan a ETFs")
    
    print("\n" + "=" * 80)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Función principal"""
    print("\n")
    print("🚀" * 40)
    print("ANÁLISIS EXPLORATORIO - BACKTEST MULTI-TICKER")
    print("🚀" * 40)
    
    # 1. Cargar datos
    df = load_and_validate_data(CSV_PATH)
    
    # 2. Estadísticas básicas
    df = basic_statistics(df)
    
    # 3. Performance por ticker
    ticker_stats = performance_by_ticker(df)
    
    # 4. Performance por categoría
    category_stats = performance_by_category(df)
    
    # 5. Responder preguntas clave
    answer_key_questions(df, ticker_stats)
    
    # 6. Análisis de correlaciones
    corr_matrix = correlation_analysis(df)
    
    # 7. Visualizaciones
    create_visualizations(df, ticker_stats, category_stats, corr_matrix)
    
    # 8. Reporte resumen
    generate_summary_report(df, ticker_stats, category_stats)
    
    print("\n" + "✅" * 40)
    print("ANÁLISIS COMPLETADO")
    print("✅" * 40)
    print("\nRevisa 'analysis_results.png' para visualizaciones detalladas\n")


if __name__ == '__main__':
    main()
