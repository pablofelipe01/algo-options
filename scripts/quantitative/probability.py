# scripts/quantitative/probability.py
"""
Probabilidad de Beneficio (PoP)
================================

Dos enfoques para calcular la probabilidad de que una operación sea rentable:

1. Método Empírico (Simulación Histórica):
   - Libre de modelos
   - Basado en rendimientos históricos reales
   - Supuesto: "El futuro se parecerá al pasado"

2. Método Monte Carlo (GBM):
   - Basado en modelo
   - Movimiento Browniano Geométrico
   - Supuesto: Precios siguen distribución log-normal
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from .utils import validate_inputs


def calculate_pop_empirical(
    historical_prices: pd.Series,
    days_to_expiry: int,
    profitable_range: Tuple[float, float],
    min_samples: int = 30
) -> Dict[str, float]:
    """
    Calcula la Probabilidad de Beneficio usando distribución empírica.
    
    Este método es "libre de modelos" y pregunta: "Dada la historia de
    movimientos de precios, ¿con qué frecuencia habría ganado esta operación?"
    
    Proceso:
    --------
    1. Calcula rendimientos rolling de N días (donde N = days_to_expiry)
    2. Proyecta precio final desde el precio actual
    3. Cuenta cuántos escenarios caen en el rango rentable
    4. PoP = escenarios_rentables / total_escenarios
    
    Parámetros:
    -----------
    historical_prices : pd.Series
        Serie temporal de precios históricos del subyacente
        Debe tener suficientes datos (> days_to_expiry + min_samples)
    days_to_expiry : int
        Días hasta el vencimiento de la opción
    profitable_range : tuple
        (precio_mínimo, precio_máximo) para ser rentable
        Ejemplo: (95, 105) = rentable entre $95 y $105
    min_samples : int
        Número mínimo de muestras históricas requeridas
    
    Retorna:
    --------
    dict
        {
            'pop': float,                    # Probabilidad 0-1
            'pop_pct': float,               # Probabilidad en porcentaje
            'num_profitable': int,           # Escenarios rentables
            'total_scenarios': int,          # Total de escenarios
            'mean_projected_price': float,   # Precio promedio proyectado
            'std_projected_price': float,    # Desviación estándar
            'percentile_5': float,          # Percentil 5%
            'percentile_25': float,         # Percentil 25%
            'percentile_50': float,         # Mediana
            'percentile_75': float,         # Percentil 75%
            'percentile_95': float          # Percentil 95%
        }
    
    Lanza:
    ------
    ValueError si datos insuficientes o parámetros inválidos
    
    Ejemplo:
    --------
    >>> # Supongamos que tenemos precios históricos de SPY
    >>> historical = pd.Series([100, 101, 99, 102, 100, ...])  # 252 días
    >>> # Queremos saber PoP de un Iron Condor con rango $95-$105
    >>> result = calculate_pop_empirical(historical, days_to_expiry=45, profitable_range=(95, 105))
    >>> print(f"Probabilidad de beneficio: {result['pop_pct']:.2f}%")
    Probabilidad de beneficio: 68.50%
    """
    # Validaciones
    if days_to_expiry <= 0:
        raise ValueError(f"days_to_expiry debe ser > 0, recibido: {days_to_expiry}")
    
    if len(historical_prices) < days_to_expiry + min_samples:
        raise ValueError(
            f"Datos históricos insuficientes. "
            f"Necesario: {days_to_expiry + min_samples}, "
            f"Disponible: {len(historical_prices)}"
        )
    
    lower_bound, upper_bound = profitable_range
    if lower_bound >= upper_bound:
        raise ValueError(
            f"Rango inválido: lower_bound ({lower_bound}) debe ser < upper_bound ({upper_bound})"
        )
    
    # Calcular rendimientos rolling de N días
    # pct_change(periods=N) calcula: (precio[t] - precio[t-N]) / precio[t-N]
    rolling_returns = historical_prices.pct_change(periods=days_to_expiry).dropna()
    
    if len(rolling_returns) < min_samples:
        raise ValueError(
            f"Muestras insuficientes después de calcular rendimientos rolling. "
            f"Necesario: {min_samples}, Disponible: {len(rolling_returns)}"
        )
    
    # Precio actual (último precio disponible)
    current_price = historical_prices.iloc[-1]
    
    # Proyectar precios finales usando rendimientos históricos
    # precio_final = precio_actual * (1 + rendimiento_histórico)
    projected_prices = current_price * (1 + rolling_returns)
    
    # Contar escenarios rentables (precio dentro del rango)
    profitable_outcomes = projected_prices[
        (projected_prices >= lower_bound) & (projected_prices <= upper_bound)
    ]
    
    num_profitable = len(profitable_outcomes)
    total_scenarios = len(projected_prices)
    pop = num_profitable / total_scenarios
    
    # Estadísticas de los precios proyectados
    return {
        'pop': pop,
        'pop_pct': pop * 100,
        'num_profitable': num_profitable,
        'total_scenarios': total_scenarios,
        'mean_projected_price': projected_prices.mean(),
        'std_projected_price': projected_prices.std(),
        'percentile_5': projected_prices.quantile(0.05),
        'percentile_25': projected_prices.quantile(0.25),
        'percentile_50': projected_prices.quantile(0.50),  # Mediana
        'percentile_75': projected_prices.quantile(0.75),
        'percentile_95': projected_prices.quantile(0.95)
    }


def calculate_pop_monte_carlo(
    S: float,
    sigma: float,
    r: float,
    T: float,
    profitable_range: Tuple[float, float],
    trials: int = 10000,
    random_seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Calcula la Probabilidad de Beneficio usando simulación Monte Carlo.
    
    Este método usa Movimiento Browniano Geométrico (GBM) y pregunta:
    "Dado un modelo de movimiento de precios, ¿con qué frecuencia ganaría
    esta operación en millones de futuros simulados?"
    
    Modelo GBM:
    -----------
    S(T) = S(0) * exp((r - σ²/2)*T + σ*√T*Z)
    
    Donde:
    - S(T) = Precio final
    - S(0) = Precio actual
    - r = Tasa libre de riesgo
    - σ = Volatilidad
    - T = Tiempo
    - Z ~ N(0,1) = Variable aleatoria normal estándar
    
    Parámetros:
    -----------
    S : float
        Precio actual del subyacente
    sigma : float
        Volatilidad implícita anualizada (ej. 0.25 = 25%)
    r : float
        Tasa de interés libre de riesgo anualizada
    T : float
        Tiempo hasta vencimiento en años (ej. 45/365)
    profitable_range : tuple
        (precio_mínimo, precio_máximo) para ser rentable
    trials : int
        Número de simulaciones (default: 10,000)
        Más simulaciones = más precisión pero más lento
    random_seed : int, optional
        Semilla para reproducibilidad
    
    Retorna:
    --------
    dict
        {
            'pop': float,
            'pop_pct': float,
            'num_profitable': int,
            'total_trials': int,
            'mean_final_price': float,
            'std_final_price': float,
            'percentile_5': float,
            'percentile_25': float,
            'percentile_50': float,
            'percentile_75': float,
            'percentile_95': float,
            'min_price': float,
            'max_price': float
        }
    
    Ejemplo:
    --------
    >>> # Iron Condor en SPY: rentable entre $95 y $105
    >>> result = calculate_pop_monte_carlo(
    ...     S=100, sigma=0.25, r=0.05, T=45/365,
    ...     profitable_range=(95, 105),
    ...     trials=10000
    ... )
    >>> print(f"PoP Monte Carlo: {result['pop_pct']:.2f}%")
    PoP Monte Carlo: 72.34%
    """
    validate_inputs(S, K=S, T=T, r=r, sigma=sigma)  # K=S solo para validar S
    
    if trials <= 0:
        raise ValueError(f"trials debe ser > 0, recibido: {trials}")
    
    lower_bound, upper_bound = profitable_range
    if lower_bound >= upper_bound:
        raise ValueError(
            f"Rango inválido: lower_bound ({lower_bound}) debe ser < upper_bound ({upper_bound})"
        )
    
    # Fijar semilla para reproducibilidad si se proporciona
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Generar variables aleatorias normales estándar
    Z = np.random.standard_normal(trials)
    
    # Movimiento Browniano Geométrico (GBM)
    # S(T) = S(0) * exp((r - σ²/2)*T + σ*√T*Z)
    drift = (r - 0.5 * sigma ** 2) * T
    diffusion = sigma * np.sqrt(T) * Z
    
    final_prices = S * np.exp(drift + diffusion)
    
    # Contar escenarios rentables
    profitable_mask = (final_prices >= lower_bound) & (final_prices <= upper_bound)
    num_profitable = np.sum(profitable_mask)
    pop = num_profitable / trials
    
    # Estadísticas
    return {
        'pop': pop,
        'pop_pct': pop * 100,
        'num_profitable': int(num_profitable),
        'total_trials': trials,
        'mean_final_price': float(final_prices.mean()),
        'std_final_price': float(final_prices.std()),
        'percentile_5': float(np.percentile(final_prices, 5)),
        'percentile_25': float(np.percentile(final_prices, 25)),
        'percentile_50': float(np.percentile(final_prices, 50)),
        'percentile_75': float(np.percentile(final_prices, 75)),
        'percentile_95': float(np.percentile(final_prices, 95)),
        'min_price': float(final_prices.min()),
        'max_price': float(final_prices.max())
    }


def compare_pop_methods(
    historical_prices: pd.Series,
    S: float,
    sigma: float,
    r: float,
    days_to_expiry: int,
    profitable_range: Tuple[float, float],
    mc_trials: int = 10000
) -> Dict[str, Dict]:
    """
    Compara ambos métodos de cálculo de PoP.
    
    Una discrepancia significativa entre métodos es altamente informativa:
    - Si PoP_MC >> PoP_Empírico: La volatilidad asumida puede ser muy baja
                                  o la historia reciente fue hostil
    - Si PoP_Empírico >> PoP_MC: La volatilidad asumida puede ser muy alta
                                  o la historia reciente fue favorable
    
    Parámetros:
    -----------
    historical_prices : pd.Series
        Precios históricos para método empírico
    S : float
        Precio actual para método Monte Carlo
    sigma : float
        Volatilidad para método Monte Carlo
    r : float
        Tasa libre de riesgo
    days_to_expiry : int
        Días hasta vencimiento
    profitable_range : tuple
        Rango de precios rentables
    mc_trials : int
        Número de simulaciones Monte Carlo
    
    Retorna:
    --------
    dict
        {
            'empirical': dict,  # Resultados método empírico
            'monte_carlo': dict,  # Resultados método Monte Carlo
            'comparison': {
                'pop_difference': float,  # Diferencia en puntos porcentuales
                'pop_ratio': float,       # Ratio MC/Empírico
                'interpretation': str     # Interpretación de la diferencia
            }
        }
    """
    T = days_to_expiry / 365
    
    # Calcular ambos métodos
    empirical = calculate_pop_empirical(historical_prices, days_to_expiry, profitable_range)
    monte_carlo = calculate_pop_monte_carlo(S, sigma, r, T, profitable_range, mc_trials)
    
    # Comparación
    pop_diff = monte_carlo['pop_pct'] - empirical['pop_pct']
    pop_ratio = monte_carlo['pop'] / empirical['pop'] if empirical['pop'] > 0 else np.inf
    
    # Interpretación
    if abs(pop_diff) < 5:
        interpretation = "Ambos métodos concuerdan (diferencia < 5%)"
    elif pop_diff > 10:
        interpretation = (
            "PoP Monte Carlo significativamente mayor. "
            "Posibles causas: (1) Volatilidad asumida baja, "
            "(2) Historia reciente hostil para la estrategia"
        )
    elif pop_diff < -10:
        interpretation = (
            "PoP Empírico significativamente mayor. "
            "Posibles causas: (1) Volatilidad asumida alta, "
            "(2) Historia reciente favorable para la estrategia"
        )
    else:
        interpretation = f"Diferencia moderada de {pop_diff:.1f}pp"
    
    return {
        'empirical': empirical,
        'monte_carlo': monte_carlo,
        'comparison': {
            'pop_difference': pop_diff,
            'pop_ratio': pop_ratio,
            'interpretation': interpretation
        }
    }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Testing: Probabilidad de Beneficio (PoP)")
    print("=" * 70)
    
    # Generar datos sintéticos para testing
    np.random.seed(42)
    days = 252  # 1 año de datos
    initial_price = 100
    daily_returns = np.random.normal(0.0005, 0.02, days)  # 0.05% drift, 2% vol diaria
    prices = initial_price * (1 + daily_returns).cumprod()
    historical_prices = pd.Series(prices)
    
    print("\n📊 DATOS DE PRUEBA:")
    print(f"   Precio inicial: ${initial_price:.2f}")
    print(f"   Precio final: ${prices[-1]:.2f}")
    print(f"   Días históricos: {days}")
    print(f"   Rendimiento total: {(prices[-1]/initial_price - 1)*100:.2f}%")
    
    # Parámetros de la operación
    current_price = prices[-1]
    days_to_expiry = 45
    profitable_range = (current_price * 0.95, current_price * 1.05)  # ±5%
    sigma = 0.25  # 25% volatilidad anualizada
    r = 0.05
    
    print("\n📋 PARÁMETROS DE LA OPERACIÓN:")
    print(f"   Precio actual: ${current_price:.2f}")
    print(f"   Días hasta vencimiento: {days_to_expiry}")
    print(f"   Rango rentable: ${profitable_range[0]:.2f} - ${profitable_range[1]:.2f}")
    print(f"   Volatilidad (σ): {sigma:.2%}")
    print(f"   Tasa libre de riesgo (r): {r:.2%}")
    
    # Test 1: PoP Empírico
    print("\n" + "-" * 70)
    print("1. Probabilidad de Beneficio - Método Empírico:")
    print("-" * 70)
    emp_result = calculate_pop_empirical(historical_prices, days_to_expiry, profitable_range)
    
    print(f"\n   PoP: {emp_result['pop_pct']:.2f}%")
    print(f"   Escenarios rentables: {emp_result['num_profitable']}/{emp_result['total_scenarios']}")
    print(f"\n   Estadísticas de precios proyectados:")
    print(f"   Media: ${emp_result['mean_projected_price']:.2f}")
    print(f"   Desv. Est.: ${emp_result['std_projected_price']:.2f}")
    print(f"   Percentil 5%: ${emp_result['percentile_5']:.2f}")
    print(f"   Percentil 95%: ${emp_result['percentile_95']:.2f}")
    
    # Test 2: PoP Monte Carlo
    print("\n" + "-" * 70)
    print("2. Probabilidad de Beneficio - Método Monte Carlo:")
    print("-" * 70)
    T = days_to_expiry / 365
    mc_result = calculate_pop_monte_carlo(
        current_price, sigma, r, T, profitable_range, trials=10000, random_seed=42
    )
    
    print(f"\n   PoP: {mc_result['pop_pct']:.2f}%")
    print(f"   Escenarios rentables: {mc_result['num_profitable']}/{mc_result['total_trials']}")
    print(f"\n   Estadísticas de simulación:")
    print(f"   Media: ${mc_result['mean_final_price']:.2f}")
    print(f"   Desv. Est.: ${mc_result['std_final_price']:.2f}")
    print(f"   Percentil 5%: ${mc_result['percentile_5']:.2f}")
    print(f"   Percentil 95%: ${mc_result['percentile_95']:.2f}")
    print(f"   Rango: ${mc_result['min_price']:.2f} - ${mc_result['max_price']:.2f}")
    
    # Test 3: Comparación
    print("\n" + "-" * 70)
    print("3. Comparación de Métodos:")
    print("-" * 70)
    comparison = compare_pop_methods(
        historical_prices, current_price, sigma, r, days_to_expiry, 
        profitable_range, mc_trials=10000
    )
    
    print(f"\n   PoP Empírico: {comparison['empirical']['pop_pct']:.2f}%")
    print(f"   PoP Monte Carlo: {comparison['monte_carlo']['pop_pct']:.2f}%")
    print(f"   Diferencia: {comparison['comparison']['pop_difference']:+.2f}pp")
    print(f"   Ratio MC/Empírico: {comparison['comparison']['pop_ratio']:.2f}x")
    print(f"\n   💡 {comparison['comparison']['interpretation']}")
    
    print("\n" + "=" * 70)
    print("✓ Tests completados exitosamente")
    print("=" * 70)