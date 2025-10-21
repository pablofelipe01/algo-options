"""
Test del Backtester Multi-Ticker con 10 TICKERS
Ejecutar desde: ~/Desktop/otions-data/scripts/

Este script prueba el backtester con TODOS los tickers disponibles.
Objetivo: Generar dataset masivo para Machine Learning.
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio scripts/ al path para poder importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.backtester_multi import BacktestConfig, BacktestEngine, BacktestVisualizer


def main():
    """Test del backtester con 10 tickers."""
    print("🧪 Testing Backtester con 10 TICKERS - Dataset Masivo\n")
    
    # Configuración con TODOS los tickers disponibles
    config = BacktestConfig(
        start_date=datetime(2025, 8, 22),  # Todo el rango disponible
        end_date=datetime(2025, 10, 20),
        initial_capital=20000,  # Capital inicial realista ($20K)
        max_positions=30,  # 🆕 Hasta 30 posiciones simultáneas
        max_positions_per_ticker=2,  # Mantener límite por ticker
        tickers=[
            # ETFs
            'SPY',   # S&P 500
            'QQQ',   # Nasdaq 100
            'IWM',   # Russell 2000
            # Tech Giants
            'AAPL',  # Apple
            'MSFT',  # Microsoft
            'NVDA',  # NVIDIA
            'TSLA',  # Tesla
            'AMZN',  # Amazon
            # Commodities
            'GLD',   # Gold
            'SLV'    # Silver
        ],
        strategies=['iron_condor']
    )
    
    print("="*70)
    print("🎯 CONFIGURACIÓN DEL BACKTEST")
    print("="*70)
    print(f"  • Período: {config.start_date.date()} → {config.end_date.date()}")
    print(f"  • Capital: ${config.initial_capital:,.0f}")
    print(f"  • Tickers: {len(config.tickers)} tickers")
    print(f"    - ETFs: SPY, QQQ, IWM")
    print(f"    - Tech: AAPL, MSFT, NVDA, TSLA, AMZN")
    print(f"    - Commodities: GLD, SLV")
    print(f"  • Máx posiciones totales: {config.max_positions}")
    print(f"  • Máx posiciones por ticker: {config.max_positions_per_ticker}")
    print(f"  • Estrategias: {config.strategies}")
    
    # Crear engine
    print("\n" + "="*70)
    print("🔧 INICIALIZANDO ENGINE")
    print("="*70)
    engine = BacktestEngine(config)
    print(f"\n✅ Engine creado con {len(engine.valid_tickers)}/{len(config.tickers)} tickers válidos")
    
    if len(engine.valid_tickers) < len(config.tickers):
        print("\n⚠️  Tickers sin datos:")
        missing = set(config.tickers) - set(engine.valid_tickers)
        for ticker in missing:
            print(f"    • {ticker}")
    
    # Ejecutar backtest
    print("\n" + "="*70)
    print("🚀 EJECUTANDO BACKTEST")
    print("="*70)
    
    try:
        results = engine.run_multi_ticker_backtest()
        
        # ====================================================================
        # RESULTADOS DETALLADOS
        # ====================================================================
        
        print("\n" + "="*70)
        print("📊 RESULTADOS DEL BACKTEST - 10 TICKERS")
        print("="*70)
        
        summary = results['summary']
        
        # === RESUMEN EJECUTIVO ===
        print(f"\n💰 RESUMEN EJECUTIVO:")
        print(f"  • Capital inicial: ${summary['capital_inicial']:,.2f}")
        print(f"  • Capital final: ${summary['capital_final']:,.2f}")
        print(f"  • Retorno total: {summary['total_return_pct']:+.2f}%")
        print(f"  • PnL total: ${summary['total_pnl']:+,.2f}")
        print(f"  • Total operaciones: {summary['total_trades']}")
        
        # === MÉTRICAS DE RENDIMIENTO ===
        print(f"\n📈 MÉTRICAS DE RENDIMIENTO:")
        print(f"  • Tasa de éxito: {summary['win_rate']:.1%}")
        print(f"  • Retorno promedio: {summary['avg_return_pct']:.2f}%")
        print(f"  • Ganancia promedio: {summary['avg_winner_pct']:.2f}%")
        print(f"  • Pérdida promedia: {summary['avg_loser_pct']:.2f}%")
        print(f"  • Días promedio en posición: {summary['avg_days_held']:.1f}")
        
        # === MÉTRICAS DE RIESGO ===
        print(f"\n📊 MÉTRICAS DE RIESGO:")
        print(f"  • Profit Factor: {summary['profit_factor']:.2f}")
        print(f"  • Expectancy: {summary['expectancy']:.2f}%")
        print(f"  • Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
        print(f"  • Max Drawdown: ${summary['max_drawdown']:,.2f} ({summary['max_drawdown_pct']:.2f}%)")
        
        # === ANÁLISIS POR TICKER ===
        if 'by_ticker' in results and results['by_ticker']:
            print(f"\n🎯 ANÁLISIS POR TICKER:")
            print("="*70)
            
            # Crear lista ordenada por PnL
            ticker_list = [(ticker, metrics) for ticker, metrics in results['by_ticker'].items()]
            ticker_list.sort(key=lambda x: x[1]['total_pnl'], reverse=True)
            
            print(f"\n{'Rank':<6} {'Ticker':<8} {'Trades':<8} {'Win%':<8} {'Avg Return':<12} {'Total PnL':<12}")
            print("-"*70)
            
            for i, (ticker, metrics) in enumerate(ticker_list, 1):
                print(f"{i:<6} {ticker:<8} {metrics['trades']:<8} "
                      f"{metrics['win_rate']*100:>6.1f}%  "
                      f"{metrics['avg_return']:>10.2f}%  "
                      f"${metrics['total_pnl']:>10,.2f}")
            
            # Top 3 y Bottom 3
            print(f"\n🏆 TOP 3 TICKERS (por PnL):")
            for i, (ticker, metrics) in enumerate(ticker_list[:3], 1):
                print(f"  {i}. {ticker}: ${metrics['total_pnl']:+,.2f} "
                      f"({metrics['trades']} trades, {metrics['win_rate']:.1%} win rate)")
            
            if len(ticker_list) > 3:
                print(f"\n⚠️  BOTTOM 3 TICKERS:")
                for i, (ticker, metrics) in enumerate(ticker_list[-3:], 1):
                    print(f"  {i}. {ticker}: ${metrics['total_pnl']:+,.2f} "
                          f"({metrics['trades']} trades, {metrics['win_rate']:.1%} win rate)")
        
        # === ANÁLISIS POR CATEGORÍA ===
        if 'by_ticker' in results and results['by_ticker']:
            print(f"\n📊 ANÁLISIS POR CATEGORÍA:")
            print("="*70)
            
            # Categorizar tickers
            categories = {
                'ETFs': ['SPY', 'QQQ', 'IWM'],
                'Tech': ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN'],
                'Commodities': ['GLD', 'SLV']
            }
            
            for category, tickers in categories.items():
                category_trades = 0
                category_pnl = 0
                category_premium = 0
                
                for ticker in tickers:
                    if ticker in results['by_ticker']:
                        metrics = results['by_ticker'][ticker]
                        category_trades += metrics['trades']
                        category_pnl += metrics['total_pnl']
                        category_premium += metrics['total_premium']
                
                if category_trades > 0:
                    print(f"\n  {category}:")
                    print(f"    • Trades: {category_trades}")
                    print(f"    • PnL total: ${category_pnl:+,.2f}")
                    print(f"    • Premium total: ${category_premium:,.2f}")
                    print(f"    • PnL promedio/trade: ${category_pnl/category_trades:+,.2f}")
        
        # === DISTRIBUCIÓN DE OPERACIONES ===
        if 'raw_data' in results and len(results['raw_data']) > 0:
            df_trades = results['raw_data']
            
            print(f"\n📈 DISTRIBUCIÓN DE OPERACIONES:")
            print("="*70)
            
            # Por status
            print(f"\n  Por status:")
            status_counts = df_trades['status'].value_counts()
            for status, count in status_counts.items():
                pct = (count / len(df_trades)) * 100
                print(f"    • {status}: {count} ({pct:.1f}%)")
            
            # Por DTE bucket
            if 'dte_bucket' in df_trades.columns:
                print(f"\n  Por DTE bucket:")
                dte_counts = df_trades['dte_bucket'].value_counts()
                for bucket, count in dte_counts.items():
                    pct = (count / len(df_trades)) * 100
                    avg_return = df_trades[df_trades['dte_bucket'] == bucket]['return_pct'].mean()
                    print(f"    • {bucket}: {count} ({pct:.1f}%), Avg: {avg_return:.2f}%")
        
        # === EQUITY CURVE ===
        if 'equity_curve' in results and len(results['equity_curve']) > 0:
            eq_df = results['equity_curve']
            print(f"\n📈 EQUITY CURVE:")
            print("="*70)
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
            print(f"  • Cambio total: {change_pct:+.2f}%")
            
            # Calcular volatilidad
            returns = eq_df['equity'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5) * 100  # Anualizada
            print(f"  • Volatilidad anualizada: {volatility:.2f}%")
        
        # === MUESTRA DE TRADES ===
        if engine.closed_positions and len(engine.closed_positions) > 0:
            print(f"\n📋 MUESTRA DE TRADES (primeras 15):")
            print("="*70)
            
            for i, pos in enumerate(engine.closed_positions[:15], 1):
                symbol = "✅" if pos.pnl > 0 else "❌"
                print(f"  {i}. {symbol} {pos.ticker} {pos.strategy_name}")
                print(f"     Entrada: {pos.entry_date.date()}, DTE: {pos.dte_at_entry}")
                print(f"     Salida: {pos.exit_date.date() if pos.exit_date else 'N/A'}, Días: {pos.days_held}")
                print(f"     Crédito: ${pos.premium_collected:.2f}, PnL: ${pos.pnl:+,.2f}")
                print(f"     Retorno: {(pos.pnl/abs(pos.max_risk))*100:.2f}%, Status: {pos.status}")
                print()
            
            if len(engine.closed_positions) > 15:
                print(f"  ... y {len(engine.closed_positions) - 15} trades más")
        
        print("\n" + "="*70)
        print("✅ BACKTEST COMPLETADO EXITOSAMENTE")
        print("="*70)
        
        # === GENERAR VISUALIZACIONES ===
        print("\n📊 Generando visualizaciones...")
        visualizer = BacktestVisualizer(results)
        
        # Guardar gráficos
        save_path = Path(__file__).parent / "backtest_10_tickers_results.png"
        visualizer.plot_all(save_path=str(save_path))
        
        # === GUARDAR DATASET PARA ML ===
        print("\n💾 Guardando dataset para Machine Learning...")
        
        if 'raw_data' in results and len(results['raw_data']) > 0:
            dataset_path = Path(__file__).parent / "ml_dataset_10_tickers.csv"
            results['raw_data'].to_csv(dataset_path, index=False)
            print(f"  ✅ Dataset guardado: {dataset_path}")
            print(f"  📊 Total de registros: {len(results['raw_data'])}")
            print(f"  📋 Columnas: {list(results['raw_data'].columns)}")
        
        # === SUMMARY FINAL ===
        print("\n" + "="*70)
        print("🎯 RESUMEN FINAL")
        print("="*70)
        print(f"  • Tickers procesados: {len(engine.valid_tickers)}")
        print(f"  • Operaciones totales: {summary['total_trades']}")
        print(f"  • Retorno total: {summary['total_return_pct']:+.2f}%")
        print(f"  • Win rate: {summary['win_rate']:.1%}")
        print(f"  • Sharpe ratio: {summary['sharpe_ratio']:.2f}")
        print(f"  • Dataset guardado: ✅")
        print(f"  • Visualizaciones: ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante backtest: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Sistema de backtesting multi-ticker con 10 tickers completado!")
        print("🎯 Dataset listo para Machine Learning")
        print("\n📁 Archivos generados:")
        print("   • backtest_10_tickers_results.png (visualizaciones)")
        print("   • ml_dataset_10_tickers.csv (dataset para ML)")
    else:
        print("\n⚠️  Revisar errores antes de continuar")