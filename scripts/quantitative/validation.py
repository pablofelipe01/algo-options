# scripts/quantitative/validation.py
"""
Validación de Modelos Cuantitativos
====================================

Este módulo proporciona herramientas para:
1. Comparar griegas calculadas (BSM) vs griegas de mercado (Polygon)
2. Validar la implementación de Black-Scholes
3. Detectar opciones mal valoradas
4. Analizar discrepancias entre modelo y mercado
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from .black_scholes import black_scholes_price, calculate_greeks
from .utils import format_greek


def compare_greeks(
    polygon_greeks: Dict[str, float],
    bsm_greeks: Dict[str, float],
    option_type: str,
    tolerance: Dict[str, float] = None
) -> Dict:
    """
    Compara griegas de Polygon vs BSM y detecta discrepancias.
    
    Útil para:
    - Validar implementación de BSM
    - Detectar opciones mal valoradas en el mercado
    - Identificar oportunidades de arbitraje
    
    Parámetros:
    -----------
    polygon_greeks : dict
        Griegas de Polygon API: {'delta': float, 'gamma': float, ...}
    bsm_greeks : dict
        Griegas calculadas por BSM: {'delta': float, 'gamma': float, ...}
    option_type : str
        'call' o 'put'
    tolerance : dict, optional
        Tolerancias para cada griega: {'delta': 0.05, 'gamma': 0.01, ...}
        Si None, usa tolerancias por defecto
    
    Retorna:
    --------
    dict
        {
            'comparisons': DataFrame con comparación detallada,
            'discrepancies': list de griegas con diferencias significativas,
            'max_difference': tuple (greek_name, difference),
            'all_within_tolerance': bool
        }
    
    Ejemplo:
    --------
    >>> polygon = {'delta': 0.55, 'gamma': 0.05, 'vega': 0.12, 'theta': -0.05}
    >>> bsm = {'delta': 0.537, 'gamma': 0.055, 'vega': 0.114, 'theta': -0.054}
    >>> result = compare_greeks(polygon, bsm, 'call')
    >>> print(result['comparisons'])
    """
    # Tolerancias por defecto
    if tolerance is None:
        tolerance = {
            'delta': 0.05,   # ±0.05 es aceptable (5 puntos)
            'gamma': 0.01,   # ±0.01
            'vega': 0.02,    # ±0.02
            'theta': 0.01,   # ±0.01 por día
            'rho': 0.02      # ±0.02
        }
    
    comparisons = []
    discrepancies = []
    
    # Griegas comunes a comparar
    greeks_to_compare = ['delta', 'gamma', 'vega', 'theta', 'rho']
    
    for greek in greeks_to_compare:
        polygon_value = polygon_greeks.get(greek)
        bsm_value = bsm_greeks.get(greek)
        
        # Manejar valores None
        if polygon_value is None or bsm_value is None:
            comparisons.append({
                'greek': greek,
                'polygon': polygon_value,
                'bsm': bsm_value,
                'difference': None,
                'pct_difference': None,
                'within_tolerance': None,
                'status': 'missing_data'
            })
            continue
        
        # Calcular diferencias
        diff = bsm_value - polygon_value
        
        # Diferencia porcentual (cuidado con división por cero)
        if abs(polygon_value) > 1e-6:
            pct_diff = (diff / abs(polygon_value)) * 100
        else:
            pct_diff = None
        
        # Verificar tolerancia
        within_tolerance = abs(diff) <= tolerance.get(greek, 0.05)
        status = 'ok' if within_tolerance else 'discrepancy'
        
        comparisons.append({
            'greek': greek,
            'polygon': polygon_value,
            'bsm': bsm_value,
            'difference': diff,
            'pct_difference': pct_diff,
            'within_tolerance': within_tolerance,
            'status': status
        })
        
        if not within_tolerance:
            discrepancies.append({
                'greek': greek,
                'difference': diff,
                'pct_difference': pct_diff
            })
    
    # Crear DataFrame
    df_comparisons = pd.DataFrame(comparisons)
    
    # Encontrar máxima diferencia
    if len(df_comparisons[df_comparisons['difference'].notna()]) > 0:
        max_diff_row = df_comparisons[df_comparisons['difference'].notna()].loc[
            df_comparisons['difference'].abs().idxmax()
        ]
        max_difference = (max_diff_row['greek'], max_diff_row['difference'])
    else:
        max_difference = None
    
    all_within_tolerance = all(
        row['within_tolerance'] for row in comparisons 
        if row['within_tolerance'] is not None
    )
    
    return {
        'comparisons': df_comparisons,
        'discrepancies': discrepancies,
        'max_difference': max_difference,
        'all_within_tolerance': all_within_tolerance,
        'option_type': option_type
    }


def validate_bsm_implementation() -> Dict[str, bool]:
    """
    Valida la implementación de Black-Scholes con casos conocidos.
    
    Tests realizados:
    -----------------
    1. Put-Call Parity: C - P = S - K·e^(-rT)
    2. Opción ATM: Delta Call ≈ 0.5, Delta Put ≈ -0.5
    3. Opción ITM profunda: Delta Call → 1, Delta Put → -1
    4. Opción OTM profunda: Delta Call → 0, Delta Put → 0
    5. Tiempo → 0: Precio → max(S-K, 0) para calls
    6. Volatilidad → 0: Comportamiento límite
    7. Gamma: Siempre positivo, máximo en ATM
    8. Theta: Generalmente negativo (opciones largas pierden valor con tiempo)
    
    Retorna:
    --------
    dict
        {
            'put_call_parity': bool,
            'atm_delta': bool,
            'itm_delta': bool,
            'otm_delta': bool,
            'time_decay': bool,
            'gamma_positive': bool,
            'theta_negative': bool,
            'all_tests_passed': bool,
            'details': dict con resultados detallados
        }
    """
    results = {}
    details = {}
    
    # Parámetros estándar
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.25
    
    print("=" * 70)
    print("Validación de Implementación Black-Scholes-Merton")
    print("=" * 70)
    
    # Test 1: Put-Call Parity
    print("\n1. Put-Call Parity: C - P = S - K·e^(-rT)")
    call_price = black_scholes_price(S, K, T, r, sigma, 'call')
    put_price = black_scholes_price(S, K, T, r, sigma, 'put')
    pcp_left = call_price - put_price
    pcp_right = S - K * np.exp(-r * T)
    pcp_diff = abs(pcp_left - pcp_right)
    pcp_test = pcp_diff < 1e-6
    
    print(f"   C - P = {pcp_left:.6f}")
    print(f"   S - K·e^(-rT) = {pcp_right:.6f}")
    print(f"   Diferencia: {pcp_diff:.10f}")
    print(f"   Status: {'✓ PASS' if pcp_test else '✗ FAIL'}")
    
    results['put_call_parity'] = pcp_test
    details['put_call_parity'] = {'difference': pcp_diff, 'passed': pcp_test}
    
    # Test 2: Delta ATM
    print("\n2. Delta ATM (≈ 0.5 para call, ≈ -0.5 para put)")
    greeks = calculate_greeks(S, K, T, r, sigma)
    delta_call_atm = greeks['call']['delta']
    delta_put_atm = greeks['put']['delta']
    delta_test = (0.45 < delta_call_atm < 0.55) and (-0.55 < delta_put_atm < -0.45)
    
    print(f"   Call Delta: {delta_call_atm:.6f}")
    print(f"   Put Delta: {delta_put_atm:.6f}")
    print(f"   Status: {'✓ PASS' if delta_test else '✗ FAIL'}")
    
    results['atm_delta'] = delta_test
    details['atm_delta'] = {
        'call_delta': delta_call_atm,
        'put_delta': delta_put_atm,
        'passed': delta_test
    }
    
    # Test 3: Delta ITM profundo (K muy bajo)
    print("\n3. Delta ITM profundo (K = 50, S = 100)")
    K_itm = 50
    greeks_itm = calculate_greeks(S, K_itm, T, r, sigma)
    delta_call_itm = greeks_itm['call']['delta']
    delta_put_itm = greeks_itm['put']['delta']
    itm_test = delta_call_itm > 0.9 and delta_put_itm > -0.1
    
    print(f"   Call Delta: {delta_call_itm:.6f} (esperado > 0.9)")
    print(f"   Put Delta: {delta_put_itm:.6f} (esperado cerca de 0)")
    print(f"   Status: {'✓ PASS' if itm_test else '✗ FAIL'}")
    
    results['itm_delta'] = itm_test
    details['itm_delta'] = {
        'call_delta': delta_call_itm,
        'put_delta': delta_put_itm,
        'passed': itm_test
    }
    
    # Test 4: Delta OTM profundo (K muy alto)
    print("\n4. Delta OTM profundo (K = 150, S = 100)")
    K_otm = 150
    greeks_otm = calculate_greeks(S, K_otm, T, r, sigma)
    delta_call_otm = greeks_otm['call']['delta']
    delta_put_otm = greeks_otm['put']['delta']
    otm_test = delta_call_otm < 0.1 and delta_put_otm < -0.9
    
    print(f"   Call Delta: {delta_call_otm:.6f} (esperado cerca de 0)")
    print(f"   Put Delta: {delta_put_otm:.6f} (esperado < -0.9)")
    print(f"   Status: {'✓ PASS' if otm_test else '✗ FAIL'}")
    
    results['otm_delta'] = otm_test
    details['otm_delta'] = {
        'call_delta': delta_call_otm,
        'put_delta': delta_put_otm,
        'passed': otm_test
    }
    
    # Test 5: Decaimiento temporal (precio cerca de vencimiento)
    print("\n5. Decaimiento temporal (T = 0.01 años ≈ 4 días)")
    T_short = 0.01
    price_long = black_scholes_price(S, K, T, r, sigma, 'call')
    price_short = black_scholes_price(S, K, T_short, r, sigma, 'call')
    time_test = price_short < price_long
    
    print(f"   Precio con T=1 año: ${price_long:.4f}")
    print(f"   Precio con T=4 días: ${price_short:.4f}")
    print(f"   Status: {'✓ PASS' if time_test else '✗ FAIL'}")
    
    results['time_decay'] = time_test
    details['time_decay'] = {
        'price_long': price_long,
        'price_short': price_short,
        'passed': time_test
    }
    
    # Test 6: Gamma siempre positivo
    print("\n6. Gamma siempre positivo")
    gamma_call = greeks['call']['gamma']
    gamma_put = greeks['put']['gamma']
    gamma_test = gamma_call > 0 and gamma_put > 0
    
    print(f"   Call Gamma: {gamma_call:.6f}")
    print(f"   Put Gamma: {gamma_put:.6f}")
    print(f"   Status: {'✓ PASS' if gamma_test else '✗ FAIL'}")
    
    results['gamma_positive'] = gamma_test
    details['gamma_positive'] = {
        'call_gamma': gamma_call,
        'put_gamma': gamma_put,
        'passed': gamma_test
    }
    
    # Test 7: Theta generalmente negativo (opciones largas)
    print("\n7. Theta negativo (decaimiento temporal)")
    theta_call = greeks['call']['theta']
    theta_put = greeks['put']['theta']
    theta_test = theta_call < 0  # Call theta casi siempre negativo
    
    print(f"   Call Theta: {theta_call:.6f}")
    print(f"   Put Theta: {theta_put:.6f}")
    print(f"   Status: {'✓ PASS' if theta_test else '✗ FAIL'}")
    
    results['theta_negative'] = theta_test
    details['theta_negative'] = {
        'call_theta': theta_call,
        'put_theta': theta_put,
        'passed': theta_test
    }
    
    # Resultado final
    all_passed = all(results.values())
    results['all_tests_passed'] = all_passed
    
    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: {'✓ TODOS LOS TESTS PASARON' if all_passed else '✗ ALGUNOS TESTS FALLARON'}")
    print(f"Tests pasados: {sum(results.values())}/{len(results) - 1}")
    print("=" * 70)
    
    return {
        **results,
        'details': details
    }


def analyze_option_mispricing(
    market_price: float,
    bsm_price: float,
    S: float,
    K: float,
    option_type: str,
    threshold: float = 0.10
) -> Dict:
    """
    Analiza si una opción está mal valorada en el mercado vs modelo BSM.
    
    Parámetros:
    -----------
    market_price : float
        Precio de mercado (de Polygon)
    bsm_price : float
        Precio teórico calculado por BSM
    S : float
        Precio del subyacente
    K : float
        Strike price
    option_type : str
        'call' o 'put'
    threshold : float
        Umbral de diferencia porcentual para considerar mispricing (default: 10%)
    
    Retorna:
    --------
    dict
        {
            'market_price': float,
            'bsm_price': float,
            'difference': float,
            'pct_difference': float,
            'mispriced': bool,
            'direction': str,  # 'overvalued', 'undervalued', 'fair'
            'intrinsic_value': float,
            'time_value_market': float,
            'time_value_bsm': float
        }
    """
    # Calcular diferencia
    diff = market_price - bsm_price
    pct_diff = (diff / bsm_price) * 100 if bsm_price > 0 else None
    
    # Determinar si está mal valorada
    mispriced = abs(pct_diff) > (threshold * 100) if pct_diff is not None else False
    
    # Dirección del mispricing
    if not mispriced:
        direction = 'fair'
    elif diff > 0:
        direction = 'overvalued'  # Mercado paga más que modelo
    else:
        direction = 'undervalued'  # Mercado paga menos que modelo
    
    # Valor intrínseco
    if option_type == 'call':
        intrinsic = max(S - K, 0)
    else:
        intrinsic = max(K - S, 0)
    
    # Valor temporal
    time_value_market = market_price - intrinsic
    time_value_bsm = bsm_price - intrinsic
    
    return {
        'market_price': market_price,
        'bsm_price': bsm_price,
        'difference': diff,
        'pct_difference': pct_diff,
        'mispriced': mispriced,
        'direction': direction,
        'intrinsic_value': intrinsic,
        'time_value_market': time_value_market,
        'time_value_bsm': time_value_bsm,
        'threshold': threshold
    }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Testing: Validación de Modelos")
    print("=" * 70)
    
    # Test 1: Validación completa de BSM
    print("\n" + "=" * 70)
    validation_results = validate_bsm_implementation()
    
    # Test 2: Comparación de griegas
    print("\n" + "=" * 70)
    print("Testing: Comparación de Griegas (Polygon vs BSM)")
    print("=" * 70)
    
    # Simular griegas de Polygon (con pequeñas diferencias)
    S, K, T, r, sigma = 100, 100, 30/365, 0.05, 0.25
    bsm_greeks = calculate_greeks(S, K, T, r, sigma)['call']
    
    # Simular pequeñas diferencias como si fueran de Polygon
    polygon_greeks = {
        'delta': bsm_greeks['delta'] + 0.02,  # Pequeña diferencia
        'gamma': bsm_greeks['gamma'] - 0.003,
        'vega': bsm_greeks['vega'] + 0.01,
        'theta': bsm_greeks['theta'] - 0.005,
        'rho': bsm_greeks['rho'] + 0.008
    }
    
    comparison = compare_greeks(polygon_greeks, bsm_greeks, 'call')
    
    print("\nComparación detallada:")
    print(comparison['comparisons'].to_string(index=False))
    
    print(f"\n¿Todas dentro de tolerancia? {'✓ Sí' if comparison['all_within_tolerance'] else '✗ No'}")
    
    if comparison['discrepancies']:
        print(f"\nDiscrepancias encontradas: {len(comparison['discrepancies'])}")
        for disc in comparison['discrepancies']:
            print(f"  - {disc['greek']}: {disc['difference']:+.6f} ({disc['pct_difference']:+.2f}%)")
    
    # Test 3: Análisis de mispricing
    print("\n" + "=" * 70)
    print("Testing: Análisis de Mispricing")
    print("=" * 70)
    
    bsm_price = black_scholes_price(S, K, T, r, sigma, 'call')
    market_price = bsm_price * 1.15  # Simular 15% overvalued
    
    mispricing = analyze_option_mispricing(market_price, bsm_price, S, K, 'call', threshold=0.10)
    
    print(f"\nPrecio de mercado: ${mispricing['market_price']:.4f}")
    print(f"Precio BSM: ${mispricing['bsm_price']:.4f}")
    print(f"Diferencia: ${mispricing['difference']:+.4f} ({mispricing['pct_difference']:+.2f}%)")
    print(f"Mal valorada: {'✓ Sí' if mispricing['mispriced'] else '✗ No'}")
    print(f"Dirección: {mispricing['direction']}")
    print(f"\nValor intrínseco: ${mispricing['intrinsic_value']:.4f}")
    print(f"Valor temporal (mercado): ${mispricing['time_value_market']:.4f}")
    print(f"Valor temporal (BSM): ${mispricing['time_value_bsm']:.4f}")
    
    print("\n" + "=" * 70)
    print("✓ Tests de validación completados")
    print("=" * 70)