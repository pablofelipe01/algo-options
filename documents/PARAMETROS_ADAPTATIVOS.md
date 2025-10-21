# Parámetros Adaptativos por Ticker

## 📋 Resumen Ejecutivo

Implementación de **parámetros dinámicos** de profit targets, stop losses y rangos DTE basados en características específicas de cada ticker:

- **Volatilidad histórica** (IV Mean de 60 días)
- **Performance observada** en backtests
- **Tipo de activo** (ETF, Tech, Commodity)

---

## 🎯 Objetivos

1. **Maximizar profit targets** en tickers con alta tasa de cierres anticipados
2. **Ajustar stop losses** según volatilidad para evitar whipsaws
3. **Optimizar rangos DTE** por tipo de activo
4. **Mejorar la gestión de riesgo** con parámetros específicos por ticker

---

## 📊 Análisis de Volatilidad

### Clasificación por IV Mean (60 días)

| Categoría | Rango IV | Tickers | Profit Target | Stop Loss |
|-----------|----------|---------|---------------|-----------|
| **High** | ≥ 0.40 | TSLA, NVDA, SLV, AMZN, AAPL, MSFT, IWM, GLD | 20-25% | 200% |
| **Medium** | 0.25-0.40 | SPY, QQQ | 30-35% | 150% |
| **Low** | < 0.25 | _(ninguno en la muestra)_ | 50% | 100% |

### Métricas de IV por Ticker

```
Ticker  | IV Mean | IV Std  | Vol Category
--------|---------|---------|-------------
TSLA    | 0.952   | 0.182   | High
SLV     | 0.917   | 0.167   | High  
NVDA    | 0.905   | 0.171   | High
AMZN    | 0.618   | 0.118   | High
AAPL    | 0.537   | 0.102   | High
MSFT    | 0.478   | 0.091   | High
GLD     | 0.408   | 0.077   | High
IWM     | 0.404   | 0.076   | High
SPY     | 0.350   | 0.066   | Medium
QQQ     | 0.347   | 0.065   | Medium
```

---

## 🔧 Configuración Adaptativa

### Por Tipo de Activo

#### 1. **ETFs** (SPY, QQQ, IWM)
- **DTE Range:** 49-56 días
- **Reasoning:** Long DTE para estabilidad y theta decay gradual
- **Características:**
  - Movimientos más predecibles
  - Menor impacto de eventos individuales
  - Ideal para estrategias de rango

| Ticker | Vol Category | Profit Target | Stop Loss | DTE Range |
|--------|--------------|---------------|-----------|-----------|
| SPY    | Medium       | 30%           | 150%      | 49-56     |
| QQQ    | Medium       | 30%           | 150%      | 49-56     |
| IWM    | High         | 25%           | 200%      | 49-56     |

#### 2. **Tech Stocks** (AAPL, MSFT, AMZN, NVDA, TSLA)
- **DTE Range:** 42-49 días
- **Reasoning:** Medium-Long DTE para capturar ciclos de volatilidad
- **Características:**
  - Alta volatilidad intraday
  - Sensibles a earnings y noticias
  - Movimientos rápidos → profit targets más agresivos

| Ticker | Vol Category | Profit Target | Stop Loss | DTE Range | Special Notes |
|--------|--------------|---------------|-----------|-----------|---------------|
| TSLA   | High         | **20%**       | 200%      | 42-49     | 🚀 Ultra-agresivo (75% early closures) |
| NVDA   | High         | 25%           | 200%      | 42-49     | - |
| AMZN   | High         | 25%           | 200%      | 42-49     | - |
| AAPL   | High         | 25%           | 200%      | 42-49     | - |
| MSFT   | High         | 25%           | 200%      | 42-49     | - |

#### 3. **Commodities** (GLD, SLV)
- **DTE Range:** 56-60 días
- **Reasoning:** Extra Long DTE para aprovechar tendencias largas
- **Características:**
  - Volatilidad de medio plazo
  - Tendencias más sostenidas
  - Menor volatilidad intraday que tech

| Ticker | Vol Category | Profit Target | Stop Loss | DTE Range |
|--------|--------------|---------------|-----------|-----------|
| GLD    | High         | 25%           | 200%      | 56-60     |
| SLV    | High         | 25%           | 200%      | 56-60     |

---

## 📈 Evidencia Empírica

### Performance por Ticker (44 trades totales)

| Ticker | Trades | Win Rate | Total PnL | Early Closure Rate | Avg Days Held |
|--------|--------|----------|-----------|--------------------|--------------:|
| TSLA   | 8      | 100.0%   | $4,654    | **75.0%** 🏆       | 13.0          |
| QQQ    | 7      | 71.4%    | $1,680    | **71.4%**          | 16.9          |
| SPY    | 7      | 71.4%    | $1,291    | **71.4%**          | 16.9          |
| IWM    | 5      | 80.0%    | $741      | 60.0%              | 22.2          |
| NVDA   | 4      | 100.0%   | $614      | 50.0%              | 24.2          |
| AMZN   | 3      | 100.0%   | $495      | 33.3%              | 32.3          |
| GLD    | 2      | 100.0%   | $481      | **0.0%** 🐢        | 52.0          |
| SLV    | 4      | 100.0%   | $378      | 50.0%              | 26.0          |
| MSFT   | 2      | 100.0%   | $275      | **0.0%**           | 52.0          |
| AAPL   | 2      | 100.0%   | $306      | **0.0%**           | 48.5          |

### Hallazgos Clave

1. **TSLA**: 75% early closures → Profit target **20%** (más agresivo)
   - Justificación: Alta volatilidad + excelente histórico de cierres anticipados
   - 8 trades, 100% win rate, $4,654 PnL

2. **SPY/QQQ**: 71.4% early closures → Profit target **30%**
   - Justificación: Medium volatility + buenos resultados con cierres anticipados
   - Ajuste de 35% base a 30% por performance

3. **GLD/MSFT/AAPL**: 0% early closures → Mantener parámetros base
   - Justificación: Mayoría de trades llegaron a expiración
   - No hay evidencia para ser más agresivos

---

## 🚀 Impacto Esperado

### Comparación: Parámetros Fijos vs Adaptativos

| Métrica | Fijos (Old) | Adaptativos (New) | Cambio |
|---------|-------------|-------------------|--------|
| Profit Target (TSLA) | 25-50% | **20%** | ⬇️ Más agresivo |
| Profit Target (SPY/QQQ) | 25-50% | **30%** | ⬇️ Más agresivo |
| Stop Loss (High Vol) | 100-200% | **200%** | ⬆️ Más protección |
| Stop Loss (Medium Vol) | 100-200% | **150%** | → Balanceado |
| DTE Tech | 15-60 | **42-49** | 🎯 Optimizado |
| DTE ETF | 15-60 | **49-56** | 🎯 Optimizado |
| DTE Commodity | 15-60 | **56-60** | 🎯 Optimizado |

### Beneficios Esperados

1. **Mayor Early Closure Rate**
   - TSLA: Profit target 20% → cerrar más rápido → liberar capital
   - SPY/QQQ: Profit target 30% → capturar movimientos favorables

2. **Menor Whipsaw Rate**
   - High Vol: Stop loss 200% → evitar salidas prematuras en movimientos bruscos
   - Medium Vol: Stop loss 150% → balance entre protección y salidas tempranas

3. **Mejor Aprovechamiento de Theta**
   - Long DTE (42-60) → sweet spot identificado en análisis
   - Tech: 42-49 días para capturar ciclos
   - ETF: 49-56 días para estabilidad
   - Commodity: 56-60 días para tendencias

---

## 🔄 Implementación

### Módulo: `adaptive_config.py`

```python
from strategies.adaptive_config import get_adaptive_config_manager

# Obtener gestor
adaptive_config = get_adaptive_config_manager()

# Obtener configuración para un ticker
config = adaptive_config.get_config('TSLA')
print(config)
# TickerParameters(TSLA: PT=20.0%, SL=200.0%, DTE=42-49)

# Calcular profit target para una posición
premium = 500.0
profit_target = adaptive_config.get_profit_target('TSLA', premium)
# $100.00 (20% de $500)

# Calcular stop loss para una posición
max_risk = 2500.0
stop_loss = adaptive_config.get_stop_loss('TSLA', max_risk)
# $5000.00 (200% de $2500)

# Obtener rango DTE
dte_min, dte_max = adaptive_config.get_dte_range('TSLA')
# (42, 49)
```

### Integración en Backtester

El backtester automáticamente aplica parámetros adaptativos en:

1. **Construcción de posiciones**
   - `position.profit_target` = adaptativo por ticker
   - `position.stop_loss` = adaptativo por ticker

2. **Selección de oportunidades**
   - Filtering por DTE range adaptativo
   - Quality score ajustado por parámetros

3. **Gestión de posiciones**
   - Profit targets y stop losses específicos por ticker
   - Tracking de efectividad por configuración

---

## 📝 Recomendaciones de Uso

### 1. **Monitoreo Continuo**
- Revisar early closure rates cada 30 días
- Ajustar profit targets si tasa cae < 50%
- Validar stop losses no generan exceso de salidas

### 2. **Backtesting Periódico**
- Re-ejecutar backtest mensual con datos actualizados
- Comparar performance: fijos vs adaptativos
- Ajustar clasificaciones de volatilidad si IV cambia >20%

### 3. **Calibración por Régimen de Mercado**
- **Bull Market**: Considerar profit targets más altos (+5%)
- **Bear Market**: Considerar stop losses más amplios (+25%)
- **High VIX (>25)**: Reducir profit targets (-5%) para capturar volatilidad

### 4. **Validación de Tickers Nuevos**
- Usar configuración conservadora (Medium Vol, ETF params)
- Monitorear primeras 10 trades
- Reclasificar basado en performance

---

## 🎓 Referencias

### Análisis Origen
1. **analyze_ticker_parameters.py** - Análisis de volatilidad y performance
2. **ticker_parameters_recommendations.csv** - Tabla de recomendaciones
3. **ticker_parameters_analysis.png** - Visualizaciones (9 gráficos)

### Documentación Relacionada
1. **FASE_2_RESUMEN_COMPLETO.md** - Contexto general de optimización
2. **PROPUESTA_SCORING_OPTIMIZADO.md** - Scoring system optimization

### Backtests Relevantes
1. **ml_dataset_10_tickers.csv** - Dataset con 44 trades
2. **test_backtest_10_tickers.py** - Script de backtesting multi-ticker

---

## ✅ Validación

### Checklist de Implementación

- [x] Módulo `adaptive_config.py` creado
- [x] Clasificación de tickers por volatilidad (High/Medium/Low)
- [x] Clasificación por tipo de activo (ETF/Tech/Commodity)
- [x] Profit targets adaptativos por ticker
- [x] Stop losses adaptativos por ticker
- [x] DTE ranges optimizados por tipo
- [x] Integración en backtester_multi.py
- [x] Testing unitario del módulo
- [x] Documentación completa

### Próximos Pasos

1. **Ejecutar backtest** con parámetros adaptativos
2. **Comparar resultados** vs scoring optimizado (TODO #4)
3. **Validar mejora** en early closure rate y PnL
4. **Ajustar parámetros** si necesario basado en resultados
5. **Documentar hallazgos** en reporte final

---

**Fecha de Implementación:** 2025-01-20  
**Autor:** Sistema de Trading Algorítmico  
**Versión:** 1.0  
**Status:** ✅ Implementado - Pendiente validación en backtest
