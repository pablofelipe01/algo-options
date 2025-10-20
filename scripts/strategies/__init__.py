# scripts/strategies/__init__.py
"""
Módulo de Estrategias de Trading de Opciones
=============================================

Implementación de estrategias cuantitativas con reglas no discrecionales:
- Iron Condor (15-60 DTE)
- Covered Call (income y assignment)
- Filtros de selección
- Gestión de riesgo adaptativa

Todas las estrategias heredan de StrategyBase y siguen reglas cuantitativas
definidas en el documento de estrategias modificadas.
"""

__version__ = "1.0.0"

# Clases base
from .base import StrategyBase, StrategyRules, Position

# Filtros
from .filters import (
    LiquidityFilter,
    VolatilityFilter,
    DeltaFilter,
    DTEFilter,
    OptionSelector
)

# Gestión de riesgo
from .risk_manager import RiskManager, RiskParameters

# Estrategias
from .iron_condor import IronCondor
from .covered_call import CoveredCall

__all__ = [
    # Base
    'StrategyBase',
    'StrategyRules',
    'Position',
    
    # Filtros
    'LiquidityFilter',
    'VolatilityFilter',
    'DeltaFilter',
    'DTEFilter',
    'OptionSelector',
    
    # Risk Management
    'RiskManager',
    'RiskParameters',
    
    # Estrategias
    'IronCondor',
    'CoveredCall',
]