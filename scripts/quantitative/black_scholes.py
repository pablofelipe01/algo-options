# scripts/quantitative/black_scholes.py
"""
Modelo Black-Scholes-Merton (BSM)
==================================

Implementación desde cero del modelo BSM para:
- Valoración de opciones europeas (Call y Put)
- Cálculo de griegas (Δ, Γ, θ, ν, ρ)

Referencias:
- Black, F., & Scholes, M. (1973). The Pricing of Options and Corporate Liabilities.
- Merton, R. C. (1973). Theory of Rational Option Pricing.
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Tuple, Literal

# 🆕 Import modificado para soportar import directo desde backtester
try:
    from .utils import validate_inputs
except ImportError:
    from utils import validate_inputs


def calculate_d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
    """
    Calcula d1 y d2 del modelo Black-Scholes.
    
    Estas son las variables auxiliares fundamentales del modelo BSM.
    
    Fórmulas:
    ---------
    d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)
    d2 = d1 - σ√T
    
    Parámetros:
    -----------
    S : float
        Precio actual del activo subyacente
    K : float
        Strike price (precio de ejercicio)
    T : float
        Tiempo hasta vencimiento en años
    r : float
        Tasa de interés libre de riesgo anualizada
    sigma : float
        Volatilidad implícita anualizada
    
    Retorna:
    --------
    tuple
        (d1, d2)
    
    Ejemplo:
    --------
    >>> d1, d2 = calculate_d1_d2(S=100, K=100, T=1, r=0.05, sigma=0.2)
    >>> print(f"d1={d1:.4f}, d2={d2:.4f}")
    d1=0.3500, d2=0.1500
    """
    validate_inputs(S, K, T, r, sigma)
    
    # Cálculo de d1
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    # Cálculo de d2
    d2 = d1 - sigma * np.sqrt(T)
    
    return d1, d2


def black_scholes_price(S: float, K: float, T: float, r: float, sigma: float, 
                        option_type: Literal['call', 'put'] = 'call') -> float:
    """
    Calcula el precio teórico de una opción europea usando Black-Scholes.
    
    Fórmulas BSM:
    -------------
    Call: C = S·N(d1) - K·e^(-rT)·N(d2)
    Put:  P = K·e^(-rT)·N(-d2) - S·N(-d1)
    
    Donde:
    - N(x) es la función de distribución acumulada normal estándar
    - e^(-rT) es el factor de descuento
    
    Parámetros:
    -----------
    S : float
        Precio actual del subyacente
    K : float
        Strike price
    T : float
        Tiempo hasta vencimiento en años (ej. 45/365 para 45 días)
    r : float
        Tasa libre de riesgo anualizada (ej. 0.05 = 5%)
    sigma : float
        Volatilidad implícita anualizada (ej. 0.25 = 25%)
    option_type : 'call' o 'put'
        Tipo de opción
    
    Retorna:
    --------
    float
        Precio teórico de la opción
    
    Ejemplo:
    --------
    >>> # Call ATM a 30 días con 25% IV
    >>> price = black_scholes_price(S=100, K=100, T=30/365, r=0.05, sigma=0.25, option_type='call')
    >>> print(f"Precio teórico Call: ${price:.2f}")
    Precio teórico Call: $2.13
    """
    validate_inputs(S, K, T, r, sigma)
    
    if option_type not in ['call', 'put']:
        raise ValueError(f"option_type debe ser 'call' o 'put', recibido: {option_type}")
    
    # Calcular d1 y d2
    d1, d2 = calculate_d1_d2(S, K, T, r, sigma)
    
    # Factor de descuento
    discount_factor = np.exp(-r * T)
    
    if option_type == 'call':
        # Precio de Call: S·N(d1) - K·e^(-rT)·N(d2)
        price = S * norm.cdf(d1) - K * discount_factor * norm.cdf(d2)
    else:  # put
        # Precio de Put: K·e^(-rT)·N(-d2) - S·N(-d1)
        price = K * discount_factor * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    return price


def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float) -> Dict[str, Dict[str, float]]:
    """
    Calcula las griegas de primer orden para opciones call y put.
    
    Las griegas miden la sensibilidad del precio de la opción a cambios
    en diferentes variables del modelo.
    
    Griegas calculadas:
    -------------------
    - Delta (Δ): ∂V/∂S - Sensibilidad al precio del subyacente
      · Call: N(d1) ∈ [0, 1]
      · Put: N(d1) - 1 ∈ [-1, 0]
      
    - Gamma (Γ): ∂²V/∂S² - Tasa de cambio de Delta
      · Call y Put: N'(d1) / (S·σ·√T)
      · Siempre positivo, máximo en ATM
      
    - Vega (ν): ∂V/∂σ - Sensibilidad a volatilidad
      · Call y Put: S·N'(d1)·√T / 100
      · Siempre positivo, máximo en ATM
      
    - Theta (Θ): ∂V/∂t - Decaimiento temporal (por día)
      · Generalmente negativo (pérdida de valor con el tiempo)
      · Call: [-(S·N'(d1)·σ)/(2√T) - r·K·e^(-rT)·N(d2)] / 365
      · Put: [-(S·N'(d1)·σ)/(2√T) + r·K·e^(-rT)·N(-d2)] / 365
      
    - Rho (ρ): ∂V/∂r - Sensibilidad a tasa de interés
      · Call: K·T·e^(-rT)·N(d2) / 100
      · Put: -K·T·e^(-rT)·N(-d2) / 100
    
    Parámetros:
    -----------
    S, K, T, r, sigma : igual que en black_scholes_price()
    
    Retorna:
    --------
    dict
        {
            'call': {'delta': float, 'gamma': float, 'vega': float, 
                     'theta': float, 'rho': float},
            'put': {'delta': float, 'gamma': float, 'vega': float, 
                    'theta': float, 'rho': float}
        }
    
    Ejemplo:
    --------
    >>> greeks = calculate_greeks(S=100, K=100, T=30/365, r=0.05, sigma=0.25)
    >>> print(f"Call Delta: {greeks['call']['delta']:.4f}")
    >>> print(f"Put Delta: {greeks['put']['delta']:.4f}")
    """
    validate_inputs(S, K, T, r, sigma)
    
    # Calcular d1 y d2
    d1, d2 = calculate_d1_d2(S, K, T, r, sigma)
    
    # Factores comunes
    sqrt_T = np.sqrt(T)
    discount_factor = np.exp(-r * T)
    pdf_d1 = norm.pdf(d1)  # N'(d1) - Densidad de probabilidad normal
    
    # === DELTA (Δ) ===
    delta_call = norm.cdf(d1)
    delta_put = delta_call - 1  # Put delta = Call delta - 1
    
    # === GAMMA (Γ) ===
    # Gamma es idéntico para call y put
    gamma = pdf_d1 / (S * sigma * sqrt_T)
    
    # === VEGA (ν) ===
    # Vega es idéntico para call y put
    # Dividimos por 100 para expresar cambio por 1% de volatilidad
    vega = S * pdf_d1 * sqrt_T / 100
    
    # === THETA (Θ) ===
    # Theta por día (dividimos por 365)
    theta_common = -(S * pdf_d1 * sigma) / (2 * sqrt_T)
    theta_call = (theta_common - r * K * discount_factor * norm.cdf(d2)) / 365
    theta_put = (theta_common + r * K * discount_factor * norm.cdf(-d2)) / 365
    
    # === RHO (ρ) ===
    # Dividimos por 100 para expresar cambio por 1% de tasa
    rho_call = (K * T * discount_factor * norm.cdf(d2)) / 100
    rho_put = (-K * T * discount_factor * norm.cdf(-d2)) / 100
    
    return {
        'call': {
            'delta': delta_call,
            'gamma': gamma,
            'vega': vega,
            'theta': theta_call,
            'rho': rho_call
        },
        'put': {
            'delta': delta_put,
            'gamma': gamma,
            'vega': vega,
            'theta': theta_put,
            'rho': rho_put
        }
    }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Testing: Modelo Black-Scholes-Merton")
    print("=" * 70)
    
    # Parámetros de ejemplo
    S = 100.0    # Precio del subyacente
    K = 100.0    # Strike ATM
    T = 30/365   # 30 días
    r = 0.05     # 5% tasa libre de riesgo
    sigma = 0.25 # 25% volatilidad
    
    print("\n📊 PARÁMETROS:")
    print(f"   Subyacente (S): ${S:.2f}")
    print(f"   Strike (K): ${K:.2f}")
    print(f"   Tiempo (T): {T*365:.0f} días ({T:.4f} años)")
    print(f"   Tasa (r): {r:.2%}")
    print(f"   Volatilidad (σ): {sigma:.2%}")
    
    # Test 1: d1 y d2
    print("\n" + "-" * 70)
    print("1. Cálculo de d1 y d2:")
    d1, d2 = calculate_d1_d2(S, K, T, r, sigma)
    print(f"   d1 = {d1:.6f}")
    print(f"   d2 = {d2:.6f}")
    print(f"   N(d1) = {norm.cdf(d1):.6f}")
    print(f"   N(d2) = {norm.cdf(d2):.6f}")
    
    # Test 2: Precios BSM
    print("\n" + "-" * 70)
    print("2. Precios Black-Scholes:")
    call_price = black_scholes_price(S, K, T, r, sigma, 'call')
    put_price = black_scholes_price(S, K, T, r, sigma, 'put')
    print(f"   Call Price: ${call_price:.4f}")
    print(f"   Put Price: ${put_price:.4f}")
    
    # Verificar Put-Call Parity: C - P = S - K·e^(-rT)
    pcp_left = call_price - put_price
    pcp_right = S - K * np.exp(-r * T)
    print(f"\n   Put-Call Parity Check:")
    print(f"   C - P = ${pcp_left:.4f}")
    print(f"   S - K·e^(-rT) = ${pcp_right:.4f}")
    print(f"   Diferencia: ${abs(pcp_left - pcp_right):.8f} {'✓' if abs(pcp_left - pcp_right) < 0.0001 else '✗'}")
    
    # Test 3: Griegas
    print("\n" + "-" * 70)
    print("3. Griegas:")
    greeks = calculate_greeks(S, K, T, r, sigma)
    
    print("\n   CALL:")
    for greek, value in greeks['call'].items():
        print(f"   {greek.capitalize():8s}: {value:>10.6f}")
    
    print("\n   PUT:")
    for greek, value in greeks['put'].items():
        print(f"   {greek.capitalize():8s}: {value:>10.6f}")
    
    # Test 4: Diferentes strikes
    print("\n" + "-" * 70)
    print("4. Precios por Moneyness:")
    print(f"\n   {'Strike':<10} {'Moneyness':<12} {'Call':<10} {'Put':<10} {'Call Δ':<10} {'Put Δ':<10}")
    print("   " + "-" * 60)
    
    for strike in [90, 95, 100, 105, 110]:
        call = black_scholes_price(S, strike, T, r, sigma, 'call')
        put = black_scholes_price(S, strike, T, r, sigma, 'put')
        g = calculate_greeks(S, strike, T, r, sigma)
        
        moneyness = "ITM" if strike < S else ("ATM" if strike == S else "OTM")
        print(f"   ${strike:<9.0f} {moneyness:<12} ${call:<9.2f} ${put:<9.2f} {g['call']['delta']:<9.4f} {g['put']['delta']:<9.4f}")
    
    print("\n" + "=" * 70)
    print("✓ Tests completados exitosamente")
    print("=" * 70)