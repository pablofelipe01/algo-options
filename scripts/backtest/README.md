# 📊 Backtesting Suite

Sistema completo de backtesting y análisis para estrategias de opciones Iron Condor con parámetros adaptativos.

---

## 🗂️ Estructura del Directorio

```
scripts/backtest/
├── README.md                              # Este archivo
├── logs/                                  # Logs de ejecución
│   └── backtest_optimized_scoring.log
├── test_backtest_10_tickers.py           # 1️⃣ Script Principal
├── analyze_backtest_results.py           # 2️⃣ Análisis Exploratorio (TODO #1)
├── analyze_early_closures.py             # 3️⃣ Análisis de Timing (TODO #3)
├── compare_scoring_optimization.py       # 4️⃣ Validación Scoring V3.0 (TODO #4)
└── analyze_ticker_parameters.py          # 5️⃣ Parámetros Adaptativos (TODO #5)
```

---

## 🚀 Pipeline de Ejecución

### **Paso 1: Backtest Principal** 🎯

Ejecuta el backtest completo con 10 tickers y parámetros adaptativos.

```bash
# Desde el directorio raíz del proyecto
python scripts/backtest/test_backtest_10_tickers.py
```

**Tiempo estimado:** 2-3 minutos  
**Outputs:**
- `scripts/visualizations/backtest_10_tickers_results.png` - Gráficos de equity, drawdown, PnL
- `data/analysis/ml_dataset_10_tickers.csv` - Dataset de 37 trades para ML

**Métricas generadas:**
- Capital inicial/final
- PnL total y retorno %
- Win rate y Sharpe ratio
- Distribución de trades por ticker
- Performance de parámetros adaptativos

---

### **Paso 2: Análisis Exploratorio** 📊 (TODO #1)

Análisis profundo de resultados con comparaciones por ticker y categoría.

```bash
python scripts/backtest/analyze_backtest_results.py
```

**Tiempo estimado:** 30-60 segundos  
**Outputs:**
- `scripts/visualizations/analysis_results.png` - 9 gráficos de análisis

**Análisis incluido:**
- 🏆 Ranking de tickers por performance
- 📦 Performance por categoría (ETFs, Tech, Commodities)
- ❓ Respuestas a preguntas clave:
  - ¿Por qué GLD superó a SPY?
  - ¿Qué tienen en común los mejores trades?
  - ¿Por qué solo el 46% cerró anticipadamente?
- 🔗 Correlaciones entre variables
- 💡 Recomendaciones de optimización

---

### **Paso 3: Análisis de Cierres Anticipados** ⏰ (TODO #3)

Estudia la efectividad de profit targets y stop losses.

```bash
python scripts/backtest/analyze_early_closures.py
```

**Tiempo estimado:** 30-60 segundos  
**Outputs:**
- `scripts/visualizations/early_closures_analysis.png` - 9 gráficos de timing

**Análisis incluido:**
- 🎯 Comparación: `closed_profit` vs `closed_loss` vs `closed_end`
- 📊 Performance por tipo de cierre
- ⏱️ Días promedio hasta cerrar vs expirar
- 💰 PnL por estrategia de exit
- 📈 ¿Qué tickers se benefician más de early closures?
- 💡 Early closures liberan capital 1.2x más rápido

---

### **Paso 4: Validación de Scoring Optimizado** 🎯 (TODO #4)

Documenta y valida los cambios del sistema de scoring V3.0.

```bash
python scripts/backtest/compare_scoring_optimization.py
```

**Tiempo estimado:** 30-60 segundos  
**Outputs:**
- `scripts/visualizations/scoring_optimization_comparison.png` - 9 gráficos

**Análisis incluido:**
- 📋 Cambios en pesos del scoring:
  ```
  Premium/Risk Ratio: 30% → 45% (+15%)
  DTE Long Bias: 10% → 20% (+10%)
  Liquidez: 20% → 15% (-5%)
  IV Rank: 15% → 10% (-5%)
  Premium Absoluto: 20% → 5% (-15%)
  ```
- 📈 Correlación scores vs PnL (+0.633)
- ✅ Validación que V3.0 > V2.0
- 💡 Justificación de cada cambio

---

### **Paso 5: Parámetros Óptimos por Ticker** ⚙️ (TODO #5)

Genera recomendaciones de profit targets, stop losses y DTEs por ticker.

```bash
python scripts/backtest/analyze_ticker_parameters.py
```

**Tiempo estimado:** 1-2 minutos  
**Outputs:**
- `data/analysis/ticker_parameters_recommendations.csv` - Tabla de recomendaciones
- `scripts/visualizations/ticker_parameters_analysis.png` - 12 gráficos

**Análisis incluido:**
- 📊 Clasificación por volatilidad:
  - High IV (≥0.40): TSLA, NVDA, etc.
  - Medium IV (0.25-0.40): SPY, QQQ, AAPL, etc.
  - Low IV (<0.25): GLD, SLV, IWM
- 🎯 Recomendaciones por ticker:
  - Profit target óptimo (20-35%)
  - Stop loss recomendado (150-200%)
  - DTE preferido (42-60 días)
  - Spread width ideal

---

## 🔄 Ejecución Completa del Pipeline

Para ejecutar todos los análisis de una vez:

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar pipeline completo
python scripts/backtest/test_backtest_10_tickers.py && \
python scripts/backtest/analyze_backtest_results.py && \
python scripts/backtest/analyze_early_closures.py && \
python scripts/backtest/compare_scoring_optimization.py && \
python scripts/backtest/analyze_ticker_parameters.py

echo "✅ Pipeline completo ejecutado"
```

**Tiempo total:** ~5-10 minutos  
**Outputs totales:**
- 5 PNGs (2.7 MB) en `scripts/visualizations/`
- 2 CSVs en `data/analysis/`

---

## 📁 Archivos Generados

### **Visualizaciones** (`scripts/visualizations/`)

| Archivo | Tamaño | Gráficos | Generado por |
|---------|--------|----------|--------------|
| `backtest_10_tickers_results.png` | 277 KB | 6 | Paso 1 |
| `analysis_results.png` | 921 KB | 9 | Paso 2 |
| `early_closures_analysis.png` | 798 KB | 9 | Paso 3 |
| `scoring_optimization_comparison.png` | 717 KB | 9 | Paso 4 |
| `ticker_parameters_analysis.png` | 274 KB | 12 | Paso 5 |

### **Datos** (`data/analysis/`)

| Archivo | Tamaño | Descripción | Generado por |
|---------|--------|-------------|--------------|
| `ml_dataset_10_tickers.csv` | 4.8 KB | 37 trades con ~30 features | Paso 1 |
| `ticker_parameters_recommendations.csv` | 2.0 KB | Parámetros óptimos por ticker | Paso 5 |

---

## 💾 Guardar Logs (Opcional)

Para guardar el output de cualquier script en un log:

```bash
# Con timestamp
python scripts/backtest/test_backtest_10_tickers.py > scripts/backtest/logs/backtest_$(date +%Y%m%d_%H%M%S).log 2>&1

# Archivo específico
python scripts/backtest/analyze_backtest_results.py > scripts/backtest/logs/analysis_results.log 2>&1

# Ver en tiempo real y guardar
python scripts/backtest/test_backtest_10_tickers.py 2>&1 | tee scripts/backtest/logs/backtest.log
```

---

## 📊 Dataset ML: `ml_dataset_10_tickers.csv`

### Columnas principales:

| Columna | Descripción | Tipo |
|---------|-------------|------|
| `ticker` | Símbolo del activo | string |
| `entry_date` | Fecha de entrada | datetime |
| `exit_date` | Fecha de salida | datetime |
| `status` | closed_profit / closed_loss / closed_end | string |
| `premium_collected` | Premium recibido | float |
| `max_risk` | Riesgo máximo | float |
| `pnl` | Profit & Loss | float |
| `return_pct` | Retorno porcentual | float |
| `dte_entry` | Days to expiration al entrar | int |
| `days_held` | Días sostenido | int |
| `iv_entry` | Volatilidad implícita | float |
| `delta_put` | Delta de put vendida | float |
| `delta_call` | Delta de call vendida | float |
| `spread_width` | Ancho del spread | float |

**Total:** ~30 features por trade

---

## 🎯 Resultados Actuales (Backtest V3.0)

### Métricas Globales

| Métrica | Valor |
|---------|-------|
| **Capital Inicial** | $20,000 |
| **Capital Final** | $28,594 |
| **PnL Total** | $8,594 |
| **Retorno Total** | 42.9% |
| **Win Rate** | 100% |
| **Sharpe Ratio** | 10.07 |
| **Total Trades** | 37 |
| **Early Closures** | 45.9% (17/37) |

### Top 3 Performers

| Ticker | Trades | Total PnL | Avg Return | Categoría |
|--------|--------|-----------|------------|-----------|
| 🥇 **TSLA** | 8 | $4,654 | 258.16% | Tech |
| 🥈 **AAPL** | 4 | $696 | 188.94% | Tech |
| 🥉 **AMZN** | 4 | $834 | 153.76% | Tech |

### Performance por Categoría

| Categoría | Trades | Avg Return | Total PnL |
|-----------|--------|------------|-----------|
| **Tech** | 24 | 156.38% | $7,155 |
| **Commodities** | 7 | 41.15% | $867 |
| **ETFs** | 6 | 24.21% | $572 |

---

## 🔍 Análisis de Dependencias

### Scripts Independientes (pueden ejecutarse solos):
- `test_backtest_10_tickers.py` ✅

### Scripts que requieren el dataset ML:
- `analyze_backtest_results.py` (requiere: `ml_dataset_10_tickers.csv`)
- `analyze_early_closures.py` (requiere: `ml_dataset_10_tickers.csv`)
- `compare_scoring_optimization.py` (requiere: `ml_dataset_10_tickers.csv`)
- `analyze_ticker_parameters.py` (requiere: `ml_dataset_10_tickers.csv` + datos históricos)

**⚠️ Importante:** Ejecuta primero el **Paso 1** para generar el dataset ML.

---

## 🛠️ Troubleshooting

### Error: `FileNotFoundError: ml_dataset_10_tickers.csv`

**Solución:** Ejecuta primero el backtest principal:
```bash
python scripts/backtest/test_backtest_10_tickers.py
```

### Error: Rutas incorrectas

Asegúrate de ejecutar desde el **directorio raíz** del proyecto:
```bash
cd ~/Desktop/otions-data
python scripts/backtest/[script_name].py
```

### Regenerar dataset ML

El dataset se sobrescribe cada vez que ejecutas el backtest:
```bash
# Esto regenera ml_dataset_10_tickers.csv
python scripts/backtest/test_backtest_10_tickers.py
```

---

## 📝 Notas Técnicas

### Configuración del Backtest
- **Capital:** $20,000 (realista para opciones)
- **Tickers:** 10 (SPY, QQQ, IWM, AAPL, MSFT, NVDA, TSLA, AMZN, GLD, SLV)
- **Período:** ~60 días (2025-08-22 → 2025-10-20)
- **Estrategia:** Iron Condor
- **Parámetros:** Adaptativos por volatilidad (High/Medium/Low IV)
- **Scoring:** V3.0 optimizado (Premium/Risk ratio = 45%)

### Parámetros Adaptativos por Volatilidad

| Volatilidad | Profit Target | Stop Loss | DTE Preferido |
|-------------|---------------|-----------|---------------|
| High (≥0.40) | 20-25% | 200% | 42-49 días |
| Medium (0.25-0.40) | 35% | 150% | 49-56 días |
| Low (<0.25) | 35% | 150% | 56-60 días |

---

## 🚀 Próximos Pasos

1. **Fase 3:** Forward testing (30 días en producción)
2. **Machine Learning:** Entrenar modelos con `ml_dataset_10_tickers.csv`
3. **Optimización:** Grid search de profit targets y stop losses
4. **Live Trading:** Integración con broker API
5. **Monitoreo:** Dashboard en tiempo real

---

## 📚 Documentación Relacionada

- **[documents/INDEX.md](../../documents/INDEX.md)** - Índice completo de documentación
- **[documents/FASE_2_COMPLETADA.md](../../documents/FASE_2_COMPLETADA.md)** - Resumen ejecutivo Fase 2
- **[documents/PARAMETROS_ADAPTATIVOS.md](../../documents/PARAMETROS_ADAPTATIVOS.md)** - Sistema de parámetros adaptativos
- **[README.md](../../README.md)** - Documentación principal del proyecto

---

## ✅ Checklist de Ejecución

- [ ] Activar entorno virtual: `source venv/bin/activate`
- [ ] Ejecutar Paso 1: Backtest principal
- [ ] Verificar dataset ML generado
- [ ] Ejecutar Paso 2: Análisis exploratorio
- [ ] Ejecutar Paso 3: Análisis de early closures
- [ ] Ejecutar Paso 4: Validación de scoring
- [ ] Ejecutar Paso 5: Parámetros por ticker
- [ ] Revisar todos los PNGs generados
- [ ] Revisar CSV de recomendaciones

---

**Última actualización:** 2025-10-21  
**Versión del sistema:** V3.0 (Scoring optimizado + Parámetros adaptativos)
