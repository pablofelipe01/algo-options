# scripts/quantitative/__init__.py
"""
Módulo de Modelado Cuantitativo para Trading de Opciones
=========================================================

Este paquete implementa:
- Modelo Black-Scholes-Merton (BSM)
- Cálculo de griegas
- Probabilidad de Beneficio (PoP)
- Validación de modelos

Uso:
    from quantitative import black_scholes_price, calculate_greeks
    from quantitative import calculate_pop_empirical, calculate_pop_monte_carlo
    from quantitative import compare_greeks, validate_bsm_implementation
"""

__version__ = "1.0.0"
__author__ = "Sistema de Trading de Opciones"

# Utilidades
from .utils import (
    annualize_volatility,
    days_to_years,
    get_risk_free_rate,
    validate_inputs,
    format_greek
)

# Black-Scholes (✅ IMPLEMENTADO)
from .black_scholes import (
    black_scholes_price,
    calculate_greeks,
    calculate_d1_d2
)

# Probabilidad de Beneficio (✅ IMPLEMENTADO)
from .probability import (
    calculate_pop_empirical,
    calculate_pop_monte_carlo,
    compare_pop_methods
)

# Validación (✅ IMPLEMENTADO)
from .validation import (
    compare_greeks,
    validate_bsm_implementation,
    analyze_option_mispricing
)

__all__ = [
    # Black-Scholes
    'black_scholes_price',
    'calculate_greeks',
    'calculate_d1_d2',
    
    # Probabilidad
    'calculate_pop_empirical',
    'calculate_pop_monte_carlo',
    'compare_pop_methods',
    
    # Validación
    'compare_greeks',
    'validate_bsm_implementation',
    'analyze_option_mispricing',
    
    # Utilidades
    'annualize_volatility',
    'days_to_years',
    'get_risk_free_rate',
    'validate_inputs',
    'format_greek',
]