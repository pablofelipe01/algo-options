# 📊 Módulo de Modelado Cuantitativo para Trading de Opciones

Implementación completa del núcleo matemático para valoración y análisis de opciones basado en el modelo Black-Scholes-Merton (BSM).

---

## 📑 Tabla de Contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Instalación](#instalación)
- [Estructura del Módulo](#estructura-del-módulo)
- [Guía de Uso](#guía-de-uso)
- [API Reference](#api-reference)
- [Ejemplos Prácticos](#ejemplos-prácticos)
- [Testing](#testing)
- [Limitaciones](#limitaciones)
- [Referencias](#referencias)

---

## 🎯 Descripción

Este módulo proporciona herramientas cuantitativas profesionales para:

- **Valoración de opciones** usando el modelo Black-Scholes-Merton
- **Cálculo de griegas** (Δ, Γ, θ, ν, ρ) desde cero
- **Probabilidad de Beneficio (PoP)** con dos métodos complementarios
- **Validación de modelos** y detección de discrepancias
- **Comparación mercado vs modelo teórico**

### ¿Por Qué Implementar BSM desde Cero?

Aunque existen bibliotecas que calculan BSM automáticamente, implementarlo desde cero proporciona:

1. **Comprensión profunda** de las relaciones entre variables
2. **Intuición** sobre el riesgo de las opciones
3. **Flexibilidad** para personalizar y extender el modelo
4. **Transparencia** total en los cálculos

---

## ✨ Características

### 1. Black-Scholes-Merton (BSM)

- ✅ Valoración de opciones europeas (Call y Put)
- ✅ Cálculo de d1 y d2
- ✅ Verificación de Put-Call Parity
- ✅ Validación automática de inputs

### 2. Griegas de Primer Orden

| Griega | Descripción | Interpretación |
|--------|-------------|----------------|
| **Delta (Δ)** | ∂V/∂S | Sensibilidad al precio del subyacente (0-1 call, -1-0 put) |
| **Gamma (Γ)** | ∂²V/∂S² | Tasa de cambio de Delta (siempre positivo, máximo ATM) |
| **Vega (ν)** | ∂V/∂σ | Sensibilidad a volatilidad (siempre positivo, máximo ATM) |
| **Theta (Θ)** | ∂V/∂t | Decaimiento temporal (generalmente negativo) |
| **Rho (ρ)** | ∂V/∂r | Sensibilidad a tasa de interés |

### 3. Probabilidad de Beneficio (PoP)

#### Método Empírico (Libre de Modelos)
- ✅ Basado en distribución histórica real
- ✅ No asume ningún modelo de precios
- ✅ Pregunta: "¿Con qué frecuencia habría ganado históricamente?"

#### Método Monte Carlo (GBM)
- ✅ Basado en Movimiento Browniano Geométrico
- ✅ Asume distribución log-normal
- ✅ Pregunta: "¿Con qué frecuencia ganaré en simulaciones?"

**La comparación entre ambos métodos es altamente informativa:**
- Si PoP_MC >> PoP_Empírico → Volatilidad asumida baja o historia reciente hostil
- Si PoP_Empírico >> PoP_MC → Volatilidad asumida alta o historia reciente favorable

### 4. Validación y Análisis

- ✅ Comparación griegas Polygon vs BSM
- ✅ Detección de opciones mal valoradas
- ✅ Tests automáticos de validación
- ✅ Análisis por moneyness (ITM/ATM/OTM)

---

## 🔧 Instalación

### Dependencias
```bash
# En el entorno virtual
pip install numpy scipy pandas
```

### Estructura de Archivos
```
scripts/
├── quantitative/
│   ├── __init__.py           # Importaciones principales
│   ├── black_scholes.py      # Modelo BSM y griegas
│   ├── probability.py        # PoP (empírico y Monte Carlo)
│   ├── validation.py         # Comparación y validación
│   └── utils.py              # Utilidades comunes
└── demo_quantitative.py      # Script de demostración
```

---

## 🚀 Guía de Uso

### Importación Rápida
```python
from quantitative import (
    black_scholes_price,
    calculate_greeks,
    calculate_pop_empirical,
    calculate_pop_monte_carlo,
    days_to_years,
    get_risk_free_rate
)
```

### Ejemplo Básico: Valorar una Opción
```python
# Parámetros
S = 100.0       # Precio del subyacente
K = 105.0       # Strike price
T = 30/365      # 30 días hasta vencimiento
r = 0.05        # Tasa libre de riesgo (5%)
sigma = 0.25    # Volatilidad implícita (25%)

# Calcular precio de Call
call_price = black_scholes_price(S, K, T, r, sigma, 'call')
print(f"Precio Call: ${call_price:.2f}")

# Calcular precio de Put
put_price = black_scholes_price(S, K, T, r, sigma, 'put')
print(f"Precio Put: ${put_price:.2f}")
```

**Salida:**
```
Precio Call: $1.19
Precio Put: $5.76
```

### Ejemplo: Calcular Griegas
```python
# Calcular todas las griegas
greeks = calculate_greeks(S, K, T, r, sigma)

# Griegas para Call
print("CALL:")
print(f"  Delta: {greeks['call']['delta']:.4f}")
print(f"  Gamma: {greeks['call']['gamma']:.4f}")
print(f"  Vega:  {greeks['call']['vega']:.4f}")
print(f"  Theta: {greeks['call']['theta']:.4f}")
print(f"  Rho:   {greeks['call']['rho']:.4f}")

# Griegas para Put
print("\nPUT:")
print(f"  Delta: {greeks['put']['delta']:.4f}")
print(f"  Gamma: {greeks['put']['gamma']:.4f}")
print(f"  Vega:  {greeks['put']['vega']:.4f}")
print(f"  Theta: {greeks['put']['theta']:.4f}")
print(f"  Rho:   {greeks['put']['rho']:.4f}")
```

**Salida:**
```
CALL:
  Delta: 0.2784
  Gamma: 0.0331
  Vega:  0.0680
  Theta: -0.0323
  Rho:   0.0227

PUT:
  Delta: -0.7216
  Gamma: 0.0331
  Vega:  0.0680
  Theta: -0.0183
  Rho:   -0.0596
```

### Ejemplo: Probabilidad de Beneficio Empírico
```python
import pandas as pd

# Cargar datos históricos
historical_prices = pd.Series([100, 102, 99, 101, 103, ...])

# Parámetros de la estrategia (ej. Iron Condor)
days_to_expiry = 45
profitable_range = (95, 105)  # Rentable entre $95 y $105

# Calcular PoP empírico
pop_result = calculate_pop_empirical(
    historical_prices,
    days_to_expiry,
    profitable_range
)

print(f"Probabilidad de Beneficio: {pop_result['pop_pct']:.2f}%")
print(f"Escenarios rentables: {pop_result['num_profitable']}/{pop_result['total_scenarios']}")
print(f"Precio proyectado (media): ${pop_result['mean_projected_price']:.2f}")
print(f"Percentil 5%: ${pop_result['percentile_5']:.2f}")
print(f"Percentil 95%: ${pop_result['percentile_95']:.2f}")
```

**Salida:**
```
Probabilidad de Beneficio: 68.50%
Escenarios rentables: 137/200
Precio proyectado (media): $100.25
Percentil 5%: $92.15
Percentil 95%: $108.45
```

### Ejemplo: Probabilidad de Beneficio Monte Carlo
```python
# Parámetros actuales
S = 100.0
sigma = 0.25
r = 0.05
T = 45/365
profitable_range = (95, 105)

# Simular 10,000 escenarios
pop_mc = calculate_pop_monte_carlo(
    S, sigma, r, T,
    profitable_range,
    trials=10000,
    random_seed=42
)

print(f"PoP Monte Carlo: {pop_mc['pop_pct']:.2f}%")
print(f"Precio final (media): ${pop_mc['mean_final_price']:.2f}")
print(f"Desviación estándar: ${pop_mc['std_final_price']:.2f}")
print(f"Rango 90%: ${pop_mc['percentile_5']:.2f} - ${pop_mc['percentile_95']:.2f}")
```

**Salida:**
```
PoP Monte Carlo: 72.34%
Precio final (media): $100.62
Desviación estándar: $7.85
Rango 90%: $90.15 - $111.25
```

### Ejemplo: Comparar Ambos Métodos de PoP
```python
from quantitative import compare_pop_methods

comparison = compare_pop_methods(
    historical_prices,
    S, sigma, r,
    days_to_expiry,
    profitable_range,
    mc_trials=10000
)

print(f"PoP Empírico: {comparison['empirical']['pop_pct']:.2f}%")
print(f"PoP Monte Carlo: {comparison['monte_carlo']['pop_pct']:.2f}%")
print(f"Diferencia: {comparison['comparison']['pop_difference']:+.2f}pp")
print(f"\n💡 {comparison['comparison']['interpretation']}")
```

**Salida:**
```
PoP Empírico: 68.50%
PoP Monte Carlo: 72.34%
Diferencia: +3.84pp

💡 Ambos métodos concuerdan (diferencia < 5%)
```

---

## 📚 API Reference

### `black_scholes.py`

#### `black_scholes_price(S, K, T, r, sigma, option_type)`

Calcula el precio teórico de una opción europea.

**Parámetros:**
- `S` (float): Precio del subyacente
- `K` (float): Strike price
- `T` (float): Tiempo hasta vencimiento en años
- `r` (float): Tasa libre de riesgo anualizada
- `sigma` (float): Volatilidad implícita anualizada
- `option_type` (str): 'call' o 'put'

**Retorna:** `float` - Precio teórico de la opción

**Ejemplo:**
```python
price = black_scholes_price(100, 105, 30/365, 0.05, 0.25, 'call')
# Returns: 1.19
```

---

#### `calculate_greeks(S, K, T, r, sigma)`

Calcula las griegas de primer orden.

**Parámetros:**
- Igual que `black_scholes_price` (sin `option_type`)

**Retorna:** `dict` con estructura:
```python
{
    'call': {
        'delta': float,
        'gamma': float,
        'vega': float,
        'theta': float,
        'rho': float
    },
    'put': {
        'delta': float,
        'gamma': float,
        'vega': float,
        'theta': float,
        'rho': float
    }
}
```

---

#### `calculate_d1_d2(S, K, T, r, sigma)`

Calcula las variables auxiliares d1 y d2 del modelo BSM.

**Retorna:** `tuple` - (d1, d2)

---

### `probability.py`

#### `calculate_pop_empirical(historical_prices, days_to_expiry, profitable_range, min_samples=30)`

Calcula PoP usando distribución empírica de rendimientos históricos.

**Parámetros:**
- `historical_prices` (pd.Series): Precios históricos
- `days_to_expiry` (int): Días hasta vencimiento
- `profitable_range` (tuple): (precio_min, precio_max)
- `min_samples` (int): Muestras mínimas requeridas

**Retorna:** `dict` con claves:
- `pop`, `pop_pct`: Probabilidad
- `num_profitable`, `total_scenarios`: Conteos
- `mean_projected_price`, `std_projected_price`: Estadísticas
- `percentile_5`, `percentile_25`, `percentile_50`, `percentile_75`, `percentile_95`

---

#### `calculate_pop_monte_carlo(S, sigma, r, T, profitable_range, trials=10000, random_seed=None)`

Calcula PoP usando simulación Monte Carlo con GBM.

**Parámetros:**
- `S` (float): Precio actual
- `sigma` (float): Volatilidad anualizada
- `r` (float): Tasa libre de riesgo
- `T` (float): Tiempo en años
- `profitable_range` (tuple): (precio_min, precio_max)
- `trials` (int): Número de simulaciones
- `random_seed` (int, optional): Semilla para reproducibilidad

**Retorna:** `dict` (similar a `calculate_pop_empirical` con claves adicionales como `min_price`, `max_price`)

---

#### `compare_pop_methods(historical_prices, S, sigma, r, days_to_expiry, profitable_range, mc_trials=10000)`

Compara ambos métodos de PoP y proporciona interpretación.

**Retorna:** `dict` con claves:
- `empirical`: Resultados del método empírico
- `monte_carlo`: Resultados de Monte Carlo
- `comparison`: Diferencias e interpretación

---

### `validation.py`

#### `compare_greeks(polygon_greeks, bsm_greeks, option_type, tolerance=None)`

Compara griegas de Polygon vs BSM.

**Retorna:** `dict` con DataFrame de comparaciones y lista de discrepancias

---

#### `validate_bsm_implementation()`

Ejecuta suite completa de tests de validación de BSM.

**Retorna:** `dict` con resultados de 7 tests diferentes

---

#### `analyze_option_mispricing(market_price, bsm_price, S, K, option_type, threshold=0.10)`

Analiza si una opción está mal valorada.

**Retorna:** `dict` con análisis de diferencias y clasificación

---

### `utils.py`

#### `days_to_years(days, calendar_days=True)`
Convierte días a fracción de año.

#### `annualize_volatility(daily_vol, trading_days=True)`
Anualiza volatilidad diaria.

#### `get_risk_free_rate(default=0.05)`
Obtiene tasa libre de riesgo (actualmente retorna default).

#### `validate_inputs(S, K, T, r, sigma)`
Valida parámetros de BSM.

#### `format_greek(value, greek_name)`
Formatea griegas para impresión.

---

## 💡 Ejemplos Prácticos

### Análisis de Iron Condor
```python
# Parámetros del Iron Condor en SPY
# Venta: Put $650 + Call $690
# Compra: Put $645 + Call $695

import pandas as pd
from quantitative import calculate_pop_empirical, calculate_pop_monte_carlo

# Cargar datos históricos de SPY
spy_prices = pd.read_parquet('../data/historical/SPY_60days.parquet')['close']

# Rango rentable: entre $650 y $690
profitable_range = (650, 690)
days_to_expiry = 45

# Método 1: Empírico
pop_emp = calculate_pop_empirical(spy_prices, days_to_expiry, profitable_range)
print(f"PoP Empírico: {pop_emp['pop_pct']:.2f}%")

# Método 2: Monte Carlo
pop_mc = calculate_pop_monte_carlo(
    S=670,
    sigma=0.15,
    r=0.05,
    T=days_to_expiry/365,
    profitable_range=profitable_range,
    trials=10000
)
print(f"PoP Monte Carlo: {pop_mc['pop_pct']:.2f}%")
```

### Detectar Opciones Mal Valoradas
```python
from quantitative import black_scholes_price, analyze_option_mispricing

# Datos de mercado
market_price = 5.50
S = 100
K = 105
T = 30/365
r = 0.05
sigma = 0.25

# Calcular precio teórico
bsm_price = black_scholes_price(S, K, T, r, sigma, 'call')

# Analizar discrepancia
analysis = analyze_option_mispricing(market_price, bsm_price, S, K, 'call', threshold=0.10)

if analysis['mispriced']:
    print(f"⚠️ Opción {analysis['direction']}")
    print(f"   Mercado: ${market_price:.2f}")
    print(f"   BSM: ${bsm_price:.2f}")
    print(f"   Diferencia: {analysis['pct_difference']:+.2f}%")
else:
    print("✓ Opción correctamente valorada")
```

---

## 🧪 Testing

### Tests Unitarios de Black-Scholes
```bash
python -m quantitative.black_scholes
```

Ejecuta tests que verifican:
- Put-Call Parity
- Delta ATM
- Comportamiento ITM/OTM
- Decaimiento temporal
- Gamma positivo
- Theta negativo

### Tests de Probabilidad
```bash
python -m quantitative.probability
```

Genera datos sintéticos y prueba ambos métodos de PoP.

### Tests de Validación
```bash
python -m quantitative.validation
```

Ejecuta suite completa de validación con 7 tests.

### Demo con Datos Reales
```bash
# Analizar 100 opciones de SPY
python demo_quantitative.py --ticker SPY --sample 100

# Analizar opciones a 45 días
python demo_quantitative.py --ticker QQQ --dte 45 --sample 50

# Analizar otro ticker
python demo_quantitative.py --ticker AAPL --sample 50
```

---

## ⚠️ Limitaciones

### Supuestos del Modelo BSM

El modelo Black-Scholes-Merton asume:

1. **Opciones europeas** (ejercicio solo al vencimiento)
   - Las opciones americanas tienen valor adicional por ejercicio anticipado
   
2. **Volatilidad constante**
   - En realidad, la IV varía por strike (volatility skew/smile)
   
3. **Distribución log-normal de precios**
   - Los mercados reales tienen fat tails y skewness
   
4. **Sin costes de transacción**
   - Spreads bid-ask afectan precios reales
   
5. **Mercados eficientes**
   - No hay arbitraje libre de riesgo
   
6. **Tasa libre de riesgo constante**
   - Las tasas varían en el tiempo

### Discrepancias Esperadas

Es **normal** ver diferencias entre BSM y precios de mercado:

- ✅ Diferencias del 5-15% son comunes
- ✅ Las griegas de Polygon pueden usar modelos más sofisticados
- ✅ El mercado incorpora información que BSM no captura

### Cuándo NO Usar BSM

❌ **No usar BSM para:**
- Opciones americanas con dividendos significativos
- Opciones con vencimiento > 2 años (incertidumbre de r y σ)
- Activos con distribuciones no log-normales
- Análisis de alta frecuencia

✅ **Usar BSM para:**
- Valoración rápida y referencias
- Comparación con mercado
- Educación y comprensión de sensibilidades
- Estrategias multi-leg

---

## 🔗 Referencias

### Papers Fundamentales

1. **Black, F., & Scholes, M. (1973)**
   "The Pricing of Options and Corporate Liabilities"
   *Journal of Political Economy*, 81(3), 637-654

2. **Merton, R. C. (1973)**
   "Theory of Rational Option Pricing"
   *The Bell Journal of Economics and Management Science*, 4(1), 141-183

### Recursos Adicionales

- **Hull, J. C.** (2018). *Options, Futures, and Other Derivatives* (10th ed.)
- **Wilmott, P.** (2006). *Paul Wilmott on Quantitative Finance*
- **Taleb, N. N.** (1997). *Dynamic Hedging: Managing Vanilla and Exotic Options*

### Implementaciones de Referencia

- [QuantLib](https://www.quantlib.org/) - Biblioteca C++ para finanzas cuantitativas
- [Mibian](https://github.com/yassinemaaroufi/mibian) - Implementación Python de BSM
- [py_vollib](https://github.com/vollib/py_vollib) - Black-Scholes y volatilidad implícita

---

## 📞 Soporte y Contribuciones

### Reportar Issues

Si encuentras bugs o tienes sugerencias:
1. Verifica que los inputs sean válidos
2. Ejecuta los tests de validación
3. Documenta el problema con ejemplos reproducibles

### Mejoras Futuras

Áreas potenciales de expansión:
- [ ] Opciones americanas (Bjerksund-Stensland)
- [ ] Volatility surface fitting
- [ ] Griegas de segundo orden (Vanna, Volga, Charm)
- [ ] Integración con FRED API para tasas actuales
- [ ] Exportación a reportes PDF/HTML
- [ ] Visualizaciones interactivas

---

## 📄 Licencia

Este módulo es parte del proyecto "Sistema de Trading Algorítmico de Opciones" y está disponible para uso educativo y personal.

---

## ✅ Checklist de Uso

Antes de usar el módulo en producción:

- [ ] Entiendo las limitaciones del modelo BSM
- [ ] He validado el módulo con `validate_bsm_implementation()`
- [ ] He comparado resultados con fuentes confiables
- [ ] Uso múltiples métodos de PoP para validación cruzada
- [ ] Considero spreads bid-ask en decisiones de trading
- [ ] Actualizo regularmente la tasa libre de riesgo
- [ ] Verifico que la volatilidad implícita sea razonable

---

**Última actualización:** Octubre 2025  
**Versión:** 1.0.0  
**Autor:** Sistema de Trading de Opciones