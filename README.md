# 📊 Sistema de Extracción y Análisis de Datos de Opciones

Sistema automatizado para extraer, almacenar y analizar datos históricos de opciones usando Polygon.io API.

---

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Configuración Inicial](#configuración-inicial)
- [Scripts Disponibles](#scripts-disponibles)
- [Uso](#uso)
- [Datos Disponibles](#datos-disponibles)
- [Análisis](#análisis)
- [Mantenimiento](#mantenimiento)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción

Sistema completo para:
- ✅ Extraer datos históricos de opciones (últimos 60 días)
- ✅ Actualización incremental semanal
- ✅ Análisis de liquidez, griegas, IV y Put/Call Ratio
- ✅ Comparación multi-ticker
- ✅ Almacenamiento eficiente en formato Parquet

### Datos Actuales:
- **10 tickers**: SPY, QQQ, IWM, AAPL, MSFT, NVDA, TSLA, AMZN, GLD, SLV
- **~116K contratos** de opciones
- **10 fechas** históricas
- **82% completitud** de datos
- **6.2 MB** de almacenamiento

---

## 💻 Requisitos

### Software:
- Python 3.9+
- Mac OS (o Linux)
- Polygon.io API Key (plan Options Starter $29/mes)

### Librerías Python:
- pandas
- pyarrow
- requests
- python-dotenv

---

## 🚀 Instalación

### 1. Clonar/Crear proyecto:
```bash
mkdir ~/Desktop/otions-data
cd ~/Desktop/otions-data
```

### 2. Crear entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias:
```bash
pip install pandas pyarrow requests python-dotenv
```

### 4. Crear estructura de carpetas:
```bash
mkdir -p data/historical logs scripts
```

### 5. Configurar API Key:
```bash
echo "POLYGON_API_KEY=tu_api_key_aqui" > .env
```

---

## 📁 Estructura del Proyecto
```
otions-data/
├── data/
│   └── historical/
│       ├── SPY_60days.parquet        # Datos SPY
│       ├── QQQ_60days.parquet        # Datos QQQ
│       ├── ...                       # Otros tickers
│       └── SUMMARY.csv               # Resumen general
│
├── logs/
│   ├── extraction.log                # Log extracción histórica
│   └── daily_update_YYYYMMDD.log     # Logs actualizaciones
│
├── scripts/
│   ├── extract_test.py               # Test de extracción
│   ├── extract_historical.py         # Extracción 60 días
│   ├── daily_update.py               # Actualización incremental
│   ├── verify_all.py                 # Verificación de datos
│   ├── analyze_data.py               # Análisis completo
│   ├── weekly_update.sh              # Wrapper ejecutable
│   └── quick_analysis.sh             # Análisis rápido
│
├── .env                              # API Key (NO compartir)
├── venv/                             # Entorno virtual
└── README.md                         # Este archivo
```

---

## ⚙️ Configuración Inicial

### 1. Obtener API Key:
1. Registrarse en https://polygon.io
2. Suscribirse al plan "Options Starter" ($29/mes)
3. Obtener API key en Dashboard
4. Agregar a `.env`: `POLYGON_API_KEY=tu_key_aqui`

### 2. Test inicial:
```bash
cd ~/Desktop/otions-data
source venv/bin/activate
python scripts/extract_test.py
```

**Resultado esperado:** Extracción de ~1,400 contratos de SPY.

### 3. Extracción histórica completa:
```bash
python scripts/extract_historical.py
```

**Tiempo:** ~15-20 minutos  
**Resultado:** 10 archivos `.parquet` con ~116K registros totales

### 4. Verificación:
```bash
python scripts/verify_all.py
```

---

## 📜 Scripts Disponibles

### `extract_test.py`
**Propósito:** Test rápido de extracción  
**Uso:**
```bash
python scripts/extract_test.py
```
**Output:** 1 ticker, 1 fecha, ~1,400 contratos

---

### `extract_historical.py`
**Propósito:** Extracción histórica completa (60 días)  
**Uso:**
```bash
python scripts/extract_historical.py
```
**Configuración:**
- Tickers: 10 (índices, stocks, commodities)
- Período: Últimos 60 días
- Frecuencia: Semanal (viernes)
- DTE: 15-60 días

**Output:** Archivos `{TICKER}_60days.parquet`

---

### `daily_update.py`
**Propósito:** Actualización incremental  
**Uso:**
```bash
python scripts/daily_update.py
```
**Función:**
- Extrae datos del día actual
- Agrega a archivos existentes
- Mantiene últimos 90 días
- Evita duplicados

---

### `verify_all.py`
**Propósito:** Verificación de calidad de datos  
**Uso:**
```bash
python scripts/verify_all.py
```
**Output:**
- Resumen por ticker
- Completitud de datos
- Estadísticas generales
- Archivo `SUMMARY.csv`

---

### `analyze_data.py`
**Propósito:** Análisis completo e interactivo  
**Uso:**
```bash
python scripts/analyze_data.py
```
**Menú:**
1. Análisis completo de un ticker
2. Comparación multi-ticker
3. Análisis rápido SPY
4. Análisis rápido QQQ
5. Salir

**Análisis incluidos:**
- 💧 Liquidez (volumen, OI)
- 🎯 Griegas (delta, gamma, theta, vega)
- 📉 Evolución de IV
- 📊 Put/Call Ratio
- 🎯 Opciones ATM

---

### `weekly_update.sh`
**Propósito:** Wrapper para actualización semanal  
**Uso:**
```bash
./scripts/weekly_update.sh
```
**Función:**
- Ejecuta `daily_update.py`
- Ejecuta `verify_all.py`
- Muestra resumen visual

---

## 🎮 Uso

### Rutina Semanal (Recomendado)

**Cada Viernes a las 5 PM:**

1. **Ejecutar actualización:**
```bash
   cd ~/Desktop/otions-data
   ./scripts/weekly_update.sh
```

2. **O doble-clic en:**
```
   ActualizarOpciones.command (escritorio)
```

3. **Verificar resultado:**
   - ✅ "Actualización completada"
   - Revisar resumen de tickers actualizados

### Análisis de Datos

**Opción 1: Menú interactivo**
```bash
python scripts/analyze_data.py
```

**Opción 2: Doble-clic**
```
AnalizarOpciones.command (escritorio)
```

**Ejemplos de análisis:**
- Análisis completo SPY
- Comparar SPY vs QQQ vs AAPL
- Identificar opciones más líquidas
- Ver evolución de Put/Call Ratio

---

## 📊 Datos Disponibles

### Por Contrato:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `date` | Fecha de snapshot | 2025-10-20 |
| `ticker` | Identificador del contrato | O:SPY251121P00628000 |
| `underlying` | Ticker subyacente | SPY |
| `type` | Tipo de opción | call / put |
| `strike` | Precio de ejercicio | 628.0 |
| `expiration` | Fecha de vencimiento | 2025-11-21 |
| `dte` | Días hasta vencimiento | 35 |
| `open` | Precio apertura | 4.50 |
| `high` | Precio máximo | 5.20 |
| `low` | Precio mínimo | 4.30 |
| `close` | Precio cierre | 4.79 |
| `volume` | Volumen negociado | 36,833 |
| `vwap` | Precio promedio ponderado | 4.65 |
| `delta` | Delta | -0.1857 |
| `gamma` | Gamma | 0.0125 |
| `theta` | Theta | -0.0534 |
| `vega` | Vega | 0.2145 |
| `iv` | Volatilidad implícita | 0.2274 (22.74%) |
| `oi` | Open Interest | 2,456 |

### Formato de Almacenamiento:

**Parquet:**
- Compresión: Snappy
- Tamaño promedio: 0.5-1.5 MB por ticker
- Lectura rápida con pandas

---

## 📈 Análisis

### 1. Análisis de Liquidez

**Métricas:**
- Volumen total y promedio
- Open Interest
- Top contratos por volumen
- Volumen por DTE

**Ejemplo SPY:**
```
Volumen total: 15,687,318
Volumen promedio: 731
OI promedio: 2,246
```

### 2. Análisis de Griegas

**Métricas:**
- Estadísticas de delta, gamma, theta, vega
- Delta promedio por tipo (call/put)
- Distribución de griegas

**Interpretación:**
- Delta alto (>0.7) = In-The-Money
- Delta bajo (<0.3) = Out-The-Money
- Gamma alto = Mayor sensibilidad
- Theta negativo = Decay diario

### 3. Análisis de IV

**Métricas:**
- IV promedio por fecha
- Tendencia de IV
- IV por moneyness
- IV Smile

**Interpretación:**
- IV alto = Opciones caras
- IV bajo = Opciones baratas
- IV smile = Patrón normal (OTM más caro que ATM)

### 4. Put/Call Ratio

**Métricas:**
- Ratio por fecha
- Tendencia
- Interpretación de sesgo

**Interpretación:**
- Ratio > 1.5 = Sesgo bearish
- Ratio < 0.7 = Sesgo bullish
- Ratio 0.7-1.5 = Relativamente balanceado

### 5. Opciones ATM

**Métricas:**
- Strike medio
- Contratos ATM (±2%)
- Top 5 por volumen
- IV y delta de ATM

**Uso:**
- Identificar strikes más líquidos
- Establecer estrategias de spreads
- Iron Condors alrededor de ATM

---

## 🔧 Mantenimiento

### Actualización Regular

**Semanal (Recomendado):**
```bash
./scripts/weekly_update.sh
```

**Manual (si necesario):**
```bash
python scripts/daily_update.py
```

### Limpieza de Datos Antiguos

El script mantiene automáticamente últimos 90 días. Para limpieza manual:
```python
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Ejemplo: mantener solo últimos 60 días
cutoff = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

for file in Path("data/historical").glob("*_60days.parquet"):
    df = pd.read_parquet(file)
    df = df[df['date'] >= cutoff]
    df.to_parquet(file, compression='snappy', index=False)
```

### Verificación de Integridad

**Ejecutar periódicamente:**
```bash
python scripts/verify_all.py
```

**Verificar:**
- ✅ Todos los tickers tienen datos
- ✅ Completitud >70%
- ✅ Fechas actualizadas
- ✅ Sin errores en logs

---

## 🐛 Troubleshooting

### Error: "API Key not found"

**Solución:**
```bash
echo "POLYGON_API_KEY=tu_key_real" > .env
```

### Error: "No such file or directory"

**Solución:**
```bash
cd ~/Desktop/otions-data
mkdir -p data/historical logs
```

### Error: "Unable to find a usable engine"

**Solución:**
```bash
pip install pyarrow
```

### Datos con baja completitud (<70%)

**Causa:** Algunas opciones no se negocian ese día  
**Solución:** Normal, especialmente en commodities

### "Fecha ya existe, saltando"

**Causa:** Ya actualizaste hoy  
**Solución:** Normal, esperar al próximo día de mercado

### Logs de errores

**Revisar:**
```bash
tail -50 logs/extraction.log
tail -50 logs/daily_update_*.log
```

---

## 📅 Recordatorio en Calendar

### Configurar alerta semanal:

1. Abrir **Calendar**
2. Nuevo evento (Cmd + N)
3. Configurar:
   - Título: 🔔 Actualizar Datos de Opciones
   - Repetir: Cada semana (viernes)
   - Hora: 5:00 PM
   - Alerta: 30 minutos antes

---

## 🎯 Mejores Prácticas

### Extracción:
- ✅ Ejecutar después del cierre del mercado (5 PM)
- ✅ Verificar completitud después de cada extracción
- ✅ Revisar logs si hay errores
- ✅ Mantener backup de datos importantes

### Análisis:
- ✅ Comparar múltiples fechas para ver tendencias
- ✅ Usar Put/Call Ratio como indicador de sentimiento
- ✅ Identificar strikes más líquidos para trading
- ✅ Monitorear IV para timing de estrategias

### Almacenamiento:
- ✅ Los archivos Parquet son eficientes
- ✅ Backup periódico de `data/historical/`
- ✅ Limpiar logs antiguos cada mes

---

## 📚 Recursos

### Polygon.io:
- Documentación: https://polygon.io/docs
- Dashboard: https://polygon.io/dashboard
- Pricing: https://polygon.io/pricing

### Análisis de Opciones:
- Greeks explicados: https://www.investopedia.com/terms/g/greeks.asp
- IV Rank: https://www.tastytrade.com/definitions/implied-volatility-rank
- Put/Call Ratio: https://www.investopedia.com/terms/p/putcallratio.asp

---

## 🚀 Próximos Pasos

### Corto Plazo (1-2 semanas):
- [ ] Acumular más datos históricos
- [ ] Familiarizarse con análisis
- [ ] Identificar patrones de liquidez

### Mediano Plazo (1-2 meses):
- [ ] Desarrollar estrategias de trading
- [ ] Backtesting de Iron Condors
- [ ] Análisis de spreads

### Largo Plazo (3+ meses):
- [ ] Automatización con GitHub Actions
- [ ] Dashboard visual con Streamlit
- [ ] Machine Learning para predicción de IV

---

## 📊 Estadísticas del Sistema

**Última actualización:** 2025-10-20

| Métrica | Valor |
|---------|-------|
| Total registros | 116,656 |
| Tickers | 10 |
| Fechas históricas | 10 |
| Completitud promedio | 82.0% |
| Volumen total | 42.3M |
| Storage total | 6.2 MB |
| IV promedio | 56.9% |

---

## 📝 Changelog

### v1.0.0 (2025-10-20)
- ✅ Sistema inicial completado
- ✅ Extracción de 10 tickers
- ✅ Análisis completo implementado
- ✅ Actualización semanal configurada
- ✅ Documentación completa

---

## 👤 Autor

Sistema desarrollado para análisis y backtesting de opciones.

---

## 📄 Licencia

Uso personal. No redistribuir con API key incluida.

---

## 🙏 Agradecimientos

- Polygon.io por API de opciones
- Pandas por manejo eficiente de datos
- PyArrow por formato Parquet

---

**¿Preguntas? Revisa la sección de [Troubleshooting](#troubleshooting)**# algo-options
