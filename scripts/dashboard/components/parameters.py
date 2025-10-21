"""
Parameters Tab - Recomendaciones de parámetros adaptativos por ticker
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render(params_df, images):
    """
    Renderiza el tab de Parámetros Adaptativos
    
    Args:
        params_df: DataFrame con recomendaciones de parámetros por ticker
        images: Dict con rutas a las imágenes generadas
    """
    st.header("⚙️ Parámetros Adaptativos por Ticker")
    
    if params_df is None or params_df.empty:
        st.warning("⚠️ No se encontraron recomendaciones de parámetros")
        st.info("🔍 Ejecuta: `python scripts/backtest/analyze_ticker_parameters.py`")
        return
    
    st.markdown("""
    Los parámetros adaptativos ajustan automáticamente los objetivos de profit, stop loss, 
    y DTE según la volatilidad histórica de cada ticker. Esto optimiza la gestión de riesgo 
    y mejora la consistencia de resultados.
    """)
    
    st.markdown("---")
    
    # Resumen general
    st.subheader("📊 Resumen de Clasificaciones")
    
    if 'volatility_category' in params_df.columns:
        vol_counts = params_df['volatility_category'].value_counts()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            high_vol = vol_counts.get('High Volatility', 0)
            st.metric(
                label="🔴 Alta Volatilidad",
                value=high_vol,
                delta="Requiere ajustes agresivos"
            )
        
        with col2:
            med_vol = vol_counts.get('Medium Volatility', 0)
            st.metric(
                label="🟡 Volatilidad Media",
                value=med_vol,
                delta="Parámetros balanceados"
            )
        
        with col3:
            low_vol = vol_counts.get('Low Volatility', 0)
            st.metric(
                label="🟢 Baja Volatilidad",
                value=low_vol,
                delta="Parámetros conservadores"
            )
    
    st.markdown("---")
    
    # Tabla de recomendaciones
    st.subheader("📋 Recomendaciones por Ticker")
    
    # Mostrar dataframe completo
    display_df = params_df.copy()
    
    # Formatear columnas numéricas si existen
    if 'profit_target' in display_df.columns:
        display_df['profit_target'] = display_df['profit_target'].apply(lambda x: f"{x:.1f}%")
    if 'stop_loss' in display_df.columns:
        display_df['stop_loss'] = display_df['stop_loss'].apply(lambda x: f"{x:.1f}%")
    if 'avg_volatility' in display_df.columns:
        display_df['avg_volatility'] = display_df['avg_volatility'].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Definir colores fuera de los bloques para usarlos en múltiples gráficos
    color_map = {
        'High Volatility': '#ef553b',
        'Medium Volatility': '#ffa15a',
        'Low Volatility': '#00cc96'
    }
    colors = params_df['volatility_category'].map(color_map) if 'volatility_category' in params_df.columns else '#636efa'
    
    # Gráficos comparativos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Profit Targets por Ticker")
        
        if 'ticker' in params_df.columns and 'profit_target' in params_df.columns:
            # Extraer valores numéricos
            params_df['profit_target_num'] = params_df['profit_target'].astype(float)
            
            fig_profit = go.Figure()
            
            fig_profit.add_trace(go.Bar(
                x=params_df['ticker'],
                y=params_df['profit_target_num'],
                marker_color=colors,
                text=params_df['profit_target_num'].apply(lambda x: f'{x:.1f}%'),
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Profit Target: %{y:.1f}%<extra></extra>'
            ))
            
            fig_profit.update_layout(
                xaxis_title="Ticker",
                yaxis_title="Profit Target (%)",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_profit, use_container_width=True)
    
    with col2:
        st.subheader("🛡️ Stop Loss por Ticker")
        
        if 'ticker' in params_df.columns and 'stop_loss' in params_df.columns:
            # Extraer valores numéricos
            params_df['stop_loss_num'] = params_df['stop_loss'].astype(float)
            
            fig_sl = go.Figure()
            
            fig_sl.add_trace(go.Bar(
                x=params_df['ticker'],
                y=params_df['stop_loss_num'],
                marker_color=colors,
                text=params_df['stop_loss_num'].apply(lambda x: f'{x:.1f}%'),
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Stop Loss: %{y:.1f}%<extra></extra>'
            ))
            
            fig_sl.update_layout(
                xaxis_title="Ticker",
                yaxis_title="Stop Loss (%)",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_sl, use_container_width=True)
    
    st.markdown("---")
    
    # DTE Ranges
    if 'dte_min' in params_df.columns and 'dte_max' in params_df.columns:
        st.subheader("📅 DTE (Days to Expiration) Ranges")
        
        fig_dte = go.Figure()
        
        for idx, row in params_df.iterrows():
            fig_dte.add_trace(go.Bar(
                name=row['ticker'],
                x=[row['ticker']],
                y=[row['dte_max'] - row['dte_min']],
                base=row['dte_min'],
                marker_color=colors.iloc[idx] if isinstance(colors, pd.Series) else colors,
                hovertemplate=f"<b>{row['ticker']}</b><br>DTE Range: {row['dte_min']}-{row['dte_max']} days<extra></extra>"
            ))
        
        fig_dte.update_layout(
            title="Rangos de DTE Recomendados",
            xaxis_title="Ticker",
            yaxis_title="Days to Expiration",
            showlegend=False,
            height=400,
            barmode='overlay'
        )
        
        st.plotly_chart(fig_dte, use_container_width=True)
    
    st.markdown("---")
    
    # Volatilidad vs Parámetros
    if 'avg_volatility' in params_df.columns:
        st.subheader("📈 Relación Volatilidad vs Parámetros")
        
        # Extraer valores numéricos de volatilidad
        params_df['volatility_num'] = params_df['avg_volatility'].astype(float)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Scatter: Volatility vs Profit Target
            fig_scatter1 = go.Figure()
            
            fig_scatter1.add_trace(go.Scatter(
                x=params_df['volatility_num'],
                y=params_df['profit_target_num'],
                mode='markers+text',
                marker=dict(
                    size=15,
                    color=params_df['volatility_num'],
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Volatility (%)")
                ),
                text=params_df['ticker'],
                textposition='top center',
                hovertemplate='<b>%{text}</b><br>Volatility: %{x:.2f}%<br>Profit Target: %{y:.1f}%<extra></extra>'
            ))
            
            fig_scatter1.update_layout(
                title="Volatilidad vs Profit Target",
                xaxis_title="Volatilidad Promedio (%)",
                yaxis_title="Profit Target (%)",
                height=400
            )
            
            st.plotly_chart(fig_scatter1, use_container_width=True)
        
        with col2:
            # Scatter: Volatility vs Stop Loss
            fig_scatter2 = go.Figure()
            
            fig_scatter2.add_trace(go.Scatter(
                x=params_df['volatility_num'],
                y=params_df['stop_loss_num'],
                mode='markers+text',
                marker=dict(
                    size=15,
                    color=params_df['volatility_num'],
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Volatility (%)")
                ),
                text=params_df['ticker'],
                textposition='top center',
                hovertemplate='<b>%{text}</b><br>Volatility: %{x:.2f}%<br>Stop Loss: %{y:.1f}%<extra></extra>'
            ))
            
            fig_scatter2.update_layout(
                title="Volatilidad vs Stop Loss",
                xaxis_title="Volatilidad Promedio (%)",
                yaxis_title="Stop Loss (%)",
                height=400
            )
            
            st.plotly_chart(fig_scatter2, use_container_width=True)
    
    st.markdown("---")
    
    # Mostrar imagen de análisis si existe
    if images['ticker_parameters'].exists():
        st.subheader("📊 Análisis Completo de Parámetros")
        st.image(str(images['ticker_parameters']), use_container_width=True)
    else:
        st.warning("⚠️ Imagen de análisis no encontrada")
    
    # Explicaciones
    with st.expander("💡 ¿Cómo se calculan estos parámetros?"):
        st.markdown("""
        ### Metodología de Parámetros Adaptativos
        
        Los parámetros se ajustan basándose en la volatilidad histórica de cada ticker:
        
        **1. Clasificación de Volatilidad:**
        - **Alta (>2.5%)**: Tickers como TSLA, NVDA con movimientos grandes
        - **Media (1.5-2.5%)**: Tickers moderados
        - **Baja (<1.5%)**: Tickers estables como SPY, QQQ
        
        **2. Ajustes de Profit Target:**
        - Alta volatilidad: 25-35% (mayor potencial de ganancia)
        - Media volatilidad: 20-30% (balance)
        - Baja volatilidad: 15-25% (objetivos conservadores)
        
        **3. Ajustes de Stop Loss:**
        - Alta volatilidad: 175-200% (mayor tolerancia a movimientos)
        - Media volatilidad: 150-175% (balance)
        - Baja volatilidad: 150% (protección estricta)
        
        **4. DTE Ranges:**
        - Basados en el ciclo de expiración óptimo para cada ticker
        - Generalmente 42-60 días para maximizar theta decay
        
        **Beneficios:**
        - ✅ Reduce riesgo en tickers volátiles
        - ✅ Maximiza oportunidades en tickers estables
        - ✅ Mejora consistencia de resultados
        - ✅ Adaptación automática a condiciones del mercado
        """)
    
    # Recomendaciones de uso
    with st.expander("🔧 ¿Cómo usar estas recomendaciones?"):
        st.markdown("""
        ### Implementación en el Backtest
        
        Estos parámetros pueden ser utilizados en el archivo de configuración adaptativa:
        
        ```python
        # scripts/strategies/adaptive_config.py
        
        ADAPTIVE_PARAMS = {
            'TSLA': {
                'profit_target': 0.35,  # 35%
                'stop_loss': 2.00,      # 200%
                'dte_min': 42,
                'dte_max': 60
            },
            # ... otros tickers
        }
        ```
        
        **Pasos para aplicar:**
        1. Copia las recomendaciones de la tabla
        2. Actualiza `adaptive_config.py`
        3. Re-ejecuta el backtest
        4. Compara resultados con parámetros fijos
        
        **Monitoreo:**
        - Revisa estos parámetros mensualmente
        - Ajusta según cambios en volatilidad del mercado
        - Documenta cambios y sus efectos
        """)
