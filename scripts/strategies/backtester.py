"""
Backtesting Engine para Estrategias de Opciones
Integrado con IronCondor, CoveredCall y datos históricos reales de Polygon.io

Autor: Sistema de Trading Algorítmico
Fecha: Parte 5 - Backtesting
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Imports de nuestros módulos existentes
import sys
from pathlib import Path

# Agregar el directorio strategies al path para imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

try:
    from base import StrategyBase, Position
    from iron_condor import IronCondor
    from covered_call import CoveredCall
    from risk_manager import RiskManager
except ImportError:
    # Si falla, intentar import relativo (cuando se importa como módulo)
    from .base import StrategyBase, Position
    from .iron_condor import IronCondor
    from .covered_call import CoveredCall
    from .risk_manager import RiskManager


# ============================================================================
# VISUALIZADOR DE RESULTADOS
# ============================================================================

class BacktestVisualizer:
    """Crea visualizaciones profesionales de resultados de backtesting."""
    
    def __init__(self, results: Dict):
        """
        Inicializa el visualizador.
        
        Args:
            results: Diccionario de resultados del backtest
        """
        self.results = results
        self.summary = results['summary']
        self.trades_df = results.get('raw_data', pd.DataFrame())
        self.equity_df = results.get('equity_curve', pd.DataFrame())
        
        # Configurar estilo
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (16, 10)
        plt.rcParams['font.size'] = 10
    
    def plot_all(self, save_path: str = None):
        """
        Crea todos los gráficos en una sola figura.
        
        Args:
            save_path: Path para guardar la imagen (opcional)
        """
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Fila 1: Equity y Drawdown
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_equity_curve(ax1)
        
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_summary_stats(ax2)
        
        # Fila 2: Returns y Win Rate
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_returns_distribution(ax3)
        
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_win_loss_analysis(ax4)
        
        ax5 = fig.add_subplot(gs[1, 2])
        self._plot_returns_by_dte(ax5)
        
        # Fila 3: Timeline y Métricas
        ax6 = fig.add_subplot(gs[2, :2])
        self._plot_trades_timeline(ax6)
        
        ax7 = fig.add_subplot(gs[2, 2])
        self._plot_monthly_returns(ax7)
        
        # Título general
        title = f"Backtest Results | {self.summary['total_trades']} Trades | "
        title += f"Win Rate: {self.summary['win_rate']:.1%} | "
        title += f"Total Return: {self.summary['total_return_pct']:+.2f}%"
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.995)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"\n📊 Gráficos guardados en: {save_path}")
        
        plt.tight_layout()
        plt.show()
    
    def _plot_equity_curve(self, ax):
        """Gráfica la curva de equity."""
        if len(self.equity_df) == 0:
            ax.text(0.5, 0.5, 'No equity data', ha='center', va='center')
            ax.set_title('Equity Curve')
            return
        
        dates = pd.to_datetime(self.equity_df['date'])
        equity = self.equity_df['equity']
        
        # Equity curve
        ax.plot(dates, equity, linewidth=2, label='Equity', color='#2E86AB')
        ax.fill_between(dates, equity, self.summary['capital_inicial'], 
                        alpha=0.3, color='#2E86AB')
        
        # Línea de capital inicial
        ax.axhline(y=self.summary['capital_inicial'], color='gray', 
                  linestyle='--', linewidth=1, label='Initial Capital')
        
        # Calcular drawdown
        running_max = equity.expanding().max()
        drawdown = equity - running_max
        
        # Graficar áreas de drawdown
        ax.fill_between(dates, equity, running_max, where=(drawdown < 0),
                        color='red', alpha=0.3, label='Drawdown')
        
        ax.set_title('Equity Curve & Drawdown', fontweight='bold', fontsize=12)
        ax.set_xlabel('Date')
        ax.set_ylabel('Equity ($)')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Formatear eje Y
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Rotar fechas
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def _plot_summary_stats(self, ax):
        """Muestra estadísticas resumidas."""
        ax.axis('off')
        
        stats_text = f"""
SUMMARY STATISTICS
{'='*25}

Total Trades: {self.summary['total_trades']}
Win Rate: {self.summary['win_rate']:.1%}

Avg Return: {self.summary['avg_return_pct']:.2f}%
Avg Winner: {self.summary['avg_winner_pct']:.2f}%
Avg Loser: {self.summary['avg_loser_pct']:.2f}%

Total Return: {self.summary['total_return_pct']:+.2f}%
Total PnL: ${self.summary['total_pnl']:,.2f}

Profit Factor: {self.summary['profit_factor']:.2f}
Sharpe Ratio: {self.summary['sharpe_ratio']:.2f}
Max DD: {self.summary['max_drawdown_pct']:.2f}%

Avg Days Held: {self.summary['avg_days_held']:.1f}
"""
        
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    def _plot_returns_distribution(self, ax):
        """Distribución de retornos."""
        if len(self.trades_df) == 0:
            return
        
        returns = self.trades_df['return_pct']
        
        # Histograma
        ax.hist(returns, bins=20, alpha=0.7, color='#A23B72', edgecolor='black')
        
        # Líneas verticales para media y mediana
        ax.axvline(returns.mean(), color='red', linestyle='--', 
                  linewidth=2, label=f'Mean: {returns.mean():.2f}%')
        ax.axvline(returns.median(), color='green', linestyle='--', 
                  linewidth=2, label=f'Median: {returns.median():.2f}%')
        
        ax.set_title('Returns Distribution', fontweight='bold')
        ax.set_xlabel('Return (%)')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_win_loss_analysis(self, ax):
        """Análisis de ganancias vs pérdidas."""
        if len(self.trades_df) == 0:
            return
        
        winners = self.trades_df[self.trades_df['profitable']]
        losers = self.trades_df[~self.trades_df['profitable']]
        
        # Barras
        categories = ['Winners', 'Losers']
        counts = [len(winners), len(losers)]
        colors = ['#18A558', '#C73E1D']
        
        bars = ax.bar(categories, counts, color=colors, alpha=0.7, edgecolor='black')
        
        # Añadir valores encima de las barras
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(count)}\n({count/len(self.trades_df)*100:.1f}%)',
                   ha='center', va='bottom')
        
        ax.set_title('Win/Loss Count', fontweight='bold')
        ax.set_ylabel('Number of Trades')
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_returns_by_dte(self, ax):
        """Retornos por bucket de DTE."""
        if len(self.trades_df) == 0 or 'dte_bucket' not in self.trades_df.columns:
            return
        
        # Boxplot por DTE bucket
        dte_data = []
        dte_labels = []
        
        for bucket in self.trades_df['dte_bucket'].dropna().unique():
            bucket_returns = self.trades_df[self.trades_df['dte_bucket'] == bucket]['return_pct']
            if len(bucket_returns) > 0:
                dte_data.append(bucket_returns)
                dte_labels.append(str(bucket))
        
        if dte_data:
            bp = ax.boxplot(dte_data, labels=dte_labels, patch_artist=True)
            
            # Colorear boxes
            for patch in bp['boxes']:
                patch.set_facecolor('#F18F01')
                patch.set_alpha(0.7)
            
            ax.set_title('Returns by DTE', fontweight='bold')
            ax.set_xlabel('DTE Bucket')
            ax.set_ylabel('Return (%)')
            ax.grid(True, alpha=0.3, axis='y')
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def _plot_trades_timeline(self, ax):
        """Timeline de trades."""
        if len(self.trades_df) == 0:
            return
        
        # Ordenar por fecha de entrada
        df_sorted = self.trades_df.sort_values('entry_date')
        
        # Crear scatter plot
        colors = ['green' if p else 'red' for p in df_sorted['profitable']]
        sizes = abs(df_sorted['pnl'])
        
        scatter = ax.scatter(df_sorted['entry_date'], df_sorted['return_pct'],
                           c=colors, s=sizes, alpha=0.6, edgecolors='black')
        
        # Línea de retorno cero
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
        
        ax.set_title('Trades Timeline', fontweight='bold')
        ax.set_xlabel('Entry Date')
        ax.set_ylabel('Return (%)')
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    def _plot_monthly_returns(self, ax):
        """Retornos mensuales."""
        if len(self.trades_df) == 0:
            ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center')
            ax.set_title('Monthly Returns')
            return
        
        # Agrupar por mes
        df = self.trades_df.copy()
        df['month'] = pd.to_datetime(df['entry_date']).dt.to_period('M')
        monthly_pnl = df.groupby('month')['pnl'].sum()
        
        if len(monthly_pnl) == 0:
            ax.text(0.5, 0.5, 'No monthly data', ha='center', va='center')
            ax.set_title('Monthly Returns')
            return
        
        # Colores según positivo/negativo
        colors = ['green' if x > 0 else 'red' for x in monthly_pnl]
        
        bars = ax.bar(range(len(monthly_pnl)), monthly_pnl, color=colors, alpha=0.7)
        
        ax.set_title('Monthly PnL', fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('PnL ($)')
        ax.set_xticks(range(len(monthly_pnl)))
        ax.set_xticklabels([str(m) for m in monthly_pnl.index], rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        ax.axhline(y=0, color='black', linewidth=1)

# Setup de estilo para gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)


@dataclass
class BacktestConfig:
    """Configuración para backtesting."""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000.0
    max_positions: int = 5
    data_path: Optional[Path] = None  # Se configurará en __post_init__
    commission_per_contract: float = 1.0  # $1 por contrato
    strategies: List[str] = field(default_factory=lambda: ['iron_condor'])
    
    def __post_init__(self):
        """Validación de configuración."""
        if self.start_date >= self.end_date:
            raise ValueError("start_date debe ser anterior a end_date")
        if self.initial_capital <= 0:
            raise ValueError("initial_capital debe ser positivo")
        if self.max_positions <= 0:
            raise ValueError("max_positions debe ser mayor a 0")
        
        # Si no se especifica data_path, usar el default relativo al script
        if self.data_path is None:
            script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
            self.data_path = script_dir.parent.parent / "data" / "historical"


class MarketDataLoader:
    """Carga y prepara datos históricos de opciones desde archivos Parquet."""
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self._cache = {}
    
    def load_ticker_data(self, ticker: str) -> pd.DataFrame:
        """
        Carga datos históricos de un ticker desde Parquet.
        
        Args:
            ticker: Símbolo del ticker (ej: 'SPY')
            
        Returns:
            DataFrame con datos históricos
        """
        if ticker in self._cache:
            return self._cache[ticker]
        
        file_path = self.data_path / f"{ticker}_60days.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No se encontró archivo: {file_path}")
        
        df = pd.read_parquet(file_path)
        
        # Validar columnas requeridas
        required_cols = [
            'date', 'ticker', 'underlying', 'type', 'strike', 'expiration',
            'dte', 'delta', 'gamma', 'theta', 'vega', 'iv', 'close', 'volume', 'oi'
        ]
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Columnas faltantes en {ticker}: {missing}")
        
        # Convertir fechas
        df['date'] = pd.to_datetime(df['date'])
        df['expiration'] = pd.to_datetime(df['expiration'])
        
        # Ordenar por fecha
        df = df.sort_values('date').reset_index(drop=True)
        
        self._cache[ticker] = df
        return df
    
    def get_options_for_date(self, ticker: str, date: datetime, 
                           min_dte: int = 15, max_dte: int = 60) -> pd.DataFrame:
        """
        Obtiene cadena de opciones disponibles para una fecha específica.
        
        Args:
            ticker: Símbolo del ticker
            date: Fecha de consulta
            min_dte: DTE mínimo
            max_dte: DTE máximo
            
        Returns:
            DataFrame con opciones disponibles
        """
        df = self.load_ticker_data(ticker)
        
        # Filtrar por fecha y DTE
        mask = (
            (df['date'] == date) &
            (df['dte'] >= min_dte) &
            (df['dte'] <= max_dte)
        )
        
        options = df[mask].copy()
        
        if len(options) == 0:
            return pd.DataFrame()
        
        # Estimar precio del subyacente desde opciones ATM
        underlying_price = self._estimate_underlying_price(options)
        if underlying_price:
            options['underlying_price'] = underlying_price
        
        return options
    
    def _estimate_underlying_price(self, options: pd.DataFrame) -> Optional[float]:
        """
        Estima el precio del subyacente desde opciones ATM.
        
        Args:
            options: DataFrame con opciones
            
        Returns:
            Precio estimado del subyacente o None
        """
        if len(options) == 0:
            return None
        
        # Buscar calls ATM (delta cercano a 0.5)
        calls = options[options['type'] == 'call']
        if len(calls) == 0:
            return None
        
        atm_calls = calls[calls['delta'].between(0.45, 0.55)]
        
        if len(atm_calls) > 0:
            # Usar la mediana de strikes ATM como estimación
            return atm_calls['strike'].median()
        else:
            # Si no hay ATM, usar el strike con delta más cercano a 0.5
            calls_sorted = calls.copy()
            calls_sorted['delta_diff'] = abs(calls_sorted['delta'] - 0.5)
            closest = calls_sorted.nsmallest(1, 'delta_diff')
            return closest['strike'].iloc[0]
    
    def get_underlying_price(self, ticker: str, date: datetime) -> Optional[float]:
        """Obtiene precio del subyacente para una fecha."""
        df = self.load_ticker_data(ticker)
        day_data = df[df['date'] == date]
        
        if len(day_data) == 0:
            return None
        
        # Estimar desde opciones ATM
        return self._estimate_underlying_price(day_data)
    
    def get_date_range(self, ticker: str) -> Tuple[datetime, datetime]:
        """Retorna el rango de fechas disponible para un ticker."""
        df = self.load_ticker_data(ticker)
        return df['date'].min(), df['date'].max()


class BacktestEngine:
    """Motor principal de backtesting."""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.data_loader = MarketDataLoader(config.data_path)
        
        # Estado del backtest
        self.current_date: Optional[datetime] = None
        self.capital: float = config.initial_capital
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []
        
        # Inicializar estrategias
        self.strategies = self._initialize_strategies()
        
        # Tracking de equity
        self.equity_curve: List[Dict] = []
    
    def _initialize_strategies(self) -> Dict[str, StrategyBase]:
        """Inicializa las estrategias de trading."""
        strategies = {}
        
        if 'iron_condor' in self.config.strategies:
            strategies['iron_condor'] = IronCondor(
                dte_range=(15, 60),
                short_delta_range=(0.16, 0.25),
                long_delta_range=(0.05, 0.10),
                min_iv_rank=60
            )
        
        if 'covered_call_income' in self.config.strategies or 'covered_call' in self.config.strategies:
            strategies['covered_call'] = CoveredCall()
        
        return strategies
    
    def run_backtest(self, ticker: str = 'SPY') -> Dict:
        """
        Ejecuta backtesting completo para un ticker.
        
        Args:
            ticker: Símbolo del ticker a backtestear
            
        Returns:
            Diccionario con resultados del backtest
        """
        print(f"\n{'='*60}")
        print(f"🚀 INICIANDO BACKTESTING - {ticker}")
        print(f"{'='*60}")
        print(f"Período: {self.config.start_date.date()} → {self.config.end_date.date()}")
        print(f"Capital inicial: ${self.config.initial_capital:,.2f}")
        print(f"Estrategias: {', '.join(self.config.strategies)}")
        print(f"Máx. posiciones: {self.config.max_positions}")
        
        # Verificar disponibilidad de datos
        available_start, available_end = self.data_loader.get_date_range(ticker)
        print(f"\nDatos disponibles: {available_start.date()} → {available_end.date()}")
        
        # Ajustar fechas si es necesario
        actual_start = max(self.config.start_date, available_start)
        actual_end = min(self.config.end_date, available_end)
        
        if actual_start != self.config.start_date or actual_end != self.config.end_date:
            print(f"⚠️  Ajustando fechas a datos disponibles:")
            print(f"   Nuevo período: {actual_start.date()} → {actual_end.date()}")
        
        # Obtener fechas únicas de trading
        df = self.data_loader.load_ticker_data(ticker)
        trading_dates = sorted(df['date'].unique())
        trading_dates = [d for d in trading_dates if actual_start <= d <= actual_end]
        
        print(f"\n📅 Días de trading: {len(trading_dates)}")
        print(f"Iniciando simulación...\n")
        
        # Loop principal de backtesting
        for i, current_date in enumerate(trading_dates):
            self.current_date = current_date
            
            # Obtener precio del subyacente
            underlying_price = self.data_loader.get_underlying_price(ticker, current_date)
            if not underlying_price:
                continue
            
            # 1. Gestionar posiciones existentes
            self._manage_positions(ticker, current_date, underlying_price)
            
            # 2. Buscar nuevas oportunidades (solo viernes para reducir frecuencia)
            # Viernes es weekday=4
            if current_date.weekday() == 4 and len(self.positions) < self.config.max_positions:
                self._find_new_opportunities(ticker, current_date, underlying_price)
            
            # 3. Registrar equity del día
            self._record_daily_equity(current_date, underlying_price)
            
            # Progress update cada 10 días
            if (i + 1) % 10 == 0 or i == len(trading_dates) - 1:
                print(f"📊 Día {i+1}/{len(trading_dates)} | {current_date.date()} | "
                      f"Precio: ${underlying_price:.2f} | "
                      f"Posiciones: {len(self.positions)} abiertas, {len(self.closed_positions)} cerradas")
        
        # Cerrar posiciones restantes al final
        self._close_remaining_positions(ticker, trading_dates[-1])
        
        print(f"\n✅ Backtesting completado")
        print(f"Total de operaciones: {len(self.closed_positions)}")
        
        return self._calculate_results()
    
    def _manage_positions(self, ticker: str, current_date: datetime, underlying_price: float):
        """
        Gestiona posiciones existentes: verificar stops, profit targets, vencimiento.
        
        Args:
            ticker: Símbolo del ticker
            current_date: Fecha actual
            underlying_price: Precio actual del subyacente
        """
        positions_to_close = []
        
        for position in self.positions:
            # Verificar si venció
            if current_date >= position.expiration_date:
                # Calcular PnL al vencimiento
                pnl = self._calculate_expiry_pnl(position, underlying_price)
                position.pnl = pnl
                position.exit_date = current_date
                position.days_held = (current_date - position.entry_date).days
                position.status = 'expired_profitable' if pnl > 0 else 'expired_loss'
                positions_to_close.append(position)
                continue
            
            # Calcular valor actual de la posición
            current_value = self._calculate_position_value(
                ticker, position, current_date, underlying_price
            )
            
            # DEBUG: Ver qué está pasando con la valoración
            days_remaining = (position.expiration_date - current_date).days
            if current_value is None:
                
                continue
            
            # Calcular PnL actual (para Iron Condor: crédito recibido - valor actual)
            current_pnl = position.premium_collected - current_value
            
            # DEBUG: Mostrar progreso de la posición
            
            
            # Verificar profit target
            if current_pnl >= position.profit_target:
                position.pnl = current_pnl
                position.exit_date = current_date
                position.exit_value = current_value
                position.days_held = (current_date - position.entry_date).days
                position.status = 'closed_profit'
                positions_to_close.append(position)
                
                continue
            
            # Verificar stop loss
            if current_pnl <= -position.stop_loss:
                position.pnl = current_pnl
                position.exit_date = current_date
                position.exit_value = current_value
                position.days_held = (current_date - position.entry_date).days
                position.status = 'closed_loss'
                positions_to_close.append(position)
                
                continue
        
        # Mover posiciones cerradas
        for position in positions_to_close:
            self.positions.remove(position)
            self.closed_positions.append(position)
            
            # Ajustar capital (devolver margen/colateral)
            self.capital += abs(position.max_risk)

    def _find_new_opportunities(self, ticker: str, current_date: datetime, underlying_price: float):
        """
        Busca nuevas oportunidades de entrada con las estrategias configuradas.
        
        Args:
            ticker: Símbolo del ticker
            current_date: Fecha actual
            underlying_price: Precio actual del subyacente
        """
        # Obtener opciones disponibles
        options = self.data_loader.get_options_for_date(ticker, current_date)
        
        if len(options) == 0:
            return
        
        # CORRECCIÓN: Convertir deltas de puts a valores absolutos
        options = options.copy()
        options.loc[options['type'] == 'put', 'delta'] = abs(options.loc[options['type'] == 'put', 'delta'])
        
        # Preparar market_data para las estrategias
        # Estimar IV Rank (simplificado: usar percentil de IV actual vs histórica)
        iv_values = options['iv'].dropna().values
        if len(iv_values) > 0:
            current_iv = np.median(iv_values)
            iv_rank = 70  # Simplificado - asumir alto para que encuentre setups
        else:
            current_iv = 0.25
            iv_rank = 70
        
        market_data = {
            'underlying_price': underlying_price,
            'iv_rank': iv_rank,
            'current_iv': current_iv
        }
        
        # Intentar crear posición con cada estrategia
        for strategy_name, strategy in self.strategies.items():
            # Verificar si tenemos capital disponible
            required_capital = 5000  # Simplificado, debería calcularse por estrategia
            if self.capital < required_capital:
                continue
            
            try:
                # Usar método scan() de la estrategia
                opportunities = strategy.scan(options, market_data)
                
                if opportunities is not None and len(opportunities) > 0:
                    # Tomar la mejor oportunidad (ya vienen rankeadas)
                    best_opportunity = opportunities.iloc[0]
                    
                    # Construir posición usando construct_position()
                    position = strategy.construct_position(best_opportunity)
                    
                    if position:
                        # Ajustar fechas
                        position.entry_date = current_date
                        
                        # Agregar posición
                        self.positions.append(position)
                        self.capital -= abs(position.max_risk)  # Reservar capital
                        
                        print(f"  ✅ Nueva posición {strategy_name}: "
                              f"DTE {position.dte_at_entry}, "
                              f"Crédito ${position.premium_collected:.2f}")
                        break  # Solo una posición por día
                        
            except Exception as e:
                # Si hay error con una estrategia, continuar con las demás
                print(f"  ⚠️  Error con {strategy_name}: {e}")
                continue
    
    def _calculate_position_value(self, ticker: str, position: Position, 
                                 current_date: datetime, underlying_price: float) -> Optional[float]:
        """
        Calcula el valor actual de mercado de una posición usando PRECIOS REALES.
        
        Args:
            ticker: Símbolo del ticker
            position: Posición a valorar
            current_date: Fecha actual
            underlying_price: Precio actual del subyacente
            
        Returns:
            Valor actual o None si no se puede calcular
        """
        # Cargar datos para esta fecha y vencimiento
        df = self.data_loader.load_ticker_data(ticker)
        
        # Filtrar opciones para esta fecha y vencimiento
        mask = (
            (df['date'] == current_date) & 
            (df['expiration'] == position.expiration_date)
        )
        
        available_options = df[mask]
        
        if len(available_options) == 0:
            # No hay datos para esta fecha/vencimiento
            return None
        
        # Calcular valor de cada leg usando precios reales
        total_value = 0.0
        legs_found = 0
        
        for leg in position.legs:
            # Buscar esta opción específica en los datos
            leg_mask = (
                (available_options['strike'] == leg['strike']) &
                (available_options['type'] == leg['type'])
            )
            
            leg_data = available_options[leg_mask]
            
            if len(leg_data) == 0:
                # No se encontró esta leg específica
                continue
            
            # Obtener precio (close o vwap si close es NaN)
            leg_price = leg_data.iloc[0]['close']
            if pd.isna(leg_price):
                leg_price = leg_data.iloc[0]['vwap']
            
            if pd.isna(leg_price):
                # No hay precio disponible
                continue
            
            legs_found += 1
            
            # Calcular valor según posición
            # Para Iron Condor: short options tienen valor positivo (vendimos), long negativo (compramos)
            if leg['position'] == 'short':
                total_value += leg_price * 100  # Multiplicar por 100 (tamaño del contrato)
            else:  # long
                total_value -= leg_price * 100
        
        # Solo retornar valor si encontramos todas las legs
        if legs_found == len(position.legs):
            return total_value
        else:
            # Si falta alguna leg, no podemos valorar correctamente
            return None

    def _calculate_expiry_pnl(self, position: Position, final_price: float) -> float:
        """
        Calcula PnL al vencimiento basado en valor intrínseco REAL.
        
        Args:
            position: Posición que vence
            final_price: Precio final del subyacente
            
        Returns:
            PnL final
        """
        # Calcular valor intrínseco de cada leg al vencimiento
        total_intrinsic_value = 0.0
        
        for leg in position.legs:
            # Valor intrínseco de la opción
            if leg['type'] == 'call':
                intrinsic = max(0, final_price - leg['strike'])
            else:  # put
                intrinsic = max(0, leg['strike'] - final_price)
            
            # Multiplicar por 100 (tamaño del contrato)
            intrinsic_value = intrinsic * 100
            
            # Para short positions: pagamos el valor intrínseco (negativo para nosotros)
            # Para long positions: recibimos el valor intrínseco (positivo para nosotros)
            if leg['position'] == 'short':
                total_intrinsic_value += intrinsic_value  # Valor que debe pagar
            else:  # long
                total_intrinsic_value -= intrinsic_value  # Valor que recibimos
        
        # PnL = Premium recibido - Valor intrínseco al vencimiento
        pnl = position.premium_collected - total_intrinsic_value
        
        return pnl

    def _record_daily_equity(self, current_date: datetime, underlying_price: float):
        """Registra equity diario para gráficas."""
        # Calcular valor de posiciones abiertas
        open_positions_value = 0
        for position in self.positions:
            current_value = self._calculate_position_value(
                'SPY', position, current_date, underlying_price
            )
            if current_value:
                open_positions_value += position.premium_collected - current_value
        
        # Capital total = efectivo + valor de posiciones abiertas + capital reservado
        reserved_capital = sum(abs(p.max_risk) for p in self.positions)
        total_equity = self.capital + open_positions_value + reserved_capital
        
        self.equity_curve.append({
            'date': current_date,
            'equity': total_equity,
            'cash': self.capital,
            'open_positions': len(self.positions),
            'closed_positions': len(self.closed_positions)
        })
    
    def _close_remaining_positions(self, ticker: str, final_date: datetime):
        """Cierra posiciones restantes al final del backtest."""
        underlying_price = self.data_loader.get_underlying_price(ticker, final_date)
        
        for position in self.positions[:]:
            pnl = self._calculate_expiry_pnl(position, underlying_price)
            position.pnl = pnl
            position.exit_date = final_date
            position.days_held = (final_date - position.entry_date).days
            position.status = 'closed_end'
            self.closed_positions.append(position)
            self.capital += abs(position.max_risk)
        
        self.positions.clear()
    
    def _calculate_results(self) -> Dict:
        """Calcula métricas de performance."""
        if len(self.closed_positions) == 0:
            return {
                'summary': {
                    'total_trades': 0,
                    'capital_inicial': self.config.initial_capital,
                    'capital_final': self.capital
                }
            }
        
        # Convertir posiciones cerradas a DataFrame
        trades_data = []
        for pos in self.closed_positions:
            trades_data.append({
                'strategy': pos.strategy_name,
                'entry_date': pos.entry_date,
                'exit_date': pos.exit_date,
                'dte_entry': pos.dte_at_entry,
                'days_held': pos.days_held,
                'premium_collected': pos.premium_collected,
                'max_risk': pos.max_risk,
                'pnl': pos.pnl,
                'return_pct': (pos.pnl / abs(pos.max_risk)) * 100 if pos.max_risk != 0 else 0,
                'profitable': pos.pnl > 0,
                'status': pos.status
            })
        
        df_trades = pd.DataFrame(trades_data)
        
        # === MÉTRICAS GENERALES ===
        total_trades = len(df_trades)
        winners = df_trades[df_trades['profitable']]
        losers = df_trades[~df_trades['profitable']]
        
        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        avg_return = df_trades['return_pct'].mean()
        avg_winner = winners['return_pct'].mean() if len(winners) > 0 else 0
        avg_loser = losers['return_pct'].mean() if len(losers) > 0 else 0
        avg_days_held = df_trades['days_held'].mean()
        
        total_pnl = df_trades['pnl'].sum()
        total_premium = df_trades['premium_collected'].sum()
        total_risk = df_trades['max_risk'].sum()
        
        # === PROFIT FACTOR ===
        gross_profit = winners['pnl'].sum() if len(winners) > 0 else 0
        gross_loss = abs(losers['pnl'].sum()) if len(losers) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # === EXPECTANCY ===
        expectancy = (win_rate * avg_winner) + ((1 - win_rate) * avg_loser)
        
        # === SHARPE RATIO ===
        returns_series = df_trades['return_pct']
        sharpe_ratio = self._calculate_sharpe(returns_series)
        
        # === MAX DRAWDOWN ===
        max_drawdown, max_dd_pct = self._calculate_max_drawdown(df_trades)
        
        # === EQUITY FINAL ===
        if self.equity_curve and len(self.equity_curve) > 0:
            initial_equity = self.equity_curve[0]['equity']
            final_equity = self.equity_curve[-1]['equity']
            total_return_pct = ((final_equity - initial_equity) / initial_equity) * 100
        else:
            initial_equity = self.config.initial_capital
            final_equity = self.capital
            total_return_pct = ((final_equity - initial_equity) / initial_equity) * 100
        
        # === MÉTRICAS POR ESTRATEGIA ===
        strategy_metrics = {}
        for strategy in df_trades['strategy'].unique():
            strat_df = df_trades[df_trades['strategy'] == strategy]
            strat_winners = strat_df[strat_df['profitable']]
            
            strategy_metrics[strategy] = {
                'trades': len(strat_df),
                'win_rate': len(strat_winners) / len(strat_df) if len(strat_df) > 0 else 0,
                'avg_return': strat_df['return_pct'].mean(),
                'avg_days_held': strat_df['days_held'].mean(),
                'total_pnl': strat_df['pnl'].sum(),
                'total_premium': strat_df['premium_collected'].sum()
            }
        
        # === MÉTRICAS POR DTE ===
        df_trades['dte_bucket'] = pd.cut(
            df_trades['dte_entry'], 
            bins=[0, 21, 35, 60, 100], 
            labels=['Short (≤21)', 'Medium (22-35)', 'Long (36-60)', 'Very Long (>60)']
        )
        
        dte_metrics = {}
        for bucket in df_trades['dte_bucket'].dropna().unique():
            bucket_df = df_trades[df_trades['dte_bucket'] == bucket]
            bucket_winners = bucket_df[bucket_df['profitable']]
            
            dte_metrics[str(bucket)] = {
                'trades': len(bucket_df),
                'win_rate': len(bucket_winners) / len(bucket_df) if len(bucket_df) > 0 else 0,
                'avg_return': bucket_df['return_pct'].mean(),
                'total_pnl': bucket_df['pnl'].sum()
            }
        
        return {
            'summary': {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'avg_return_pct': avg_return,
                'avg_winner_pct': avg_winner,
                'avg_loser_pct': avg_loser,
                'avg_days_held': avg_days_held,
                'total_pnl': total_pnl,
                'total_premium': total_premium,
                'total_risk': total_risk,
                'profit_factor': profit_factor,
                'expectancy': expectancy,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_dd_pct,
                'capital_inicial': self.config.initial_capital,
                'capital_final': final_equity,
                'total_return_pct': total_return_pct
            },
            'by_strategy': strategy_metrics,
            'by_dte': dte_metrics,
            'raw_data': df_trades,
            'equity_curve': pd.DataFrame(self.equity_curve) if self.equity_curve else pd.DataFrame()
        }
    
    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.03) -> float:
        """
        Calcula Sharpe Ratio.
        
        Args:
            returns: Serie de retornos (%)
            risk_free_rate: Tasa libre de riesgo anualizada
            
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        # Convertir retornos % a decimales
        returns_decimal = returns / 100
        
        # Exceso de retorno
        excess_returns = returns_decimal - (risk_free_rate / 252)  # Daily risk-free rate
        
        # Sharpe anualizado
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_max_drawdown(self, trades_df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calcula máximo drawdown desde equity curve.
        
        Args:
            trades_df: DataFrame de trades
            
        Returns:
            (max_drawdown en $, max_drawdown en %)
        """
        if not self.equity_curve or len(self.equity_curve) == 0:
            return (0.0, 0.0)
        
        equity_series = pd.Series([eq['equity'] for eq in self.equity_curve])
        
        # Calcular running maximum
        running_max = equity_series.expanding().max()
        
        # Drawdown en cada punto
        drawdown = equity_series - running_max
        drawdown_pct = (drawdown / running_max) * 100
        
        max_dd = drawdown.min()
        max_dd_pct = drawdown_pct.min()
        
        return (max_dd, max_dd_pct)