"""
ML Dataset Tab - Explorador interactivo del dataset completo
"""

import streamlit as st
import pandas as pd
import plotly.express as px

def render(df):
    """
    Renderiza el tab de ML Dataset Viewer
    
    Args:
        df: DataFrame con los datos del backtest
    """
    st.header("📊 ML Dataset Viewer")
    
    st.markdown("""
    Este módulo te permite explorar el dataset completo utilizado para el backtest.
    Puedes filtrar, buscar, y descargar los datos en formato CSV.
    """)
    
    # Información general
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Registros", len(df))
    
    with col2:
        st.metric("Columnas", len(df.columns))
    
    with col3:
        if 'ticker' in df.columns:
            st.metric("Tickers Únicos", df['ticker'].nunique())
        else:
            st.metric("Tickers Únicos", "N/A")
    
    with col4:
        if 'strategy' in df.columns:
            st.metric("Estrategias", df['strategy'].nunique())
        else:
            st.metric("Estrategias", "N/A")
    
    st.markdown("---")
    
    # Filtros
    st.subheader("🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro por ticker
        if 'ticker' in df.columns:
            tickers = st.multiselect(
                "Filtrar por Ticker:",
                options=['ALL'] + sorted(df['ticker'].unique().tolist()),
                default=['ALL']
            )
            
            if 'ALL' not in tickers and len(tickers) > 0:
                df = df[df['ticker'].isin(tickers)]
    
    with col2:
        # Filtro por estrategia
        if 'strategy' in df.columns:
            strategies = st.multiselect(
                "Filtrar por Estrategia:",
                options=['ALL'] + sorted(df['strategy'].unique().tolist()),
                default=['ALL']
            )
            
            if 'ALL' not in strategies and len(strategies) > 0:
                df = df[df['strategy'].isin(strategies)]
    
    with col3:
        # Filtro por PnL
        pnl_filter = st.selectbox(
            "Filtrar por Resultado:",
            ['Todos', 'Solo Ganadores', 'Solo Perdedores']
        )
        
        if pnl_filter == 'Solo Ganadores':
            df = df[df['pnl'] > 0]
        elif pnl_filter == 'Solo Perdedores':
            df = df[df['pnl'] < 0]
    
    # Buscador de texto
    search_query = st.text_input("🔎 Buscar en cualquier columna:", "")
    
    if search_query:
        # Buscar en todas las columnas de tipo string
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]
    
    st.markdown("---")
    
    # Mostrar resultados
    st.subheader(f"📋 Resultados: {len(df)} registros")
    
    # Selector de columnas a mostrar
    all_columns = df.columns.tolist()
    
    default_columns = ['ticker', 'strategy', 'entry_date', 'exit_date', 'pnl', 'exit_reason']
    default_columns = [col for col in default_columns if col in all_columns]
    
    selected_columns = st.multiselect(
        "Selecciona columnas a mostrar:",
        options=all_columns,
        default=default_columns if default_columns else all_columns[:6]
    )
    
    if not selected_columns:
        st.warning("⚠️ Selecciona al menos una columna")
    else:
        # Mostrar dataframe
        st.dataframe(
            df[selected_columns],
            use_container_width=True,
            height=400
        )
    
    st.markdown("---")
    
    # Estadísticas descriptivas
    st.subheader("📈 Estadísticas Descriptivas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Estadísticas numéricas
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if numeric_cols:
            selected_stat_col = st.selectbox(
                "Selecciona columna numérica:",
                options=numeric_cols
            )
            
            stats_df = pd.DataFrame({
                'Estadística': ['Count', 'Mean', 'Std', 'Min', '25%', '50%', '75%', 'Max'],
                'Valor': [
                    len(df[selected_stat_col]),
                    df[selected_stat_col].mean(),
                    df[selected_stat_col].std(),
                    df[selected_stat_col].min(),
                    df[selected_stat_col].quantile(0.25),
                    df[selected_stat_col].quantile(0.50),
                    df[selected_stat_col].quantile(0.75),
                    df[selected_stat_col].max()
                ]
            })
            
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
    
    with col2:
        # Histograma
        if numeric_cols and selected_stat_col:
            fig_hist = px.histogram(
                df,
                x=selected_stat_col,
                nbins=30,
                title=f"Distribución de {selected_stat_col}",
                color_discrete_sequence=['#636efa']
            )
            
            fig_hist.update_layout(
                xaxis_title=selected_stat_col,
                yaxis_title="Frecuencia",
                showlegend=False,
                height=350
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
    
    st.markdown("---")
    
    # Análisis de correlación
    if len(numeric_cols) > 1:
        st.subheader("🔗 Matriz de Correlación")
        
        # Calcular correlaciones
        corr_matrix = df[numeric_cols].corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            text_auto='.2f',
            aspect='auto',
            color_continuous_scale='RdBu_r',
            title="Correlaciones entre Variables Numéricas"
        )
        
        fig_corr.update_layout(
            height=500
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
    
    st.markdown("---")
    
    # Descarga de datos
    st.subheader("⬇️ Descargar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV completo
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV Filtrado",
            data=csv,
            file_name="backtest_filtered_data.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # CSV solo columnas seleccionadas
        if selected_columns:
            csv_selected = df[selected_columns].to_csv(index=False)
            st.download_button(
                label="📥 Descargar Columnas Seleccionadas",
                data=csv_selected,
                file_name="backtest_selected_columns.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Información del dataset
    with st.expander("ℹ️ Información del Dataset"):
        st.write("**Columnas disponibles:**")
        
        for col in all_columns:
            dtype = df[col].dtype
            unique = df[col].nunique()
            nulls = df[col].isnull().sum()
            
            st.write(f"- `{col}` ({dtype}) - {unique} valores únicos - {nulls} nulos")
