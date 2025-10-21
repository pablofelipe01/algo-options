"""
Configuración Adaptativa de Parámetros por Ticker
Implementa parámetros dinámicos de profit targets, stop losses y DTE ranges
basados en volatilidad histórica y tipo de activo.

Autor: Sistema de Trading Algorítmico
Fecha: Fase 2 - TODO #5
"""

from dataclasses import dataclass
from typing import Dict, Tuple
from enum import Enum


class VolatilityCategory(Enum):
    """Categorías de volatilidad basadas en IV histórico."""
    HIGH = "High"      # IV Mean >= 0.40
    MEDIUM = "Medium"  # 0.25 <= IV Mean < 0.40
    LOW = "Low"        # IV Mean < 0.25


class AssetType(Enum):
    """Tipos de activos para estrategias diferenciadas."""
    ETF = "ETF"
    TECH = "Tech"
    COMMODITY = "Commodity"


@dataclass
class TickerParameters:
    """Parámetros adaptativos para un ticker específico."""
    ticker: str
    asset_type: AssetType
    volatility_category: VolatilityCategory
    
    # Risk management parameters
    profit_target_pct: float  # % del crédito/premium
    stop_loss_pct: float      # % del max_risk
    
    # Entry parameters
    dte_min: int
    dte_max: int
    
    # Reasoning (para debugging/documentación)
    reasoning: str = ""
    
    def __repr__(self):
        return (f"TickerParameters({self.ticker}: "
                f"PT={self.profit_target_pct}%, SL={self.stop_loss_pct}%, "
                f"DTE={self.dte_min}-{self.dte_max})")


class AdaptiveConfigManager:
    """
    Gestor centralizado de configuraciones adaptativas por ticker.
    
    Basado en análisis empírico de:
    - Volatilidad histórica (IV mean de 60 días)
    - Performance por ticker en backtests
    - Tipo de activo (ETF, Tech, Commodity)
    """
    
    # Configuración base por volatilidad
    VOLATILITY_CONFIGS = {
        VolatilityCategory.HIGH: {
            'profit_target_pct': 25.0,
            'stop_loss_pct': 200.0,
            'reasoning': "Alta volatilidad → cerrar rápido para capturar theta, stop loss amplio anti-whipsaw"
        },
        VolatilityCategory.MEDIUM: {
            'profit_target_pct': 35.0,
            'stop_loss_pct': 150.0,
            'reasoning': "Volatilidad media → balance entre theta y protección"
        },
        VolatilityCategory.LOW: {
            'profit_target_pct': 50.0,
            'stop_loss_pct': 100.0,
            'reasoning': "Baja volatilidad → permitir mayor decay de theta, stop loss ajustado"
        }
    }
    
    # DTE ranges por tipo de activo
    DTE_CONFIGS = {
        AssetType.ETF: {
            'dte_min': 49,
            'dte_max': 56,
            'reasoning': "ETF → Long DTE (49-56) para estabilidad y aprovechar theta decay gradual"
        },
        AssetType.TECH: {
            'dte_min': 42,
            'dte_max': 49,
            'reasoning': "Tech → Medium-Long DTE (42-49) para capturar ciclos de volatilidad"
        },
        AssetType.COMMODITY: {
            'dte_min': 56,
            'dte_max': 60,
            'reasoning': "Commodity → Extra Long DTE (56-60) para aprovechar tendencias largas"
        }
    }
    
    # Clasificación de tickers
    TICKER_CLASSIFICATIONS = {
        # ETFs
        'SPY': (AssetType.ETF, VolatilityCategory.MEDIUM),
        'QQQ': (AssetType.ETF, VolatilityCategory.MEDIUM),
        'IWM': (AssetType.ETF, VolatilityCategory.HIGH),
        
        # Tech Stocks
        'AAPL': (AssetType.TECH, VolatilityCategory.HIGH),
        'MSFT': (AssetType.TECH, VolatilityCategory.HIGH),
        'AMZN': (AssetType.TECH, VolatilityCategory.HIGH),
        'NVDA': (AssetType.TECH, VolatilityCategory.HIGH),
        'TSLA': (AssetType.TECH, VolatilityCategory.HIGH),
        
        # Commodities
        'GLD': (AssetType.COMMODITY, VolatilityCategory.HIGH),
        'SLV': (AssetType.COMMODITY, VolatilityCategory.HIGH),
    }
    
    # Ajustes especiales por ticker (basados en performance histórica)
    TICKER_OVERRIDES = {
        'TSLA': {
            'profit_target_pct': 20.0,  # Más agresivo (75% early closures, 100% win rate)
            'reasoning_override': "TSLA → Profit target ultra-agresivo (75% early closures observados)"
        },
        'QQQ': {
            'profit_target_pct': 30.0,  # Ajuste por buenos resultados con cierres anticipados
            'reasoning_override': "QQQ → Ajustado por 71.4% early closure rate"
        },
        'SPY': {
            'profit_target_pct': 30.0,  # Similar a QQQ
            'reasoning_override': "SPY → Ajustado por 71.4% early closure rate"
        }
    }
    
    def __init__(self):
        """Inicializa el gestor y precarga configuraciones."""
        self._config_cache: Dict[str, TickerParameters] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Precarga configuraciones para todos los tickers conocidos."""
        for ticker in self.TICKER_CLASSIFICATIONS.keys():
            self._config_cache[ticker] = self._build_config(ticker)
    
    def _build_config(self, ticker: str) -> TickerParameters:
        """
        Construye configuración para un ticker específico.
        
        Args:
            ticker: Símbolo del ticker
            
        Returns:
            TickerParameters con configuración adaptativa
        """
        # Obtener clasificación
        if ticker not in self.TICKER_CLASSIFICATIONS:
            # Ticker desconocido: usar configuración conservadora (Medium Vol, ETF)
            asset_type = AssetType.ETF
            vol_category = VolatilityCategory.MEDIUM
            reasoning = f"{ticker} → Ticker desconocido, usando configuración conservadora"
        else:
            asset_type, vol_category = self.TICKER_CLASSIFICATIONS[ticker]
            reasoning = ""
        
        # Obtener configuración base por volatilidad
        vol_config = self.VOLATILITY_CONFIGS[vol_category]
        profit_target = vol_config['profit_target_pct']
        stop_loss = vol_config['stop_loss_pct']
        reasoning += vol_config['reasoning']
        
        # Obtener DTE range por tipo de activo
        dte_config = self.DTE_CONFIGS[asset_type]
        dte_min = dte_config['dte_min']
        dte_max = dte_config['dte_max']
        reasoning += f" | {dte_config['reasoning']}"
        
        # Aplicar overrides específicos por ticker
        if ticker in self.TICKER_OVERRIDES:
            override = self.TICKER_OVERRIDES[ticker]
            if 'profit_target_pct' in override:
                profit_target = override['profit_target_pct']
            if 'stop_loss_pct' in override:
                stop_loss = override['stop_loss_pct']
            if 'reasoning_override' in override:
                reasoning = f"{override['reasoning_override']} | {reasoning}"
        
        return TickerParameters(
            ticker=ticker,
            asset_type=asset_type,
            volatility_category=vol_category,
            profit_target_pct=profit_target,
            stop_loss_pct=stop_loss,
            dte_min=dte_min,
            dte_max=dte_max,
            reasoning=reasoning
        )
    
    def get_config(self, ticker: str) -> TickerParameters:
        """
        Obtiene configuración para un ticker.
        
        Args:
            ticker: Símbolo del ticker
            
        Returns:
            TickerParameters con configuración adaptativa
        """
        if ticker not in self._config_cache:
            # Construir on-the-fly si no está en cache
            self._config_cache[ticker] = self._build_config(ticker)
        
        return self._config_cache[ticker]
    
    def get_dte_range(self, ticker: str) -> Tuple[int, int]:
        """
        Obtiene rango de DTE recomendado para un ticker.
        
        Args:
            ticker: Símbolo del ticker
            
        Returns:
            (dte_min, dte_max)
        """
        config = self.get_config(ticker)
        return (config.dte_min, config.dte_max)
    
    def get_profit_target(self, ticker: str, premium_collected: float) -> float:
        """
        Calcula profit target en dólares para un ticker.
        
        Args:
            ticker: Símbolo del ticker
            premium_collected: Premium cobrado en la posición
            
        Returns:
            Profit target en dólares
        """
        config = self.get_config(ticker)
        return premium_collected * (config.profit_target_pct / 100.0)
    
    def get_stop_loss(self, ticker: str, max_risk: float) -> float:
        """
        Calcula stop loss en dólares para un ticker.
        
        Args:
            ticker: Símbolo del ticker
            max_risk: Riesgo máximo de la posición (absolute value)
            
        Returns:
            Stop loss en dólares
        """
        config = self.get_config(ticker)
        return abs(max_risk) * (config.stop_loss_pct / 100.0)
    
    def print_all_configs(self):
        """Imprime todas las configuraciones cargadas."""
        print("\n" + "="*70)
        print("📋 CONFIGURACIONES ADAPTATIVAS POR TICKER")
        print("="*70)
        
        # Agrupar por tipo de activo
        for asset_type in AssetType:
            tickers = [t for t, config in self._config_cache.items() 
                      if config.asset_type == asset_type]
            
            if not tickers:
                continue
            
            print(f"\n{asset_type.value}:")
            for ticker in sorted(tickers):
                config = self._config_cache[ticker]
                print(f"  {ticker:<6} | PT: {config.profit_target_pct:>5.1f}% | "
                      f"SL: {config.stop_loss_pct:>5.1f}% | "
                      f"DTE: {config.dte_min}-{config.dte_max} días | "
                      f"Vol: {config.volatility_category.value}")
    
    def get_strategy_params_for_ticker(self, ticker: str) -> Dict:
        """
        Retorna diccionario con todos los parámetros para usar en Strategy.
        
        Args:
            ticker: Símbolo del ticker
            
        Returns:
            Dict con todos los parámetros
        """
        config = self.get_config(ticker)
        
        return {
            'dte_min': config.dte_min,
            'dte_max': config.dte_max,
            'profit_target_pct': config.profit_target_pct,
            'stop_loss_pct': config.stop_loss_pct,
            'asset_type': config.asset_type.value,
            'volatility_category': config.volatility_category.value,
            'reasoning': config.reasoning
        }


# ============================================================================
# INSTANCIA GLOBAL (Singleton pattern simplificado)
# ============================================================================

_adaptive_config_manager = None

def get_adaptive_config_manager() -> AdaptiveConfigManager:
    """
    Obtiene la instancia global del gestor de configuración adaptativa.
    
    Returns:
        AdaptiveConfigManager singleton
    """
    global _adaptive_config_manager
    if _adaptive_config_manager is None:
        _adaptive_config_manager = AdaptiveConfigManager()
    return _adaptive_config_manager


# ============================================================================
# DEMO / TESTING
# ============================================================================

if __name__ == "__main__":
    # Demostración del uso
    manager = get_adaptive_config_manager()
    
    print("\n" + "="*70)
    print("🎯 DEMO: ADAPTIVE CONFIG MANAGER")
    print("="*70)
    
    # Mostrar todas las configuraciones
    manager.print_all_configs()
    
    # Ejemplos de uso
    print("\n" + "="*70)
    print("📝 EJEMPLOS DE USO")
    print("="*70)
    
    test_tickers = ['TSLA', 'SPY', 'GLD']
    
    for ticker in test_tickers:
        print(f"\n{ticker}:")
        config = manager.get_config(ticker)
        print(f"  Configuración: {config}")
        
        # Simular una posición
        premium = 500.0
        max_risk = 2500.0
        
        profit_target = manager.get_profit_target(ticker, premium)
        stop_loss = manager.get_stop_loss(ticker, max_risk)
        dte_min, dte_max = manager.get_dte_range(ticker)
        
        print(f"\n  Ejemplo con Premium=${premium:.2f}, Max Risk=${max_risk:.2f}:")
        print(f"    - Profit Target: ${profit_target:.2f} ({config.profit_target_pct}% del premium)")
        print(f"    - Stop Loss: ${stop_loss:.2f} ({config.stop_loss_pct}% del max risk)")
        print(f"    - DTE Range: {dte_min}-{dte_max} días")
        print(f"    - Reasoning: {config.reasoning}")
    
    print("\n✅ Demo completado")
