"""
Test del Loop Principal de Backtesting
Ejecutar desde: ~/Desktop/otions-data/scripts/
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from strategies.backtester import BacktestConfig, BacktestEngine
from strategies.backtester import BacktestVisualizer  # Nueva importación


def main():
    """Test del loop principal de backtesting."""
    print("🧪 Testing Loop Principal de Backtesting\n")
    
    # Configuración simple para test
    config = BacktestConfig(
        start_date=datetime(2025, 8, 22),  # Todo el rango disponible
        end_date=datetime(2025, 10, 20),
        initial_capital=50000,
        max_positions=3,  # Más posiciones para test
        strategies=['iron_condor']
    )
    
    print("Configuración del test:")
    print(f"  • Período: {config.start_date.date()} → {config.end_date.date()}")
    print(f"  • Capital: ${config.initial_capital:,.0f}")
    print(f"  • Máx posiciones: {config.max_positions}")
    print(f"  • Estrategias: {config.strategies}")
    
    # Crear engine
    print("\n1. Inicializando BacktestEngine...")
    engine = BacktestEngine(config)
    print(f"   ✅ Engine creado")
    
    # Ejecutar backtest
    print("\n2. Ejecutando backtest...")
    try:
        results = engine.run_backtest(ticker='SPY')
        
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL BACKTEST")
        print("="*60)
        
        summary = results['summary']
        
        print(f"\n💰 RESUMEN FINANCIERO:")
        print(f"  • Capital inicial: ${summary['capital_inicial']:,.2f}")
        print(f"  • Capital final: ${summary['capital_final']:,.2f}")
        print(f"  • Retorno total: {summary['total_return_pct']:+.2f}%")
        print(f"  • PnL total: ${summary['total_pnl']:+,.2f}")
        
        print(f"\n📈 MÉTRICAS DE TRADING:")
        print(f"  • Total operaciones: {summary['total_trades']}")
        print(f"  • Tasa de éxito: {summary['win_rate']:.1%}")
        print(f"  • Retorno promedio: {summary['avg_return_pct']:.2f}%")
        print(f"  • Ganancia promedio: {summary['avg_winner_pct']:.2f}%")
        print(f"  • Pérdida promedia: {summary['avg_loser_pct']:.2f}%")
        print(f"  • Días promedio: {summary['avg_days_held']:.1f}")
        
        print(f"\n📊 MÉTRICAS AVANZADAS:")
        print(f"  • Profit Factor: {summary['profit_factor']:.2f}")
        print(f"  • Expectancy: {summary['expectancy']:.2f}%")
        print(f"  • Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
        print(f"  • Max Drawdown: ${summary['max_drawdown']:,.2f} ({summary['max_drawdown_pct']:.2f}%)")
        
        print(f"\n💵 CAPITAL UTILIZADO:")
        print(f"  • Premium total: ${summary['total_premium']:,.2f}")
        print(f"  • Riesgo total: ${summary['total_risk']:,.2f}")
        
        # Métricas por estrategia
        if 'by_strategy' in results and results['by_strategy']:
            print(f"\n📋 POR ESTRATEGIA:")
            for strategy, metrics in results['by_strategy'].items():
                print(f"\n  {strategy}:")
                print(f"    • Operaciones: {metrics['trades']}")
                print(f"    • Win rate: {metrics['win_rate']:.1%}")
                print(f"    • Retorno promedio: {metrics['avg_return']:.2f}%")
                print(f"    • PnL total: ${metrics['total_pnl']:,.2f}")
        
        # Métricas por DTE
        if 'by_dte' in results and results['by_dte']:
            print(f"\n📅 POR DTE:")
            for dte_bucket, metrics in results['by_dte'].items():
                print(f"\n  {dte_bucket}:")
                print(f"    • Operaciones: {metrics['trades']}")
                print(f"    • Win rate: {metrics['win_rate']:.1%}")
                print(f"    • Retorno promedio: {metrics['avg_return']:.2f}%")
        
        # Ver equity curve
        if 'equity_curve' in results and len(results['equity_curve']) > 0:
            eq_df = results['equity_curve']
            print(f"\n📈 EQUITY CURVE:")
            print(f"  • Días registrados: {len(eq_df)}")
            first_equity = eq_df['equity'].iloc[0]
            last_equity = eq_df['equity'].iloc[-1]
            max_equity = eq_df['equity'].max()
            min_equity = eq_df['equity'].min()
            print(f"  • Equity inicial: ${first_equity:,.2f}")
            print(f"  • Equity final: ${last_equity:,.2f}")
            print(f"  • Equity máximo: ${max_equity:,.2f}")
            print(f"  • Equity mínimo: ${min_equity:,.2f}")
            change_pct = ((last_equity - first_equity) / first_equity) * 100
            print(f"  • Cambio: {change_pct:+.2f}%")
        
        # Ver detalle de posiciones cerradas
        if engine.closed_positions and len(engine.closed_positions) > 0:
            print(f"\n📋 Posiciones Cerradas:")
            for i, pos in enumerate(engine.closed_positions[:5], 1):  # Solo primeras 5
                print(f"\n  Posición {i}:")
                print(f"    • Estrategia: {pos.strategy_name}")
                print(f"    • Entrada: {pos.entry_date.date()}, DTE: {pos.dte_at_entry}")
                print(f"    • Salida: {pos.exit_date.date() if pos.exit_date else 'N/A'}, Días: {pos.days_held}")
                print(f"    • Crédito: ${pos.premium_collected:.2f}")
                print(f"    • PnL: ${pos.pnl:.2f}")
                print(f"    • Status: {pos.status}")
            
            if len(engine.closed_positions) > 5:
                print(f"\n  ... y {len(engine.closed_positions) - 5} posiciones más")
        
        print("\n" + "="*60)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("="*60)
        
        # Crear visualizaciones
        print("\n📊 Generando visualizaciones...")
        visualizer = BacktestVisualizer(results)
        
        # Guardar gráficos
        save_path = Path(__file__).parent / "backtest_results.png"
        visualizer.plot_all(save_path=str(save_path))
        
    except Exception as e:
        print(f"\n❌ Error durante backtest: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Sistema de backtesting completo y funcional!")
        print("   • Métricas profesionales ✅")
        print("   • Visualizaciones ✅")
        print("   • Integración con estrategias ✅")
    else:
        print("\n⚠️  Corregir errores antes de continuar")