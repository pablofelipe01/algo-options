# 🎯 Sistema de Trading Algorítmico de Opciones

Sistema completo de trading algorítmico para opciones, con extracción de datos, análisis cuantitativo, backtesting multi-ticker y parámetros adaptativos.

---

## 📊 Estado del Proyecto

**Versión:** 2.0 - Fase 2 Completada  
**Fecha:** 2025-10-21  
**Status:** ✅ Production Ready

### Métricas Clave del Sistema

| Métrica | Valor |
|---------|-------|
| **PnL Total** | $8,594 |
| **Win Rate** | 100% |
| **Trades** | 37 |
| **Early Closures** | 45.9% |
| **Sharpe Ratio** | 10.07 |
| **BSM Fallback** | 34% usage, 0% failures |

---

## 🗂️ Estructura del Proyecto

```
otions-data/
├── data/
│   ├── historical/          # Datos históricos (116K contratos, 10 tickers)
│   └── analysis/            # Datasets de análisis y resultados
│
├── documents/               # 📚 Documentación completa
│   ├── INDEX.md             # Índice de toda la documentación
│   ├── README.md            # Guía de uso del data pipeline
│   ├── FASE_2_COMPLETADA.md # Resumen ejecutivo Fase 2
│   └── ... (9 archivos)
│
├── scripts/
│   ├── data_pipeline/       # 🔄 Extracción y verificación de datos
│   ├── quantitative/        # 🧮 Black-Scholes, Greeks, Probabilidad
│   ├── strategies/          # 🎲 Backtester + Estrategias
│   ├── backtest/            # 📊 Tests y análisis
│   └── visualizations/      # 📈 Gráficos (8 PNGs, 45 gráficos)
│
└── logs/                    # Logs de ejecución
```

---

## 🚀 Quick Start

### 1. Configuración Inicial

```bash
# Clonar y configurar entorno
cd ~/Desktop/otions-data
python3 -m venv venv
source venv/bin/activate
pip install pandas pyarrow requests python-dotenv scipy matplotlib seaborn

# Configurar API Key
echo "POLYGON_API_KEY=tu_api_key" > .env
```

### 2. Extracción de Datos

```bash
# Test de conexión (rápido)
python scripts/data_pipeline/extract_test.py

# Extracción histórica completa (15-20 min)
python scripts/data_pipeline/extract_historical.py

# Verificar datos
python scripts/data_pipeline/verify_all.py
```

### 3. Ejecutar Backtesting

```bash
# Backtest con 10 tickers y parámetros adaptativos
python scripts/backtest/test_backtest_10_tickers.py

# Ver resultados en scripts/visualizations/
```

---

## 📚 Documentación

### Documentos Principales

| Documento | Descripción |
|-----------|-------------|
| **[documents/INDEX.md](documents/INDEX.md)** | 📖 Índice completo de documentación |
| **[documents/README.md](documents/README.md)** | 📊 Guía del data pipeline |
| **[documents/FASE_2_COMPLETADA.md](documents/FASE_2_COMPLETADA.md)** | 🏆 Resumen ejecutivo Fase 2 |
| **[documents/PARAMETROS_ADAPTATIVOS.md](documents/PARAMETROS_ADAPTATIVOS.md)** | 🎯 Sistema de parámetros adaptativos |
| **[documents/quantitative_README.md](documents/quantitative_README.md)** | 🧮 Módulo cuantitativo (BSM) |
| **[documents/strategies_README.md](documents/strategies_README.md)** | 🎲 Estrategias de trading |

---

## 🔧 Componentes del Sistema

### 1. Data Pipeline (`scripts/data_pipeline/`)
- **Extracción:** `extract_historical.py`, `extract_test.py`
- **Actualización:** `daily_update.py`, `weekly_update.sh`
- **Verificación:** `verify_all.py`, `verify_data.py`
- **Análisis:** `analyze_data.py`

**Datos:** 116,656 contratos de opciones de 10 tickers (SPY, QQQ, IWM, AAPL, MSFT, NVDA, TSLA, AMZN, GLD, SLV)

### 2. Módulo Cuantitativo (`scripts/quantitative/`)
- **Black-Scholes-Merton:** Valorización con fallback automático
- **Greeks:** Delta, Gamma, Theta, Vega, Rho
- **Probabilidad:** PoP, Expected Value
- **Validaciones:** Análisis de sensibilidad

### 3. Estrategias (`scripts/strategies/`)
- **Iron Condor:** Estrategia principal
- **Backtester Multi-Ticker:** Soporte para 10 tickers simultáneos
- **Parámetros Adaptativos:** Por volatilidad y tipo de activo
- **Risk Manager:** Gestión dinámica de riesgo
- **Filtros:** Liquidez, Volatilidad, Delta, DTE

### 4. Backtesting y Análisis (`scripts/backtest/`)
- **Tests:** `test_backtest_10_tickers.py`, `test_backtest_multi.py`
- **Análisis:** 
  - Resultados de backtest
  - Cierres anticipados
  - Parámetros por ticker
  - Comparaciones (GLD vs TSLA, scoring optimization)

### 5. Visualizaciones (`scripts/visualizations/`)
8 archivos PNG con 45 gráficos totales mostrando:
- Distribuciones de PnL
- Análisis de early closures
- Parámetros recomendados por ticker
- Comparaciones de performance

---

## 🎯 Features Clave - Fase 2

### ✨ Parámetros Adaptativos por Ticker
- **Clasificación por volatilidad:** High (≥0.40 IV), Medium (0.25-0.40), Low (<0.25)
- **Clasificación por tipo:** ETF, Tech, Commodity
- **Profit targets dinámicos:**
  - TSLA: 20% (ultra-agresivo)
  - SPY/QQQ: 30% (ajustado)
  - Tech stocks: 25%
  - Commodities: 25%
- **Stop losses adaptativos:** 200% (High Vol), 150% (Medium), 100% (Low)
- **DTE ranges optimizados:** Tech 42-49, ETF 49-56, Commodity 56-60 días

### 📊 Scoring System Optimizado
- **Premium/Risk:** 45% (correlación +0.633)
- **DTE Long Bias:** 20% (sweet spot 42-56 días)
- **ATM Preference:** 15% (opciones líquidas)
- **Volatility Edge:** 10% (alta IV)
- **Market Context:** 10% (VIX, sentimiento)

### 🔧 BSM Fallback System
- **Uso:** 34% de las valorizaciones
- **Éxito:** 0% failures
- **Función:** Estima valor cuando faltan datos de mercado
- **Impacto:** Habilita early closures (0% → 45.9%)

---

## 📈 Resultados de Backtesting

### Evolución del Sistema

| Métrica | V1.0 (Bug) | V2.0 (BSM+Scoring) | V3.0 (Adaptive) |
|---------|------------|-------------------|-----------------|
| **Trades** | 20 | 44 | 37 |
| **PnL** | $2,839 | $11,099 | $8,594 |
| **Win Rate** | 100% | 88.6% | 100% |
| **Early Closures** | 0% | 54.5% | 45.9% |
| **Sharpe Ratio** | 11.08 | 6.93 | 10.07 |
| **Avg Days Held** | 60 | 36 | 38 |

### Top Performers (V3.0)
1. **GLD:** $4,654 PnL (8 trades)
2. **SPY:** $2,157 PnL (7 trades)
3. **QQQ:** $1,783 PnL (7 trades)

---

## 🔄 Mantenimiento Semanal

### Actualización de Datos (Viernes 5 PM)

```bash
cd ~/Desktop/otions-data
source venv/bin/activate
./scripts/data_pipeline/weekly_update.sh
```

Esto ejecuta:
1. ✅ `daily_update.py` - Extrae datos del día
2. ✅ `verify_all.py` - Verifica calidad
3. ✅ Muestra resumen visual

---

## 🛠️ Tecnologías

- **Python 3.9+**
- **Polygon.io API** (Options Starter $29/mes)
- **Pandas, NumPy** - Análisis de datos
- **SciPy** - Black-Scholes-Merton
- **Matplotlib, Seaborn** - Visualizaciones
- **PyArrow** - Almacenamiento Parquet eficiente

---

## 📞 Recursos Adicionales

- **Repositorio:** [github.com/pablofelipe01/algo-options](https://github.com/pablofelipe01/algo-options)
- **Documentación completa:** Ver `documents/INDEX.md`
- **API Reference:** [polygon.io/docs](https://polygon.io/docs)

---

## 🎯 Próximos Pasos - Fase 3

### Corto Plazo (1-2 semanas)
- [ ] Forward testing 30 días
- [ ] Monitorear early closure rate >50%
- [ ] Refinar parámetros TSLA (considerar PT 15%)

### Medio Plazo (1-3 meses)
- [ ] Machine Learning integration
- [ ] Regime detection (Bull/Bear/High VIX)
- [ ] Multi-strategy (covered calls, CSPs, calendar spreads)

### Largo Plazo (3-6 meses)
- [ ] Portfolio optimization (MPT, correlation-based)
- [ ] Real-time monitoring dashboard
- [ ] Automated execution via broker API

---

## 📝 Changelog

### v2.0 - 2025-10-21
- ✅ Sistema de parámetros adaptativos por ticker
- ✅ Reorganización modular completa
- ✅ 5 folders temáticos en scripts/
- ✅ Documentación exhaustiva (9 archivos)

### v1.0 - 2025-10-20
- ✅ Fase 2 completada (TODO #1-5)
- ✅ BSM fallback implementation
- ✅ Scoring system optimizado
- ✅ Early closures habilitados (45.9%)
- ✅ 19 archivos generados (scripts, visualizaciones, datasets)

---

**Made with ❤️ for algorithmic options trading**
