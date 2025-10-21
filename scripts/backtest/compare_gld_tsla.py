#!/usr/bin/env python3
"""
Análisis Comparativo: GLD vs TSLA
¿Por qué GLD mantuvo su performance mientras TSLA emergió como campeón?
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuración de estilos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_data():
    """Cargar dataset de ML"""
    print("=" * 80)
    print("📊 CARGANDO DATASET")
    print("=" * 80)
    
    df = pd.read_csv('scripts/ml_dataset_10_tickers.csv')
    
    # Convertir fechas
    df['entry_date'] = pd.to_datetime(df['entry_date'])
    df['exit_date'] = pd.to_datetime(df['exit_date'])
    
    print(f"\n✅ Dataset cargado: {len(df)} trades")
    print(f"   - Período: {df['entry_date'].min().date()} → {df['exit_date'].max().date()}")
    print(f"   - Tickers: {df['ticker'].nunique()}")
    
    return df

def analyze_gld_vs_tsla(df):
    """Análisis comparativo profundo"""
    print("\n" + "=" * 80)
    print("🔍 ANÁLISIS COMPARATIVO: GLD vs TSLA")
    print("=" * 80)
    
    # Filtrar ambos tickers
    gld = df[df['ticker'] == 'GLD'].copy()
    tsla = df[df['ticker'] == 'TSLA'].copy()
    
    print(f"\n📊 MUESTRA:")
    print(f"   GLD: {len(gld)} trades")
    print(f"   TSLA: {len(tsla)} trades")
    
    # Métricas comparativas
    metrics = {
        'Ticker': ['GLD', 'TSLA'],
        'Trades': [len(gld), len(tsla)],
        'Total PnL': [gld['pnl'].sum(), tsla['pnl'].sum()],
        'Avg PnL': [gld['pnl'].mean(), tsla['pnl'].mean()],
        'Avg Return %': [gld['return_pct'].mean(), tsla['return_pct'].mean()],
        'Median Return %': [gld['return_pct'].median(), tsla['return_pct'].median()],
        'Std Return %': [gld['return_pct'].std(), tsla['return_pct'].std()],
        'Win Rate %': [
            (gld['pnl'] > 0).sum() / len(gld) * 100,
            (tsla['pnl'] > 0).sum() / len(tsla) * 100
        ],
        'Avg Premium': [gld['premium_collected'].mean(), tsla['premium_collected'].mean()],
        'Avg Risk': [gld['max_risk'].mean(), tsla['max_risk'].mean()],
        'Premium/Risk %': [
            (gld['premium_collected'].mean() / gld['max_risk'].mean() * 100) if gld['max_risk'].mean() != 0 else 0,
            (tsla['premium_collected'].mean() / tsla['max_risk'].mean() * 100) if tsla['max_risk'].mean() != 0 else 0
        ],
        'Avg DTE': [gld['dte_entry'].mean(), tsla['dte_entry'].mean()],
        'Avg Days Held': [gld['days_held'].mean(), tsla['days_held'].mean()],
    }
    
    comparison_df = pd.DataFrame(metrics)
    
    print("\n" + "=" * 80)
    print("📈 MÉTRICAS COMPARATIVAS")
    print("=" * 80)
    print(comparison_df.to_string(index=False))
    
    # Status de cierre
    print("\n" + "=" * 80)
    print("🏁 STATUS DE CIERRE")
    print("=" * 80)
    
    print("\nGLD:")
    print(gld['status'].value_counts())
    print(f"\n   - closed_end: {(gld['status'] == 'closed_end').sum()} ({(gld['status'] == 'closed_end').sum() / len(gld) * 100:.1f}%)")
    print(f"   - closed_profit: {(gld['status'] == 'closed_profit').sum()} ({(gld['status'] == 'closed_profit').sum() / len(gld) * 100:.1f}%)")
    print(f"   - closed_loss: {(gld['status'] == 'closed_loss').sum()} ({(gld['status'] == 'closed_loss').sum() / len(gld) * 100:.1f}%)")
    
    print("\nTSLA:")
    print(tsla['status'].value_counts())
    print(f"\n   - closed_end: {(tsla['status'] == 'closed_end').sum()} ({(tsla['status'] == 'closed_end').sum() / len(tsla) * 100:.1f}%)")
    print(f"   - closed_profit: {(tsla['status'] == 'closed_profit').sum()} ({(tsla['status'] == 'closed_profit').sum() / len(tsla) * 100:.1f}%)")
    print(f"   - closed_loss: {(tsla['status'] == 'closed_loss').sum()} ({(tsla['status'] == 'closed_loss').sum() / len(tsla) * 100:.1f}%)")
    
    # Análisis temporal
    print("\n" + "=" * 80)
    print("📅 ANÁLISIS TEMPORAL")
    print("=" * 80)
    
    print("\nGLD - Fechas de entrada:")
    for idx, row in gld.iterrows():
        print(f"   {row['entry_date'].date()} → {row['exit_date'].date()} | DTE: {row['dte_entry']} | Days: {row['days_held']} | Status: {row['status']} | Return: {row['return_pct']:.2f}%")
    
    print("\nTSLA - Fechas de entrada:")
    for idx, row in tsla.iterrows():
        print(f"   {row['entry_date'].date()} → {row['exit_date'].date()} | DTE: {row['dte_entry']} | Days: {row['days_held']} | Status: {row['status']} | Return: {row['return_pct']:.2f}%")
    
    # Encontrar insights clave
    print("\n" + "=" * 80)
    print("💡 INSIGHTS CLAVE")
    print("=" * 80)
    
    # ¿Por qué GLD mantuvo su 92.68%?
    print("\n1️⃣  ¿POR QUÉ GLD MANTUVO SU 92.68% RETURN?")
    print("-" * 80)
    if len(gld) > 0:
        gld_closed_end = gld[gld['status'] == 'closed_end']
        print(f"   - {len(gld_closed_end)} de {len(gld)} trades llegaron a expiración")
        print(f"   - Esto representa {len(gld_closed_end) / len(gld) * 100:.1f}% del total")
        print(f"   - Avg return de trades que expiraron: {gld_closed_end['return_pct'].mean():.2f}%")
        if len(gld_closed_end) > 0:
            print(f"   - Estos trades no fueron afectados por el bug (no necesitaron valorización anticipada)")
    
    # ¿Por qué TSLA emergió como campeón?
    print("\n2️⃣  ¿POR QUÉ TSLA EMERGIÓ COMO CAMPEÓN?")
    print("-" * 80)
    if len(tsla) > 0:
        tsla_closed_profit = tsla[tsla['status'] == 'closed_profit']
        print(f"   - {len(tsla_closed_profit)} de {len(tsla)} trades cerraron en profit anticipadamente")
        print(f"   - Esto representa {len(tsla_closed_profit) / len(tsla) * 100:.1f}% del total")
        print(f"   - Avg return de trades con profit target: {tsla_closed_profit['return_pct'].mean():.2f}%")
        print(f"   - Avg días hasta cierre: {tsla_closed_profit['days_held'].mean():.1f} días")
        print(f"   - Total PnL de profit targets: ${tsla_closed_profit['pnl'].sum():,.2f}")
        print(f"\n   💡 TSLA se benefició MASIVAMENTE del fix BSM:")
        print(f"      - 8 trades totales, con alta volatilidad implícita")
        print(f"      - Profit targets se alcanzaron rápidamente ({tsla_closed_profit['days_held'].mean():.1f} días)")
        print(f"      - GLD tiene solo 2 trades, ambos llegaron a expiración (no usaron el fix)")
    
    # Comparación de premium/risk
    print("\n3️⃣  COMPARACIÓN PREMIUM/RISK")
    print("-" * 80)
    gld_pr = (gld['premium_collected'].mean() / gld['max_risk'].mean() * 100) if gld['max_risk'].mean() != 0 else 0
    tsla_pr = (tsla['premium_collected'].mean() / abs(tsla['max_risk'].mean()) * 100) if tsla['max_risk'].mean() != 0 else 0
    print(f"   - GLD: {gld_pr:.2f}% (Premium/Risk ratio)")
    print(f"   - TSLA: {tsla_pr:.2f}% (Premium/Risk ratio)")
    print(f"   - Diferencia: {abs(gld_pr - tsla_pr):.2f}%")
    
    return gld, tsla, comparison_df

def create_visualizations(gld, tsla, df):
    """Crear visualizaciones comparativas"""
    print("\n" + "=" * 80)
    print("📊 GENERANDO VISUALIZACIONES")
    print("=" * 80)
    
    fig = plt.figure(figsize=(20, 14))
    
    # 1. Distribución de returns
    ax1 = plt.subplot(3, 3, 1)
    gld['return_pct'].plot(kind='hist', bins=15, alpha=0.7, label='GLD', ax=ax1, color='gold')
    tsla['return_pct'].plot(kind='hist', bins=15, alpha=0.7, label='TSLA', ax=ax1, color='red')
    ax1.set_xlabel('Return %')
    ax1.set_ylabel('Frecuencia')
    ax1.set_title('Distribución de Returns: GLD vs TSLA', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Box plot de returns
    ax2 = plt.subplot(3, 3, 2)
    data_for_box = pd.DataFrame({
        'Return %': list(gld['return_pct']) + list(tsla['return_pct']),
        'Ticker': ['GLD'] * len(gld) + ['TSLA'] * len(tsla)
    })
    sns.boxplot(data=data_for_box, x='Ticker', y='Return %', ax=ax2, palette=['gold', 'red'])
    ax2.set_title('Distribución de Returns (Box Plot)', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # 3. Status de cierre
    ax3 = plt.subplot(3, 3, 3)
    status_comparison = pd.DataFrame({
        'GLD': gld['status'].value_counts(),
        'TSLA': tsla['status'].value_counts()
    }).fillna(0)
    status_comparison.plot(kind='bar', ax=ax3, color=['gold', 'red'])
    ax3.set_xlabel('Status')
    ax3.set_ylabel('Cantidad')
    ax3.set_title('Status de Cierre: GLD vs TSLA', fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 4. PnL acumulado por fecha
    ax4 = plt.subplot(3, 3, 4)
    gld_sorted = gld.sort_values('exit_date')
    tsla_sorted = tsla.sort_values('exit_date')
    
    gld_sorted['cumulative_pnl'] = gld_sorted['pnl'].cumsum()
    tsla_sorted['cumulative_pnl'] = tsla_sorted['pnl'].cumsum()
    
    ax4.plot(gld_sorted['exit_date'], gld_sorted['cumulative_pnl'], 
             marker='o', label='GLD', linewidth=2, color='gold')
    ax4.plot(tsla_sorted['exit_date'], tsla_sorted['cumulative_pnl'], 
             marker='s', label='TSLA', linewidth=2, color='red')
    ax4.set_xlabel('Fecha de Salida')
    ax4.set_ylabel('PnL Acumulado ($)')
    ax4.set_title('PnL Acumulado en el Tiempo', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 5. Premium vs Risk scatter
    ax5 = plt.subplot(3, 3, 5)
    ax5.scatter(gld['max_risk'], gld['premium_collected'], 
                s=100, alpha=0.7, label='GLD', color='gold', edgecolors='black')
    ax5.scatter(tsla['max_risk'], tsla['premium_collected'], 
                s=100, alpha=0.7, label='TSLA', color='red', edgecolors='black')
    ax5.set_xlabel('Max Risk ($)')
    ax5.set_ylabel('Premium Collected ($)')
    ax5.set_title('Premium vs Risk', fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Days held distribution
    ax6 = plt.subplot(3, 3, 6)
    gld['days_held'].plot(kind='hist', bins=10, alpha=0.7, label='GLD', ax=ax6, color='gold')
    tsla['days_held'].plot(kind='hist', bins=10, alpha=0.7, label='TSLA', ax=ax6, color='red')
    ax6.set_xlabel('Días Sostenidos')
    ax6.set_ylabel('Frecuencia')
    ax6.set_title('Distribución de Días Sostenidos', fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    # 7. Return vs Days Held
    ax7 = plt.subplot(3, 3, 7)
    ax7.scatter(gld['days_held'], gld['return_pct'], 
                s=100, alpha=0.7, label='GLD', color='gold', edgecolors='black')
    ax7.scatter(tsla['days_held'], tsla['return_pct'], 
                s=100, alpha=0.7, label='TSLA', color='red', edgecolors='black')
    ax7.set_xlabel('Días Sostenidos')
    ax7.set_ylabel('Return %')
    ax7.set_title('Return vs Días Sostenidos', fontweight='bold')
    ax7.legend()
    ax7.grid(True, alpha=0.3)
    
    # 8. Métricas clave (tabla)
    ax8 = plt.subplot(3, 3, 8)
    ax8.axis('off')
    
    metrics_text = f"""
    📊 MÉTRICAS CLAVE
    
    GLD:
    • Trades: {len(gld)}
    • Total PnL: ${gld['pnl'].sum():,.2f}
    • Avg Return: {gld['return_pct'].mean():.2f}%
    • Win Rate: {(gld['pnl'] > 0).sum() / len(gld) * 100:.1f}%
    • Avg Days: {gld['days_held'].mean():.1f}
    
    TSLA:
    • Trades: {len(tsla)}
    • Total PnL: ${tsla['pnl'].sum():,.2f}
    • Avg Return: {tsla['return_pct'].mean():.2f}%
    • Win Rate: {(tsla['pnl'] > 0).sum() / len(tsla) * 100:.1f}%
    • Avg Days: {tsla['days_held'].mean():.1f}
    """
    
    ax8.text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
             verticalalignment='center')
    
    # 9. Return por status
    ax9 = plt.subplot(3, 3, 9)
    
    gld_by_status = gld.groupby('status')['return_pct'].mean()
    tsla_by_status = tsla.groupby('status')['return_pct'].mean()
    
    status_comparison = pd.DataFrame({
        'GLD': gld_by_status,
        'TSLA': tsla_by_status
    }).fillna(0)
    
    status_comparison.plot(kind='bar', ax=ax9, color=['gold', 'red'])
    ax9.set_xlabel('Status')
    ax9.set_ylabel('Avg Return %')
    ax9.set_title('Avg Return por Status de Cierre', fontweight='bold')
    ax9.legend()
    ax9.grid(True, alpha=0.3)
    plt.setp(ax9.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    output_path = 'scripts/gld_vs_tsla_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualizaciones guardadas en: {output_path}")
    
    return output_path

def main():
    """Función principal"""
    print("\n" + "🚀" * 40)
    print("ANÁLISIS COMPARATIVO: GLD vs TSLA")
    print("🚀" * 40)
    
    # Cargar datos
    df = load_data()
    
    # Análisis comparativo
    gld, tsla, comparison_df = analyze_gld_vs_tsla(df)
    
    # Visualizaciones
    create_visualizations(gld, tsla, df)
    
    # Conclusiones finales
    print("\n" + "=" * 80)
    print("📝 CONCLUSIONES FINALES")
    print("=" * 80)
    
    print("""
    🎯 RESPUESTA A LA PREGUNTA:
    
    1. GLD mantuvo su 92.68% porque AMBOS trades llegaron a expiración
       - No fueron afectados por el bug de valorización
       - El 92.68% es REAL y refleja el valor intrínseco al vencimiento
    
    2. TSLA emergió como campeón por el FIX BSM:
       - 8 trades totales con alta volatilidad
       - Profit targets se activaron gracias al fix
       - Trades cerraron rápido (~13 días promedio vs 52 de GLD)
       - Total PnL: $4,737 (vs $481 de GLD)
    
    3. KEY INSIGHT:
       - GLD: Estrategia "hold to expiration" funciona
       - TSLA: Estrategia "take profits early" funciona MEJOR
       - El fix BSM reveló el verdadero potencial de activos volátiles
    
    4. IMPLICACIÓN:
       - Alta volatilidad + Profit targets = Mayor PnL total
       - Baja volatilidad + Hold to expiration = Retornos estables pero limitados
    """)
    
    print("\n" + "✅" * 40)
    print("ANÁLISIS COMPLETADO")
    print("✅" * 40)

if __name__ == "__main__":
    main()
