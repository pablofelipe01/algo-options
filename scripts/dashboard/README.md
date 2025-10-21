# 📊 Options Backtesting Dashboard

Dashboard interactivo construido con **Streamlit** para visualizar y analizar los resultados del sistema de backtesting de opciones.

## 🚀 Inicio Rápido

### Prerequisitos

El dashboard requiere que hayas ejecutado previamente el pipeline de backtest:

```bash
# 1. Ejecutar el backtest principal
python scripts/backtest/test_backtest_10_tickers.py

# 2. Generar análisis (opcional pero recomendado)
python scripts/backtest/analyze_backtest_results.py
python scripts/backtest/analyze_early_closures.py
python scripts/backtest/compare_scoring_optimization.py
python scripts/backtest/analyze_ticker_parameters.py
```

### Lanzar el Dashboard

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar dashboard
streamlit run scripts/dashboard/app.py
```

El dashboard se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## 📋 Estructura del Dashboard

El dashboard está organizado en **5 pestañas principales**:

### 1. 📈 Overview
**Resumen general del backtest**

- **Métricas principales:**
  - Total Trades
  - Win Rate
  - Total PnL
  - ROI (Return on Investment)
  - Sharpe Ratio

- **Visualizaciones:**
  - Equity Curve (evolución del capital)
  - Distribución de PnL
  - Performance por estrategia

- **Imagen:** Análisis detallado de resultados (`analysis_results.png`)

---

### 2. 🎯 Performance por Ticker
**Análisis detallado de cada ticker**

- **Métricas destacadas:**
  - Mejor ticker (por PnL)
  - Más operado (por cantidad)
  - Mejor Win Rate

- **Filtros interactivos:**
  - Selección múltiple de tickers
  - Ordenamiento por diferentes métricas

- **Visualizaciones:**
  - Ranking de tickers (tabla)
  - Total PnL por ticker (gráfico de barras)
  - Win Rate por ticker (gráfico de barras)
  - Scatter plot: PnL vs Trades (tamaño = Win Rate)

- **Análisis individual:**
  - Selecciona un ticker específico
  - Ve su equity curve individual
  - Métricas detalladas

---

### 3. ⏱️ Early Closures
**Análisis de cierres anticipados vs expiración**

- **Comparación:**
  - Early Closures (cierres por profit/loss)
  - Expirations (cierres por vencimiento)

- **Métricas:**
  - Total y porcentaje de cada tipo
  - Ratio Early/Expiration
  - PnL por tipo de cierre

- **Análisis temporal:**
  - Días promedio mantenidos
  - Ventaja de rotación de capital
  - Timeline de cierres

- **Visualizaciones:**
  - Pie chart (distribución)
  - Bar chart (PnL comparativo)
  - Box plot (días mantenidos)
  - Timeline (frecuencia a lo largo del tiempo)

---

### 4. 📊 ML Dataset Viewer
**Explorador interactivo del dataset completo**

- **Filtros:**
  - Por ticker
  - Por estrategia
  - Por resultado (ganadores/perdedores)
  - Búsqueda de texto

- **Funcionalidades:**
  - Selector de columnas a mostrar
  - Estadísticas descriptivas
  - Histogramas de variables numéricas
  - Matriz de correlación

- **Descarga:**
  - CSV filtrado completo
  - CSV solo columnas seleccionadas

---

### 5. ⚙️ Parámetros Adaptativos
**Recomendaciones de parámetros por ticker**

- **Clasificación por volatilidad:**
  - Alta Volatilidad (>2.5%)
  - Volatilidad Media (1.5-2.5%)
  - Baja Volatilidad (<1.5%)

- **Parámetros recomendados:**
  - Profit Target (%)
  - Stop Loss (%)
  - DTE Range (Days to Expiration)

- **Visualizaciones:**
  - Profit Targets por ticker
  - Stop Loss por ticker
  - DTE Ranges
  - Volatilidad vs Parámetros (scatter plots)

- **Explicaciones:**
  - Metodología de cálculo
  - Cómo implementar los parámetros
  - Beneficios del approach adaptativo

---

## 🗂️ Estructura de Archivos

```
scripts/dashboard/
├── app.py                          # Aplicación principal de Streamlit
├── components/                     # Componentes modulares
│   ├── __init__.py                # Inicialización del paquete
│   ├── overview.py                # Tab 1: Overview
│   ├── performance.py             # Tab 2: Performance por Ticker
│   ├── early_closures.py          # Tab 3: Early Closures
│   ├── ml_dataset.py              # Tab 4: ML Dataset Viewer
│   └── parameters.py              # Tab 5: Parámetros Adaptativos
└── README.md                       # Esta documentación
```

---

## 📊 Datos Utilizados

El dashboard carga automáticamente:

### CSV Files:
- `data/analysis/ml_dataset_10_tickers.csv` - Dataset principal del backtest
- `data/analysis/ticker_parameters_recommendations.csv` - Parámetros adaptativos

### PNG Files:
- `scripts/visualizations/analysis_results.png` - Análisis general
- `scripts/visualizations/early_closures_analysis.png` - Análisis de cierres
- `scripts/visualizations/scoring_optimization_comparison.png` - Comparación de scoring
- `scripts/visualizations/ticker_parameters_analysis.png` - Análisis de parámetros

---

## ⚙️ Configuración

### Configuración de la Página

```python
st.set_page_config(
    page_title="Options Backtesting Dashboard",
    page_icon="📊",
    layout="wide",                  # Layout ancho
    initial_sidebar_state="expanded"  # Sidebar visible
)
```

### Variables de Entorno

El dashboard no requiere variables de entorno. Toda la configuración está en el código.

---

## 🎨 Features Principales

### ✅ Interactividad
- Filtros dinámicos en tiempo real
- Selección múltiple de tickers
- Búsqueda de texto
- Hover tooltips informativos

### ✅ Visualizaciones
- Gráficos interactivos con Plotly
- Zoom, pan, y export a PNG
- Múltiples tipos: bar, line, scatter, pie, box, heatmap
- Color coding por categorías

### ✅ Navegación
- Sidebar con métricas generales
- Tabs organizados por tema
- Expanders para información adicional
- Botones de descarga

### ✅ Responsivo
- Layout adaptable a diferentes pantallas
- Columnas que se reorganizan
- Gráficos que escalan

---

## 🔧 Personalización

### Modificar Colores

Los colores están definidos en cada componente. Para cambiarlos globalmente:

```python
# En cada componente (overview.py, performance.py, etc.)

# Colores actuales:
COLORS = {
    'profit': '#00cc96',      # Verde
    'loss': '#ef553b',        # Rojo
    'neutral': '#636efa',     # Azul
    'warning': '#ffa15a'      # Naranja
}
```

### Agregar Nuevas Métricas

Para agregar una nueva métrica en Overview:

```python
# En components/overview.py
with col6:  # Nueva columna
    st.metric(
        label="Tu Nueva Métrica",
        value=calcular_metrica(df),
        delta="Tu delta"
    )
```

### Crear un Nuevo Tab

1. Crea un nuevo archivo en `components/`:
```bash
touch scripts/dashboard/components/nuevo_tab.py
```

2. Implementa la función `render()`:
```python
def render(df, images):
    st.header("Título del Tab")
    # Tu código aquí
```

3. Agrégalo a `app.py`:
```python
from scripts.dashboard.components import nuevo_tab

# En main()
tab6 = st.tabs(["Nuevo Tab"])
with tab6:
    nuevo_tab.render(df, images)
```

---

## 🐛 Troubleshooting

### Error: "No se encontró el archivo ml_dataset_10_tickers.csv"

**Solución:** Ejecuta primero el backtest principal:
```bash
python scripts/backtest/test_backtest_10_tickers.py
```

### Error: "ModuleNotFoundError: No module named 'streamlit'"

**Solución:** Instala las dependencias:
```bash
source venv/bin/activate
pip install streamlit plotly
```

### El dashboard no se abre automáticamente

**Solución:** Abre manualmente en tu navegador:
```
http://localhost:8501
```

### Las imágenes no se muestran

**Solución:** Ejecuta los scripts de análisis:
```bash
python scripts/backtest/analyze_backtest_results.py
python scripts/backtest/analyze_early_closures.py
python scripts/backtest/analyze_ticker_parameters.py
```

### Warning de urllib3/OpenSSL

Este es un warning que puedes ignorar. No afecta la funcionalidad del dashboard.

---

## 📈 Mejores Prácticas

### 1. Mantén los Datos Actualizados
Ejecuta el pipeline completo regularmente:
```bash
# Script automatizado (puedes crearlo)
./scripts/backtest/run_full_pipeline.sh
```

### 2. Exporta Visualizaciones
Usa los botones de descarga de Plotly para guardar gráficos específicos.

### 3. Compara Períodos
Guarda snapshots del CSV en diferentes fechas para comparar evolución.

### 4. Documenta Cambios
Si modificas parámetros, anota los cambios y sus efectos.

---

## 🚀 Roadmap Futuro

### Próximas Features
- [ ] Comparación de múltiples backtests
- [ ] Integración con ML models para predicciones
- [ ] Alertas automáticas de parámetros desviados
- [ ] Export de reportes en PDF
- [ ] Modo dark/light theme
- [ ] Autenticación multi-usuario
- [ ] Deploy en cloud (Streamlit Cloud)

---

## 📚 Recursos

### Documentación Oficial
- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Python Docs](https://plotly.com/python/)

### Tutoriales Relacionados
- [Streamlit Gallery](https://streamlit.io/gallery)
- [Plotly Examples](https://plotly.com/python/basic-charts/)

---

## 👤 Soporte

Si tienes problemas o preguntas:

1. Revisa la sección de [Troubleshooting](#-troubleshooting)
2. Verifica que todos los archivos CSV/PNG existan
3. Asegúrate de estar en el entorno virtual correcto
4. Revisa los logs de la terminal donde se ejecuta Streamlit

---

## 📝 Changelog

### v1.0.0 (2025-10-21)
- ✨ Implementación inicial
- 📊 5 tabs completos (Overview, Performance, Early Closures, ML Dataset, Parameters)
- 🎨 Visualizaciones interactivas con Plotly
- 📥 Funcionalidad de descarga de datos
- 📱 Diseño responsivo

---

**Creado con ❤️ usando Streamlit y Plotly**
