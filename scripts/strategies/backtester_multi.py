"""
Backtesting Engine para Estrategias de Opciones - MULTI-TICKER
Integrado con IronCondor, CoveredCall y datos históricos reales de Polygon.io

Autor: Sistema de Trading Algorítmico
Fecha: Parte 6 - Multi-Ticker Backtesting (con Selección Inteligente)
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
import importlib.util

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
    from adaptive_config import get_adaptive_config_manager  # 🆕 Configuración adaptativa
except ImportError:
    # Si falla, intentar import relativo (cuando se importa como módulo)
    from .base import StrategyBase, Position
    from .iron_condor import IronCondor
    from .covered_call import CoveredCall
    from .risk_manager import RiskManager
    from .adaptive_config import get_adaptive_config_manager  # 🆕 Configuración adaptativa

# 🆕 Importar Black-Scholes para valoración fallback
BSM_AVAILABLE = False
black_scholes_price = None

def _import_black_scholes():
    """Importa Black-Scholes con manejo robusto de paths."""
    global BSM_AVAILABLE, black_scholes_price
    
    try:
        # Obtener path absoluto a quantitative
        current_file = Path(__file__).resolve()
        quantitative_path = current_file.parent.parent / "quantitative"
        
        if not quantitative_path.exists():
            raise FileNotFoundError(f"Path no encontrado: {quantitative_path}")
        
        # Agregar al sys.path si no está
        quantitative_str = str(quantitative_path)
        if quantitative_str not in sys.path:
            sys.path.insert(0, quantitative_str)
        
        # Importar black_scholes ahora que el path está configurado
        import black_scholes as bs_module
        
        # Obtener la función
        black_scholes_price = bs_module.black_scholes_price
        BSM_AVAILABLE = True
        print("✅ Black-Scholes importado exitosamente para valoración fallback")
        return True
        
    except Exception as e:
        BSM_AVAILABLE = False
        black_scholes_price = None
        print(f"⚠️  WARNING: No se pudo importar Black-Scholes: {e}")
        print("   Valoración fallback deshabilitada (solo usará market data)")
        return False

# Intentar importar al inicio
_import_black_scholes()


# ============================================================================
# CLASES AUXILIARES PARA SELECCIÓN INTELIGENTE
# ============================================================================

@dataclass
class OpportunityCandidate:
    """Representa una oportunidad de trading con su scoring."""
    ticker: str
    strategy_name: str
    opportunity_data: pd.Series  # La fila del DataFrame de scan()
    position: Position  # La posición construida
    quality_score: float = 0.0
    
    # Métricas individuales para análisis
    ror: float = 0.0
    credit: float = 0.0
    liquidity_score: float = 0.0
    iv_rank: float = 0.0
    delta_quality: float = 0.0


class OpportunityScorer:
    """Sistema de scoring para rankear oportunidades."""
    
    @staticmethod
    def calculate_quality_score(
        opportunity: pd.Series,
        position: Position,
        market_data: Dict
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calcula un quality score para una oportunidad.
        
        SCORING OPTIMIZADO (Opción 3: Híbrido)
        Basado en análisis de 44 trades con BSM fallback:
        - Premium/Risk ratio: 45% (evidencia: 511.72% en profit targets)
        - DTE Long Bias: 20% (evidencia: 385.78% return en Long DTE)
        - Liquidez: 15% (BSM fallback compensa gaps)
        - IV Rank: 10% (menos predictivo de lo esperado)
        - Premium Absoluto: 5% (ratio importa más que valor absoluto)
        - Delta Quality: 5% (mantener)
        
        Args:
            opportunity: Serie con datos de la oportunidad (del scan())
            position: Posición construida
            market_data: Datos de mercado
            
        Returns:
            (quality_score, metrics_dict)
        """
        metrics = {}
        
        # 1. Premium/Risk Ratio - Peso: 45% (AUMENTADO de 30%)
        # Evidencia: Profit targets promediaron 511.72% Premium/Risk
        # Closed end promediaron 277.50% Premium/Risk
        ror = (position.premium_collected / abs(position.max_risk)) * 100
        # Normalizar a 400% para capturar mejor rango (basado en 511.72% observado)
        ror_score = min(ror / 400.0, 1.0) * 0.45  
        metrics['ror'] = ror
        
        # 2. DTE Long Bias - Peso: 20% (AUMENTADO de 10%)
        # Evidencia: Long DTE (36-60) + profit targets = 385.78% return
        # vs Hold to expiration = 143.52% return (2.69x mejor)
        dte = position.dte_at_entry
        if 42 <= dte <= 56:
            # SWEET SPOT: mejor performance observada
            dte_score = 0.20
        elif 36 <= dte < 42 or 56 < dte <= 60:
            # Long DTE range
            dte_score = 0.17
        elif 30 <= dte < 36:
            # Medium DTE
            dte_score = 0.12
        elif 22 <= dte < 30:
            # Medium-Short DTE
            dte_score = 0.08
        else:
            # Muy corto o muy largo
            dte_score = 0.04
        metrics['dte'] = dte
        
        # 3. Liquidez promedio de las legs - Peso: 15% (REDUCIDO de 20%)
        # BSM fallback ha demostrado que gaps de liquidez son manejables
        total_volume = 0
        total_oi = 0
        leg_count = len(position.legs)
        
        for leg in position.legs:
            total_volume += getattr(opportunity, f"{leg['type']}_volume", 100)
            total_oi += getattr(opportunity, f"{leg['type']}_oi", 100)
        
        avg_volume = total_volume / leg_count if leg_count > 0 else 0
        avg_oi = total_oi / leg_count if leg_count > 0 else 0
        
        # Normalizar liquidez
        volume_normalized = min(avg_volume / 100.0, 1.0)
        oi_normalized = min(avg_oi / 200.0, 1.0)
        liquidity_score = ((volume_normalized + oi_normalized) / 2) * 0.15
        metrics['liquidity_score'] = liquidity_score * 6.67  # Escalar para mostrar
        
        # 4. IV Rank - Peso: 10% (REDUCIDO de 15%)
        # Menos predictivo de lo esperado en el análisis
        iv_rank = market_data.get('iv_rank', 50)
        iv_score = (iv_rank / 100.0) * 0.10
        metrics['iv_rank'] = iv_rank
        
        # 5. Premium Absoluto - Peso: 5% (REDUCIDO de 20%)
        # Evidencia: Ratio importa más que valor absoluto
        # Correlación: premium_collected = +0.270
        credit = position.premium_collected
        credit_score = min(credit / 500.0, 1.0) * 0.05
        metrics['credit'] = credit
        
        # 6. Delta Quality - Peso: 5% (MANTENER)
        # Para IC: preferir deltas balanceadas y dentro de rango óptimo
        delta_score = 0.05  # Simplificado
        metrics['delta_quality'] = delta_score * 20  # Escalar
        
        # Score total (suma de todos los componentes ponderados)
        quality_score = (
            ror_score +          # 45%
            dte_score +          # 20%
            liquidity_score +    # 15%
            iv_score +           # 10%
            credit_score +       # 5%
            delta_score          # 5%
        )                        # = 100%
        
        return quality_score, metrics


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
    """Configuración para backtesting multi-ticker."""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000.0
    max_positions: int = 5
    max_positions_per_ticker: int = 2  # 🆕 Límite por ticker
    tickers: List[str] = field(default_factory=lambda: ['SPY'])  # 🆕 Lista de tickers
    data_path: Optional[Path] = None
    commission_per_contract: float = 1.0
    strategies: List[str] = field(default_factory=lambda: ['iron_condor'])
    
    def __post_init__(self):
        """Validación de configuración."""
        if self.start_date >= self.end_date:
            raise ValueError("start_date debe ser anterior a end_date")
        if self.initial_capital <= 0:
            raise ValueError("initial_capital debe ser positivo")
        if self.max_positions <= 0:
            raise ValueError("max_positions debe ser mayor a 0")
        if not self.tickers or len(self.tickers) == 0:
            raise ValueError("Debe especificar al menos un ticker")
        
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
    """Motor principal de backtesting multi-ticker."""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.data_loader = MarketDataLoader(config.data_path)
        
        # Estado del backtest
        self.current_date: Optional[datetime] = None
        self.capital: float = config.initial_capital
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []
        
        # 🆕 Cache de tickers válidos (que tienen datos)
        self.valid_tickers: List[str] = []
        self._validate_tickers()
        
        # Inicializar estrategias
        self.strategies = self._initialize_strategies()
        
        # 🆕 Gestor de configuración adaptativa
        self.adaptive_config = get_adaptive_config_manager()
        print(f"\n⚙️  Configuración adaptativa cargada para {len(self.valid_tickers)} tickers")
        
        # Tracking de equity
        self.equity_curve: List[Dict] = []
        
        # 🆕 Contadores de valoración (diagnóstico)
        self.valorization_failures = 0  # Fallos de market data
        self.valorization_attempts = 0
        self.bsm_fallback_used = 0  # Veces que se usó BSM
    
    def _validate_tickers(self):
        """Valida qué tickers tienen datos disponibles."""
        print(f"\n🔍 Validando tickers...")
        
        for ticker in self.config.tickers:
            try:
                # Intentar cargar datos
                df = self.data_loader.load_ticker_data(ticker)
                
                # Verificar que tenga datos en el rango solicitado
                available_start, available_end = self.data_loader.get_date_range(ticker)
                
                # Verificar overlap con rango solicitado
                if available_end < self.config.start_date or available_start > self.config.end_date:
                    print(f"  ⚠️  {ticker}: Sin datos en rango solicitado")
                    continue
                
                self.valid_tickers.append(ticker)
                print(f"  ✅ {ticker}: {len(df):,} registros disponibles")
                
            except FileNotFoundError:
                print(f"  ❌ {ticker}: Archivo no encontrado")
            except Exception as e:
                print(f"  ❌ {ticker}: Error - {e}")
        
        if len(self.valid_tickers) == 0:
            raise ValueError("Ningún ticker tiene datos disponibles")
        
        print(f"\n📊 Tickers válidos: {len(self.valid_tickers)}/{len(self.config.tickers)}")
    
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
    
    def _get_consolidated_trading_dates(self) -> List[datetime]:
        """
        Consolida fechas de trading de todos los tickers válidos.
        
        Returns:
            Lista ordenada de fechas únicas
        """
        all_dates = set()
        
        for ticker in self.valid_tickers:
            df = self.data_loader.load_ticker_data(ticker)
            ticker_dates = df['date'].unique()
            
            # Filtrar por rango solicitado
            ticker_dates = [d for d in ticker_dates 
                           if self.config.start_date <= d <= self.config.end_date]
            
            all_dates.update(ticker_dates)
        
        # Retornar ordenadas
        return sorted(list(all_dates))
    
    def run_multi_ticker_backtest(self) -> Dict:
        """
        Ejecuta backtesting para TODOS los tickers configurados.
        
        Returns:
            Diccionario con resultados consolidados
        """
        print(f"\n{'='*70}")
        print(f"🚀 INICIANDO BACKTESTING MULTI-TICKER")
        print(f"{'='*70}")
        print(f"Tickers: {', '.join(self.valid_tickers)}")
        print(f"Período: {self.config.start_date.date()} → {self.config.end_date.date()}")
        print(f"Capital inicial: ${self.config.initial_capital:,.2f}")
        print(f"Estrategias: {', '.join(self.config.strategies)}")
        print(f"Máx. posiciones totales: {self.config.max_positions}")
        print(f"Máx. posiciones por ticker: {self.config.max_positions_per_ticker}")
        
        # 1. Consolidar fechas de trading de todos los tickers
        all_trading_dates = self._get_consolidated_trading_dates()
        print(f"\n📅 Días de trading consolidados: {len(all_trading_dates)}")
        
        # 2. Loop principal de backtesting
        print(f"\nIniciando simulación...\n")
        
        for i, current_date in enumerate(all_trading_dates):
            self.current_date = current_date
            
            # 3. Gestionar posiciones existentes (todos los tickers)
            self._manage_all_positions(current_date)
            
            # 4. Buscar nuevas oportunidades en TODOS los tickers
            # 🆕 BUSCAR TODOS LOS DÍAS (no solo viernes) para maximizar trades
            if len(self.positions) < self.config.max_positions:
                self._find_multi_ticker_opportunities(current_date)
            
            # 5. Registrar equity del día
            self._record_multi_ticker_equity(current_date)
            
            # Progress update
            if (i + 1) % 10 == 0 or i == len(all_trading_dates) - 1:
                print(f"📊 Día {i+1}/{len(all_trading_dates)} | {current_date.date()} | "
                      f"Posiciones: {len(self.positions)} abiertas, {len(self.closed_positions)} cerradas | "
                      f"Capital: ${self.capital:,.0f}")
        
        # 6. Cerrar posiciones restantes
        self._close_all_remaining_positions(all_trading_dates[-1])
        
        print(f"\n✅ Backtesting completado")
        print(f"Total de operaciones: {len(self.closed_positions)}")
        
        # 🆕 Reporte de valorización
        if self.valorization_attempts > 0:
            market_data_failure_rate = (self.valorization_failures / self.valorization_attempts) * 100
            bsm_usage_rate = (self.bsm_fallback_used / self.valorization_attempts) * 100
            total_failures = self.valorization_failures - self.bsm_fallback_used
            
            print(f"\n📊 REPORTE DE VALORIZACIÓN:")
            print(f"   - Total intentos: {self.valorization_attempts}")
            print(f"   - Fallos de market data: {self.valorization_failures} ({market_data_failure_rate:.1f}%)")
            print(f"   - BSM fallback usado: {self.bsm_fallback_used} ({bsm_usage_rate:.1f}%)")
            print(f"   - Fallos totales (skip): {total_failures}")
            print(f"   - Éxitos (market data): {self.valorization_attempts - self.valorization_failures}")
            
            if market_data_failure_rate > 50:
                print(f"   ℹ️  INFO: >50% de legs sin market data → BSM fallback activado")
            if total_failures > 0:
                print(f"   ⚠️  ALERTA: {total_failures} intentos sin valoración (ni market data ni BSM)")

        
        # 7. Calcular resultados consolidados
        return self._calculate_multi_ticker_results()
    
    def _manage_all_positions(self, current_date: datetime):
        """
        Gestiona TODAS las posiciones existentes de todos los tickers.
        
        Args:
            current_date: Fecha actual
        """
        positions_to_close = []
        
        for position in self.positions:
            # Obtener ticker de la posición
            ticker = position.ticker
            
            # Verificar si venció
            if current_date >= position.expiration_date:
                underlying_price = self.data_loader.get_underlying_price(ticker, current_date)
                if underlying_price:
                    pnl = self._calculate_expiry_pnl(position, underlying_price)
                    position.pnl = pnl
                    position.exit_date = current_date
                    position.days_held = (current_date - position.entry_date).days
                    position.status = 'expired_profitable' if pnl > 0 else 'expired_loss'
                    positions_to_close.append(position)
                continue
            
            # Obtener precio del subyacente
            underlying_price = self.data_loader.get_underlying_price(ticker, current_date)
            if not underlying_price:
                continue
            
            # Calcular valor actual de la posición
            current_value = self._calculate_position_value(
                ticker, position, current_date, underlying_price
            )
            
            # 🆕 Tracking de valorización
            self.valorization_attempts += 1
            
            if current_value is None:
                self.valorization_failures += 1
                
                # 🆕 FALLBACK: Intentar valorar con Black-Scholes
                current_value = self._estimate_value_with_model(
                    ticker, position, current_date, underlying_price
                )
                
                if current_value is None:
                    # Si aún no podemos valorar, skip este día
                    # DEBUG: Mostrar cuando falla completamente
                    # print(f"  ⚠️  No se pudo valorar {ticker} en {current_date.date()} "
                    #       f"(DTE={position.dte_at_entry}, Expiración={position.expiration_date.date()})")
                    continue
                else:
                    # Se usó BSM fallback exitosamente
                    self.bsm_fallback_used += 1
                    # DEBUG: Indicar que se usó fallback
                    # print(f"  ℹ️  Usando BSM fallback para {ticker} en {current_date.date()}")
                    pass
            
            # Calcular PnL actual
            current_pnl = position.premium_collected - current_value
            
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
    
    def _find_multi_ticker_opportunities(self, current_date: datetime):
        """
        VERSIÓN MEJORADA: Busca oportunidades en TODOS los tickers simultáneamente
        y selecciona las mejores basándose en quality score.
        
        Args:
            current_date: Fecha actual
        """
        print(f"\n🔍 Buscando oportunidades en {len(self.valid_tickers)} tickers...")
        
        # 1. RECOLECTAR todas las oportunidades de todos los tickers
        all_opportunities: List[OpportunityCandidate] = []
        
        for ticker in self.valid_tickers:
            # Verificar límite por ticker
            ticker_positions = [p for p in self.positions if p.ticker == ticker]
            if len(ticker_positions) >= self.config.max_positions_per_ticker:
                print(f"  ⏭️  {ticker}: Límite alcanzado ({len(ticker_positions)}/{self.config.max_positions_per_ticker})")
                continue
            
            # Obtener precio del subyacente
            underlying_price = self.data_loader.get_underlying_price(ticker, current_date)
            if not underlying_price:
                print(f"  ⚠️  {ticker}: Sin precio subyacente")
                continue
            
            # Obtener opciones disponibles
            options = self.data_loader.get_options_for_date(ticker, current_date)
            if len(options) == 0:
                print(f"  ⚠️  {ticker}: Sin opciones disponibles")
                continue
            
            # Corregir deltas de puts
            options = options.copy()
            options.loc[options['type'] == 'put', 'delta'] = abs(options.loc[options['type'] == 'put', 'delta'])
            
            # Preparar market_data
            iv_values = options['iv'].dropna().values
            if len(iv_values) > 0:
                current_iv = np.median(iv_values)
                iv_rank = 70  # Simplificado
            else:
                current_iv = 0.25
                iv_rank = 70
            
            market_data = {
                'underlying_price': underlying_price,
                'iv_rank': iv_rank,
                'current_iv': current_iv
            }
            
            # Escanear cada estrategia
            for strategy_name, strategy in self.strategies.items():
                # Verificar capital disponible
                required_capital = 5000
                if self.capital < required_capital:
                    continue
                
                try:
                    # Escanear oportunidades
                    opportunities_df = strategy.scan(options, market_data)
                    
                    if opportunities_df is None or len(opportunities_df) == 0:
                        continue
                    
                    # Procesar cada oportunidad encontrada (tomar top 3)
                    for idx in range(min(3, len(opportunities_df))):
                        opp_data = opportunities_df.iloc[idx]
                        
                        # Construir posición
                        position = strategy.construct_position(opp_data)
                        
                        if position:
                            # Ajustar ticker y fecha
                            position.ticker = ticker
                            position.entry_date = current_date
                            
                            # 🆕 APLICAR PARÁMETROS ADAPTATIVOS POR TICKER
                            adaptive_params = self.adaptive_config.get_config(ticker)
                            
                            # Recalcular profit target y stop loss con parámetros adaptativos
                            position.profit_target = self.adaptive_config.get_profit_target(
                                ticker, position.premium_collected
                            )
                            position.stop_loss = self.adaptive_config.get_stop_loss(
                                ticker, position.max_risk
                            )
                            
                            # 🆕 Log de parámetros aplicados (debug)
                            # print(f"    {ticker} Adaptive: PT={adaptive_params.profit_target_pct}% "
                            #       f"(${position.profit_target:.2f}), "
                            #       f"SL={adaptive_params.stop_loss_pct}% (${position.stop_loss:.2f})")
                            
                            # Calcular quality score
                            quality_score, metrics = OpportunityScorer.calculate_quality_score(
                                opp_data, position, market_data
                            )
                            
                            # Crear candidato
                            candidate = OpportunityCandidate(
                                ticker=ticker,
                                strategy_name=strategy_name,
                                opportunity_data=opp_data,
                                position=position,
                                quality_score=quality_score,
                                ror=metrics['ror'],
                                credit=metrics['credit'],
                                liquidity_score=metrics['liquidity_score'],
                                iv_rank=metrics['iv_rank'],
                                delta_quality=metrics['delta_quality']
                            )
                            
                            all_opportunities.append(candidate)
                            
                except Exception as e:
                    print(f"  ⚠️  Error escaneando {ticker} {strategy_name}: {e}")
                    continue
        
        # 2. RANKEAR todas las oportunidades por quality score
        if len(all_opportunities) == 0:
            print(f"  ❌ No se encontraron oportunidades este día")
            return
        
        # Ordenar por quality score descendente
        all_opportunities.sort(key=lambda x: x.quality_score, reverse=True)
        
        print(f"\n📊 Oportunidades encontradas: {len(all_opportunities)}")
        print(f"{'Rank':<6} {'Ticker':<8} {'Strategy':<15} {'Score':<8} {'RoR':<10} {'Credit':<10}")
        print("="*70)
        
        for i, opp in enumerate(all_opportunities[:10], 1):  # Mostrar top 10
            print(f"{i:<6} {opp.ticker:<8} {opp.strategy_name:<15} "
                  f"{opp.quality_score:.3f}    {opp.ror:>6.1f}%    ${opp.credit:>7.2f}")
        
        # 3. SELECCIONAR las mejores oportunidades respetando límites
        positions_added = 0
        
        for candidate in all_opportunities:
            # Verificar límite total
            if len(self.positions) >= self.config.max_positions:
                print(f"\n⚠️  Límite total de posiciones alcanzado ({self.config.max_positions})")
                break
            
            # Verificar límite por ticker nuevamente (pudo cambiar)
            ticker_positions = [p for p in self.positions if p.ticker == candidate.ticker]
            if len(ticker_positions) >= self.config.max_positions_per_ticker:
                continue
            
            # Verificar capital disponible
            if self.capital < abs(candidate.position.max_risk):
                print(f"\n⚠️  Capital insuficiente para {candidate.ticker}")
                continue
            
            # AGREGAR POSICIÓN
            self.positions.append(candidate.position)
            self.capital -= abs(candidate.position.max_risk)
            positions_added += 1
            
            print(f"\n  ✅ Posición #{positions_added}: {candidate.ticker} {candidate.strategy_name}")
            print(f"     Score: {candidate.quality_score:.3f} | RoR: {candidate.ror:.1f}% | "
                  f"Crédito: ${candidate.credit:.2f} | DTE: {candidate.position.dte_at_entry}")
        
        if positions_added == 0:
            print(f"\n  ⚠️  No se agregaron posiciones (restricciones de capital/límites)")
        else:
            print(f"\n  🎯 Total posiciones agregadas: {positions_added}")
    
    def _record_multi_ticker_equity(self, current_date: datetime):
        """
        Registra equity diario considerando todas las posiciones de todos los tickers.
        
        Args:
            current_date: Fecha actual
        """
        # Calcular valor de posiciones abiertas
        open_positions_value = 0
        for position in self.positions:
            ticker = position.ticker
            underlying_price = self.data_loader.get_underlying_price(ticker, current_date)
            if underlying_price:
                current_value = self._calculate_position_value(
                    ticker, position, current_date, underlying_price
                )
                if current_value:
                    open_positions_value += position.premium_collected - current_value
        
        # Capital total
        reserved_capital = sum(abs(p.max_risk) for p in self.positions)
        total_equity = self.capital + open_positions_value + reserved_capital
        
        self.equity_curve.append({
            'date': current_date,
            'equity': total_equity,
            'cash': self.capital,
            'open_positions': len(self.positions),
            'closed_positions': len(self.closed_positions)
        })
    
    def _close_all_remaining_positions(self, final_date: datetime):
        """
        Cierra todas las posiciones restantes al final del backtest.
        
        Args:
            final_date: Fecha final
        """
        for position in self.positions[:]:
            ticker = position.ticker
            underlying_price = self.data_loader.get_underlying_price(ticker, final_date)
            
            if underlying_price:
                pnl = self._calculate_expiry_pnl(position, underlying_price)
                position.pnl = pnl
                position.exit_date = final_date
                position.days_held = (final_date - position.entry_date).days
                position.status = 'closed_end'
                self.closed_positions.append(position)
                self.capital += abs(position.max_risk)
        
        self.positions.clear()
    
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
            return None
        
        # Calcular valor de cada leg
        total_value = 0.0
        legs_found = 0
        
        for leg in position.legs:
            leg_mask = (
                (available_options['strike'] == leg['strike']) &
                (available_options['type'] == leg['type'])
            )
            
            leg_data = available_options[leg_mask]
            
            if len(leg_data) == 0:
                continue
            
            leg_price = leg_data.iloc[0]['close']
            if pd.isna(leg_price):
                leg_price = leg_data.iloc[0]['vwap']
            
            if pd.isna(leg_price):
                continue
            
            legs_found += 1
            
            if leg['position'] == 'short':
                total_value += leg_price * 100
            else:
                total_value -= leg_price * 100
        
        if legs_found == len(position.legs):
            return total_value
        else:
            return None
    
    def _estimate_value_with_model(self, ticker: str, position: Position,
                                   current_date: datetime, underlying_price: float) -> Optional[float]:
        """
        🆕 FALLBACK: Estima el valor de una posición usando Black-Scholes cuando
        no hay datos de mercado suficientes.
        
        Args:
            ticker: Símbolo del ticker
            position: Posición a valorar
            current_date: Fecha actual
            underlying_price: Precio actual del subyacente
            
        Returns:
            Valor estimado o None si no se puede calcular
        """
        # Verificar que tengamos Black-Scholes disponible
        if not BSM_AVAILABLE or black_scholes_price is None:
            return None
        
        # Cargar datos para estimar IV
        df = self.data_loader.load_ticker_data(ticker)
        
        # Filtrar opciones cercanas a la fecha y vencimiento
        mask = (
            (df['date'] == current_date) & 
            (df['expiration'] == position.expiration_date)
        )
        available_options = df[mask]
        
        # Estimar IV promedio (usar mediana para robustez)
        if len(available_options) > 0:
            iv_values = available_options['iv'].dropna()
            if len(iv_values) > 0:
                estimated_iv = iv_values.median()
            else:
                estimated_iv = 0.25  # Default si no hay IV
        else:
            estimated_iv = 0.25
        
        # Calcular días hasta vencimiento
        days_to_expiry = (position.expiration_date - current_date).days
        if days_to_expiry <= 0:
            # Si ya venció, usar valor intrínseco
            return 0.0
        
        # Convertir días a años
        time_to_expiry = days_to_expiry / 365.0
        
        # Tasa libre de riesgo (simplificado)
        risk_free_rate = 0.05
        
        # Calcular valor de cada leg usando Black-Scholes
        total_value = 0.0
        
        try:
            for leg in position.legs:
                # Calcular precio teórico usando la función black_scholes_price
                theoretical_price = black_scholes_price(
                    S=underlying_price,
                    K=leg['strike'],
                    T=time_to_expiry,
                    r=risk_free_rate,
                    sigma=estimated_iv,
                    option_type=leg['type']  # 'call' o 'put'
                )
                
                # Multiplicar por 100 (tamaño del contrato)
                theoretical_value = theoretical_price * 100
                
                # Ajustar según posición (short/long)
                if leg['position'] == 'short':
                    total_value += theoretical_value
                else:
                    total_value -= theoretical_value
            
            return total_value
            
        except Exception as e:
            # Si hay algún error en el cálculo BSM, retornar None
            # print(f"  ⚠️  Error en BSM fallback: {e}")
            return None
    
    def _calculate_expiry_pnl(self, position: Position, final_price: float) -> float:
        """
        Calcula PnL al vencimiento basado en valor intrínseco.
        
        Args:
            position: Posición que vence
            final_price: Precio final del subyacente
            
        Returns:
            PnL final
        """
        total_intrinsic_value = 0.0
        
        for leg in position.legs:
            if leg['type'] == 'call':
                intrinsic = max(0, final_price - leg['strike'])
            else:
                intrinsic = max(0, leg['strike'] - final_price)
            
            intrinsic_value = intrinsic * 100
            
            if leg['position'] == 'short':
                total_intrinsic_value += intrinsic_value
            else:
                total_intrinsic_value -= intrinsic_value
        
        pnl = position.premium_collected - total_intrinsic_value
        return pnl
    
    def _calculate_multi_ticker_results(self) -> Dict:
        """
        Calcula métricas de performance para backtesting multi-ticker.
        
        Returns:
            Diccionario con resultados consolidados + por ticker
        """
        if len(self.closed_positions) == 0:
            return {
                'summary': {
                    'total_trades': 0,
                    'capital_inicial': self.config.initial_capital,
                    'capital_final': self.capital
                }
            }
        
        # Convertir posiciones a DataFrame
        trades_data = []
        for pos in self.closed_positions:
            trades_data.append({
                'ticker': pos.ticker,  # 🆕 Incluir ticker
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
        
        gross_profit = winners['pnl'].sum() if len(winners) > 0 else 0
        gross_loss = abs(losers['pnl'].sum()) if len(losers) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        expectancy = (win_rate * avg_winner) + ((1 - win_rate) * avg_loser)
        
        returns_series = df_trades['return_pct']
        sharpe_ratio = self._calculate_sharpe(returns_series)
        
        max_drawdown, max_dd_pct = self._calculate_max_drawdown(df_trades)
        
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
        
        # === 🆕 MÉTRICAS POR TICKER ===
        ticker_metrics = {}
        for ticker in df_trades['ticker'].unique():
            ticker_df = df_trades[df_trades['ticker'] == ticker]
            ticker_winners = ticker_df[ticker_df['profitable']]
            
            ticker_metrics[ticker] = {
                'trades': len(ticker_df),
                'win_rate': len(ticker_winners) / len(ticker_df) if len(ticker_df) > 0 else 0,
                'avg_return': ticker_df['return_pct'].mean(),
                'avg_days_held': ticker_df['days_held'].mean(),
                'total_pnl': ticker_df['pnl'].sum(),
                'total_premium': ticker_df['premium_collected'].sum()
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
            'by_ticker': ticker_metrics,  # 🆕 Métricas por ticker
            'by_dte': dte_metrics,
            'raw_data': df_trades,
            'equity_curve': pd.DataFrame(self.equity_curve) if self.equity_curve else pd.DataFrame()
        }
    
    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.03) -> float:
        """Calcula Sharpe Ratio."""
        if len(returns) < 2:
            return 0.0
        
        returns_decimal = returns / 100
        excess_returns = returns_decimal - (risk_free_rate / 252)
        
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        return sharpe
    
    def _calculate_max_drawdown(self, trades_df: pd.DataFrame) -> Tuple[float, float]:
        """Calcula máximo drawdown."""
        if not self.equity_curve or len(self.equity_curve) == 0:
            return (0.0, 0.0)
        
        equity_series = pd.Series([eq['equity'] for eq in self.equity_curve])
        running_max = equity_series.expanding().max()
        drawdown = equity_series - running_max
        drawdown_pct = (drawdown / running_max) * 100
        
        max_dd = drawdown.min()
        max_dd_pct = drawdown_pct.min()
        
        return (max_dd, max_dd_pct)