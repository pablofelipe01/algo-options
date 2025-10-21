"""
🎯 Backtesting Dashboard - Options Trading Analysis
====================================================
Dashboard interactivo para visualizar resultados del backtest,
performance por ticker, early closures, y parámetros adaptativos.

Para ejecutar:
    streamlit run scripts/dashboard/app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Configuración de la página
st.set_page_config(
    page_title="Options Backtesting Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Importar componentes
from scripts.dashboard.components import (
    overview,
    performance,
    early_closures,
    ml_dataset,
    parameters
)

def load_data():
    """Carga todos los datos necesarios"""
    data_dir = root_dir / 'data' / 'analysis'
    viz_dir = root_dir / 'scripts' / 'visualizations'
    
    # Verificar que existan los archivos
    ml_dataset_path = data_dir / 'ml_dataset_10_tickers.csv'
    params_path = data_dir / 'ticker_parameters_recommendations.csv'
    
    if not ml_dataset_path.exists():
        st.error(f"❌ No se encontró el archivo: {ml_dataset_path}")
        st.info("🔍 Ejecuta primero: `python scripts/backtest/test_backtest_10_tickers.py`")
        return None, None, None
    
    # Cargar datasets
    df = pd.read_csv(ml_dataset_path)
    
    # Cargar parámetros si existe
    params_df = None
    if params_path.exists():
        params_df = pd.read_csv(params_path)
    
    # Rutas de las imágenes
    images = {
        'analysis_results': viz_dir / 'analysis_results.png',
        'early_closures': viz_dir / 'early_closures_analysis.png',
        'scoring_comparison': viz_dir / 'scoring_optimization_comparison.png',
        'ticker_parameters': viz_dir / 'ticker_parameters_analysis.png'
    }
    
    return df, params_df, images

def main():
    """Función principal del dashboard"""
    
    # Header
    st.title("📊 Options Trading Backtesting Dashboard")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("🔄 Cargando datos..."):
        df, params_df, images = load_data()
    
    if df is None:
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        st.markdown("### 📋 Información del Backtest")
        
        # Métricas generales
        total_trades = len(df)
        winning_trades = len(df[df['pnl'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = df['pnl'].sum()
        
        st.metric("Total Trades", total_trades)
        st.metric("Win Rate", f"{win_rate:.1f}%")
        st.metric("Total PnL", f"${total_pnl:,.2f}")
        
        st.markdown("---")
        st.markdown("### 🎯 Navegación")
        st.markdown("""
        - **Overview**: Resumen general
        - **Performance**: Por ticker
        - **Early Closures**: Análisis de cierres
        - **ML Dataset**: Datos completos
        - **Parameters**: Recomendaciones
        """)
        
        st.markdown("---")
        st.markdown("### 🔧 Herramientas")
        st.markdown("""
        **Pipeline Completo:**
        1. `test_backtest_10_tickers.py`
        2. `analyze_backtest_results.py`
        3. `analyze_early_closures.py`
        4. `compare_scoring_optimization.py`
        5. `analyze_ticker_parameters.py`
        """)
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "🎯 Performance por Ticker",
        "⏱️ Early Closures",
        "📊 ML Dataset",
        "⚙️ Parámetros Adaptativos"
    ])
    
    with tab1:
        overview.render(df, images)
    
    with tab2:
        performance.render(df, images)
    
    with tab3:
        early_closures.render(df, images)
    
    with tab4:
        ml_dataset.render(df)
    
    with tab5:
        parameters.render(params_df, images)

if __name__ == "__main__":
    main()
