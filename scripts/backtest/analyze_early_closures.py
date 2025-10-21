#!/usr/bin/env python3
"""
Análisis de Cierres Anticipados
Estudiar los 24 trades que cerraron anticipadamente vs los 20 que expiraron
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_data():
    """Cargar dataset"""
    print("=" * 80)
    print("📊 CARGANDO DATASET")
    print("=" * 80)
    
    df = pd.read_csv('scripts/ml_dataset_10_tickers.csv')
    df['entry_date'] = pd.to_datetime(df['entry_date'])
    df['exit_date'] = pd.to_datetime(df['exit_date'])
    
    print(f"\n✅ Dataset cargado: {len(df)} trades")
    print(f"   Status distribution: {df['status'].value_counts().to_dict()}")
    
    return df

def analyze_early_closures(df):
    """Análisis de cierres anticipados"""
    print("\n" + "=" * 80)
    print("🎯 ANÁLISIS DE CIERRES ANTICIPADOS")
    print("=" * 80)
    
    # Separar por tipo de cierre
    closed_profit = df[df['status'] == 'closed_profit'].copy()
    closed_loss = df[df['status'] == 'closed_loss'].copy()
    closed_end = df[df['status'] == 'closed_end'].copy()
    
    early_closures = pd.concat([closed_profit, closed_loss])
    
    print(f"\n📊 DISTRIBUCIÓN:")
    print(f"   - Closed Profit: {len(closed_profit)} ({len(closed_profit)/len(df)*100:.1f}%)")
    print(f"   - Closed Loss: {len(closed_loss)} ({len(closed_loss)/len(df)*100:.1f}%)")
    print(f"   - Closed End: {len(closed_end)} ({len(closed_end)/len(df)*100:.1f}%)")
    print(f"   - Total Early Closures: {len(early_closures)} ({len(early_closures)/len(df)*100:.1f}%)")
    
    # Métricas comparativas
    print("\n" + "=" * 80)
    print("📈 MÉTRICAS COMPARATIVAS")
    print("=" * 80)
    
    comparison = pd.DataFrame({
        'Metric': [
            'Trades',
            'Total PnL',
            'Avg PnL',
            'Avg Return %',
            'Median Return %',
            'Std Return %',
            'Avg Days Held',
            'Avg Premium',
            'Avg Risk',
            'Premium/Risk %'
        ],
        'Closed Profit': [
            len(closed_profit),
            closed_profit['pnl'].sum(),
            closed_profit['pnl'].mean(),
            closed_profit['return_pct'].mean(),
            closed_profit['return_pct'].median(),
            closed_profit['return_pct'].std(),
            closed_profit['days_held'].mean(),
            closed_profit['premium_collected'].mean(),
            closed_profit['max_risk'].mean(),
            (closed_profit['premium_collected'].mean() / abs(closed_profit['max_risk'].mean()) * 100) if closed_profit['max_risk'].mean() != 0 else 0
        ],
        'Closed Loss': [
            len(closed_loss),
            closed_loss['pnl'].sum(),
            closed_loss['pnl'].mean(),
            closed_loss['return_pct'].mean(),
            closed_loss['return_pct'].median(),
            closed_loss['return_pct'].std(),
            closed_loss['days_held'].mean(),
            closed_loss['premium_collected'].mean(),
            closed_loss['max_risk'].mean(),
            (closed_loss['premium_collected'].mean() / closed_loss['max_risk'].mean() * 100) if closed_loss['max_risk'].mean() != 0 else 0
        ],
        'Closed End': [
            len(closed_end),
            closed_end['pnl'].sum(),
            closed_end['pnl'].mean(),
            closed_end['return_pct'].mean(),
            closed_end['return_pct'].median(),
            closed_end['return_pct'].std(),
            closed_end['days_held'].mean(),
            closed_end['premium_collected'].mean(),
            closed_end['max_risk'].mean(),
            (closed_end['premium_collected'].mean() / abs(closed_end['max_risk'].mean()) * 100) if closed_end['max_risk'].mean() != 0 else 0
        ]
    })
    
    print("\n" + comparison.to_string(index=False))
    
    # Análisis por ticker
    print("\n" + "=" * 80)
    print("📦 ANÁLISIS POR TICKER")
    print("=" * 80)
    
    ticker_analysis = df.groupby(['ticker', 'status']).agg({
        'pnl': ['count', 'sum', 'mean'],
        'return_pct': 'mean',
        'days_held': 'mean'
    }).round(2)
    
    print("\n" + ticker_analysis.to_string())
    
    # ¿Qué tickers se beneficiaron más del fix?
    print("\n" + "=" * 80)
    print("🚀 ¿QUÉ TICKERS SE BENEFICIARON MÁS DEL FIX BSM?")
    print("=" * 80)
    
    early_closure_by_ticker = early_closures.groupby('ticker').agg({
        'pnl': ['count', 'sum', 'mean'],
        'return_pct': 'mean',
        'days_held': 'mean'
    }).round(2)
    early_closure_by_ticker.columns = ['Trades', 'Total_PnL', 'Avg_PnL', 'Avg_Return%', 'Avg_Days']
    early_closure_by_ticker = early_closure_by_ticker.sort_values('Total_PnL', ascending=False)
    
    print("\n" + early_closure_by_ticker.to_string())
    
    # Análisis por DTE bucket
    print("\n" + "=" * 80)
    print("📊 ANÁLISIS POR DTE BUCKET")
    print("=" * 80)
    
    dte_analysis = df.groupby(['dte_bucket', 'status']).agg({
        'pnl': ['count', 'sum', 'mean'],
        'return_pct': 'mean',
        'days_held': 'mean'
    }).round(2)
    
    print("\n" + dte_analysis.to_string())
    
    # Patrones temporales
    print("\n" + "=" * 80)
    print("⏱️  PATRONES TEMPORALES")
    print("=" * 80)
    
    print(f"\n📊 CLOSED PROFIT ({len(closed_profit)} trades):")
    print(f"   - Avg días hasta cierre: {closed_profit['days_held'].mean():.1f}")
    print(f"   - Min días: {closed_profit['days_held'].min()}")
    print(f"   - Max días: {closed_profit['days_held'].max()}")
    print(f"   - Median días: {closed_profit['days_held'].median():.1f}")
    
    print(f"\n📊 CLOSED LOSS ({len(closed_loss)} trades):")
    print(f"   - Avg días hasta cierre: {closed_loss['days_held'].mean():.1f}")
    print(f"   - Min días: {closed_loss['days_held'].min()}")
    print(f"   - Max días: {closed_loss['days_held'].max()}")
    print(f"   - Median días: {closed_loss['days_held'].median():.1f}")
    
    print(f"\n📊 CLOSED END ({len(closed_end)} trades):")
    print(f"   - Avg días hasta expiración: {closed_end['days_held'].mean():.1f}")
    print(f"   - Min días: {closed_end['days_held'].min()}")
    print(f"   - Max días: {closed_end['days_held'].max()}")
    print(f"   - Median días: {closed_end['days_held'].median():.1f}")
    
    # Key insights
    print("\n" + "=" * 80)
    print("💡 KEY INSIGHTS")
    print("=" * 80)
    
    print(f"""
    1️⃣  EFICIENCIA DE CAPITAL:
       - Early closures: {early_closures['days_held'].mean():.1f} días promedio
       - Hold to expiration: {closed_end['days_held'].mean():.1f} días promedio
       - Diferencia: {closed_end['days_held'].mean() - early_closures['days_held'].mean():.1f} días
       - Early closures liberan capital {closed_end['days_held'].mean() / early_closures['days_held'].mean():.1f}x más rápido
    
    2️⃣  PROFIT TARGETS FUNCIONAN:
       - {len(closed_profit)} trades cerraron en profit
       - Avg return: {closed_profit['return_pct'].mean():.2f}%
       - Total PnL: ${closed_profit['pnl'].sum():,.2f}
       - Representa {closed_profit['pnl'].sum() / df['pnl'].sum() * 100:.1f}% del PnL total
    
    3️⃣  STOP LOSSES PROTEGEN:
       - {len(closed_loss)} trades cerraron en loss
       - Avg loss: {closed_loss['return_pct'].mean():.2f}%
       - Total pérdida: ${closed_loss['pnl'].sum():,.2f}
       - Evitaron pérdidas mayores al cerrar en {closed_loss['days_held'].mean():.1f} días
    
    4️⃣  TICKERS MÁS BENEFICIADOS:
       - {early_closure_by_ticker.index[0]}: ${early_closure_by_ticker.iloc[0]['Total_PnL']:,.2f} PnL ({early_closure_by_ticker.iloc[0]['Trades']:.0f} trades)
       - {early_closure_by_ticker.index[1] if len(early_closure_by_ticker) > 1 else 'N/A'}: ${early_closure_by_ticker.iloc[1]['Total_PnL']:,.2f} PnL ({early_closure_by_ticker.iloc[1]['Trades']:.0f} trades)
       - {early_closure_by_ticker.index[2] if len(early_closure_by_ticker) > 2 else 'N/A'}: ${early_closure_by_ticker.iloc[2]['Total_PnL']:,.2f} PnL ({early_closure_by_ticker.iloc[2]['Trades']:.0f} trades)
    """)
    
    return closed_profit, closed_loss, closed_end, early_closures

def create_visualizations(df, closed_profit, closed_loss, closed_end, early_closures):
    """Crear visualizaciones"""
    print("\n" + "=" * 80)
    print("📊 GENERANDO VISUALIZACIONES")
    print("=" * 80)
    
    fig = plt.figure(figsize=(20, 14))
    
    # 1. Distribución de status
    ax1 = plt.subplot(3, 3, 1)
    status_counts = df['status'].value_counts()
    colors = {'closed_profit': 'green', 'closed_loss': 'red', 'closed_end': 'gray'}
    bars = ax1.bar(status_counts.index, status_counts.values, 
                   color=[colors.get(x, 'blue') for x in status_counts.index])
    ax1.set_xlabel('Status')
    ax1.set_ylabel('Cantidad de Trades')
    ax1.set_title('Distribución de Status de Cierre', fontweight='bold', fontsize=12)
    
    # Agregar porcentajes
    for i, (idx, val) in enumerate(status_counts.items()):
        ax1.text(i, val + 0.5, f'{val}\n({val/len(df)*100:.1f}%)', 
                ha='center', va='bottom', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 2. Days held por status
    ax2 = plt.subplot(3, 3, 2)
    data_for_box = pd.DataFrame({
        'Days Held': list(closed_profit['days_held']) + list(closed_loss['days_held']) + list(closed_end['days_held']),
        'Status': ['Profit'] * len(closed_profit) + ['Loss'] * len(closed_loss) + ['Expiration'] * len(closed_end)
    })
    sns.boxplot(data=data_for_box, x='Status', y='Days Held', ax=ax2,
                palette=['green', 'red', 'gray'])
    ax2.set_title('Días Sostenidos por Status', fontweight='bold', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # 3. Return distribution por status
    ax3 = plt.subplot(3, 3, 3)
    closed_profit['return_pct'].hist(bins=15, alpha=0.7, label='Profit', ax=ax3, color='green')
    closed_loss['return_pct'].hist(bins=15, alpha=0.7, label='Loss', ax=ax3, color='red')
    closed_end['return_pct'].hist(bins=15, alpha=0.7, label='Expiration', ax=ax3, color='gray')
    ax3.set_xlabel('Return %')
    ax3.set_ylabel('Frecuencia')
    ax3.set_title('Distribución de Returns por Status', fontweight='bold', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Early closures por ticker
    ax4 = plt.subplot(3, 3, 4)
    ticker_status = df.groupby(['ticker', 'status']).size().unstack(fill_value=0)
    ticker_status.plot(kind='bar', stacked=True, ax=ax4, 
                      color=['green', 'red', 'gray'])
    ax4.set_xlabel('Ticker')
    ax4.set_ylabel('Cantidad de Trades')
    ax4.set_title('Status de Cierre por Ticker', fontweight='bold', fontsize=12)
    ax4.legend(title='Status', labels=['Profit', 'Loss', 'Expiration'])
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax4.grid(True, alpha=0.3)
    
    # 5. PnL acumulado por status
    ax5 = plt.subplot(3, 3, 5)
    
    # Calcular PnL por status
    profit_pnl = closed_profit['pnl'].sum()
    loss_pnl = closed_loss['pnl'].sum()
    end_pnl = closed_end['pnl'].sum()
    
    bars = ax5.bar(['Profit\nTargets', 'Stop\nLosses', 'Expiration'],
                   [profit_pnl, loss_pnl, end_pnl],
                   color=['green', 'red', 'gray'])
    ax5.set_ylabel('Total PnL ($)')
    ax5.set_title('PnL Total por Status de Cierre', fontweight='bold', fontsize=12)
    ax5.axhline(y=0, color='black', linestyle='--', linewidth=1)
    
    # Agregar valores
    for bar, val in zip(bars, [profit_pnl, loss_pnl, end_pnl]):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                f'${val:,.0f}',
                ha='center', va='bottom' if val > 0 else 'top',
                fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # 6. Return vs Days Held scatter
    ax6 = plt.subplot(3, 3, 6)
    ax6.scatter(closed_profit['days_held'], closed_profit['return_pct'],
               s=100, alpha=0.6, label='Profit', color='green', edgecolors='black')
    ax6.scatter(closed_loss['days_held'], closed_loss['return_pct'],
               s=100, alpha=0.6, label='Loss', color='red', edgecolors='black')
    ax6.scatter(closed_end['days_held'], closed_end['return_pct'],
               s=100, alpha=0.6, label='Expiration', color='gray', edgecolors='black')
    ax6.set_xlabel('Días Sostenidos')
    ax6.set_ylabel('Return %')
    ax6.set_title('Return vs Días Sostenidos', fontweight='bold', fontsize=12)
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    # 7. DTE bucket analysis
    ax7 = plt.subplot(3, 3, 7)
    dte_status = df.groupby(['dte_bucket', 'status']).size().unstack(fill_value=0)
    dte_status.plot(kind='bar', stacked=True, ax=ax7,
                        color=['green', 'red', 'gray'])
    ax7.set_xlabel('DTE Bucket')
    ax7.set_ylabel('Cantidad de Trades')
    ax7.set_title('Status de Cierre por DTE Bucket', fontweight='bold', fontsize=12)
    ax7.legend(title='Status', labels=['Profit', 'Loss', 'Expiration'])
    plt.setp(ax7.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax7.grid(True, alpha=0.3)
    
    # 8. Timeline de cierres
    ax8 = plt.subplot(3, 3, 8)
    
    # Ordenar por fecha de salida
    for status, color, label in [('closed_profit', 'green', 'Profit'),
                                  ('closed_loss', 'red', 'Loss'),
                                  ('closed_end', 'gray', 'Expiration')]:
        data = df[df['status'] == status].sort_values('exit_date')
        if len(data) > 0:
            ax8.scatter(data['exit_date'], data['return_pct'],
                       s=100, alpha=0.6, label=label, color=color,
                       edgecolors='black')
    
    ax8.set_xlabel('Fecha de Salida')
    ax8.set_ylabel('Return %')
    ax8.set_title('Timeline de Cierres', fontweight='bold', fontsize=12)
    ax8.legend()
    ax8.grid(True, alpha=0.3)
    plt.setp(ax8.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 9. Tabla resumen
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    summary_text = f"""
    📊 RESUMEN EJECUTIVO
    
    EARLY CLOSURES ({len(early_closures)} trades):
    • Profit Targets: {len(closed_profit)} ({len(closed_profit)/len(df)*100:.1f}%)
    • Stop Losses: {len(closed_loss)} ({len(closed_loss)/len(df)*100:.1f}%)
    • Total PnL: ${early_closures['pnl'].sum():,.2f}
    • Avg días: {early_closures['days_held'].mean():.1f}
    
    HOLD TO EXPIRATION ({len(closed_end)} trades):
    • Cantidad: {len(closed_end)} ({len(closed_end)/len(df)*100:.1f}%)
    • Total PnL: ${closed_end['pnl'].sum():,.2f}
    • Avg días: {closed_end['days_held'].mean():.1f}
    
    IMPACTO DEL FIX BSM:
    • {len(early_closures)/len(df)*100:.1f}% de trades ahora cierran anticipadamente
    • Liberación de capital {closed_end['days_held'].mean() / early_closures['days_held'].mean():.1f}x más rápida
    • Profit targets generaron ${closed_profit['pnl'].sum():,.2f}
    """
    
    ax9.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
            verticalalignment='center')
    
    plt.tight_layout()
    
    output_path = 'scripts/visualizations/early_closures_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualizaciones guardadas en: {output_path}")
    
    return output_path

def main():
    """Función principal"""
    print("\n" + "🚀" * 40)
    print("ANÁLISIS DE CIERRES ANTICIPADOS")
    print("🚀" * 40)
    
    # Cargar datos
    df = load_data()
    
    # Análisis
    closed_profit, closed_loss, closed_end, early_closures = analyze_early_closures(df)
    
    # Visualizaciones
    create_visualizations(df, closed_profit, closed_loss, closed_end, early_closures)
    
    print("\n" + "✅" * 40)
    print("ANÁLISIS COMPLETADO")
    print("✅" * 40)

if __name__ == "__main__":
    main()
