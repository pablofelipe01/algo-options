# scripts/quantitative/utils.py
"""
Utilidades para Modelado Cuantitativo
======================================

Funciones helper para conversiones, validaciones y constantes.
"""

import numpy as np
from typing import Union


# Constantes
TRADING_DAYS_PER_YEAR = 252
CALENDAR_DAYS_PER_YEAR = 365
DEFAULT_RISK_FREE_RATE = 0.05  # 5% anualizado


def days_to_years(days: Union[int, float], calendar_days: bool = True) -> float:
    """
    Convierte días a años para cálculos de Black-Scholes.
    
    Parámetros:
    -----------
    days : int o float
        Número de días
    calendar_days : bool
        True = usar 365 días/año (default)
        False = usar 252 días trading/año
    
    Retorna:
    --------
    float
        Fracción de año
    
    Ejemplo:
    --------
    >>> days_to_years(30)  # 30 días calendario
    0.0821917808219178
    >>> days_to_years(30, calendar_days=False)  # 30 días trading
    0.11904761904761904
    """
    divisor = CALENDAR_DAYS_PER_YEAR if calendar_days else TRADING_DAYS_PER_YEAR
    return days / divisor


def annualize_volatility(daily_vol: float, trading_days: bool = True) -> float:
    """
    Anualiza volatilidad diaria.
    
    Parámetros:
    -----------
    daily_vol : float
        Volatilidad diaria (ej. 0.02 = 2% diario)
    trading_days : bool
        True = usar sqrt(252) (default)
        False = usar sqrt(365)
    
    Retorna:
    --------
    float
        Volatilidad anualizada
    
    Ejemplo:
    --------
    >>> annualize_volatility(0.02)  # 2% diario
    0.31749015789389575  # ~31.7% anualizado
    """
    factor = np.sqrt(TRADING_DAYS_PER_YEAR if trading_days else CALENDAR_DAYS_PER_YEAR)
    return daily_vol * factor


def get_risk_free_rate(default: float = DEFAULT_RISK_FREE_RATE) -> float:
    """
    Obtiene la tasa libre de riesgo actual.
    
    Por ahora retorna una tasa por defecto.
    TODO: En el futuro, obtener de FRED API o Treasury yields.
    
    Parámetros:
    -----------
    default : float
        Tasa por defecto si no se puede obtener datos externos
    
    Retorna:
    --------
    float
        Tasa libre de riesgo anualizada (ej. 0.05 = 5%)
    """
    # TODO: Implementar obtención desde FRED API
    # from fredapi import Fred
    # fred = Fred(api_key='YOUR_KEY')
    # rate = fred.get_series_latest_release('DGS10') / 100  # 10Y Treasury
    
    return default


def validate_inputs(S: float, K: float, T: float, r: float, sigma: float) -> None:
    """
    Valida que los inputs de Black-Scholes sean correctos.
    
    Lanza:
    ------
    ValueError si algún parámetro es inválido
    """
    if S <= 0:
        raise ValueError(f"Precio del subyacente debe ser > 0, recibido: {S}")
    if K <= 0:
        raise ValueError(f"Strike price debe ser > 0, recibido: {K}")
    if T <= 0:
        raise ValueError(f"Tiempo hasta vencimiento debe ser > 0, recibido: {T}")
    if sigma <= 0:
        raise ValueError(f"Volatilidad debe ser > 0, recibida: {sigma}")
    if r < -1 or r > 1:
        raise ValueError(f"Tasa de interés parece incorrecta, recibida: {r}")


def format_greek(value: float, greek_name: str) -> str:
    """
    Formatea una griega para impresión legible.
    
    Parámetros:
    -----------
    value : float
        Valor de la griega
    greek_name : str
        Nombre de la griega ('delta', 'gamma', etc.)
    
    Retorna:
    --------
    str
        String formateado
    """
    formats = {
        'delta': f"{value:.4f}",
        'gamma': f"{value:.6f}",
        'vega': f"{value:.4f}",
        'theta': f"{value:.4f}",
        'rho': f"{value:.4f}"
    }
    return formats.get(greek_name.lower(), f"{value:.6f}")


# Test del módulo
if __name__ == "__main__":
    print("=" * 70)
    print("Testing: Utilidades Cuantitativas")
    print("=" * 70)
    
    print("\n1. Conversión de tiempo:")
    print(f"   30 días calendario = {days_to_years(30):.6f} años")
    print(f"   30 días trading = {days_to_years(30, calendar_days=False):.6f} años")
    
    print("\n2. Anualización de volatilidad:")
    print(f"   2% diario = {annualize_volatility(0.02):.2%} anualizado")
    
    print("\n3. Tasa libre de riesgo:")
    print(f"   Tasa actual: {get_risk_free_rate():.2%}")
    
    print("\n4. Validación de inputs:")
    try:
        validate_inputs(S=100, K=105, T=0.0821, r=0.05, sigma=0.25)
        print("   ✓ Inputs válidos")
    except ValueError as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 70)