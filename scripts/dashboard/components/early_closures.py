"""
Early Closures Tab - Análisis de cierres anticipados vs expiración
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render(df, images):
    """
    Renderiza el tab de Early Closures Analysis
    
    Args:
        df: DataFrame con los datos del backtest
        images: Dict con rutas a las imágenes generadas
    """
    st.header("⏱️ Early Closures Analysis")
    
    # Verificar columna correcta (status en lugar de exit_reason)
    status_col = 'status' if 'status' in df.columns else 'exit_reason' if 'exit_reason' in df.columns else None
    
    if status_col is None:
        st.warning("⚠️ No se encontró columna 'status' o 'exit_reason'. Análisis no disponible.")
        return
    
    # Clasificar por tipo de cierre
    df['closure_type'] = df[status_col].apply(
        lambda x: 'Early Closure' if 'closed_profit' in str(x).lower() or 'closed_loss' in str(x).lower() 
        else 'Expiration'
    )
    
    # Métricas generales
    total_trades = len(df)
    early_closures = len(df[df['closure_type'] == 'Early Closure'])
    expirations = len(df[df['closure_type'] == 'Expiration'])
    early_pct = (early_closures / total_trades * 100) if total_trades > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Trades",
            value=total_trades
        )
    
    with col2:
        st.metric(
            label="Early Closures",
            value=early_closures,
            delta=f"{early_pct:.1f}%"
        )
    
    with col3:
        st.metric(
            label="Expirations",
            value=expirations,
            delta=f"{100-early_pct:.1f}%"
        )
    
    with col4:
        # Ratio de early vs expiration
        ratio = early_closures / expirations if expirations > 0 else 0
        st.metric(
            label="Early/Exp Ratio",
            value=f"{ratio:.2f}",
            delta="Mayor rotación" if ratio > 1 else None
        )
    
    st.markdown("---")
    
    # Comparación de Performance
    st.subheader("📊 Comparación de Performance")
    
    comparison = df.groupby('closure_type').agg({
        'pnl': ['sum', 'mean', 'std', 'count']
    }).reset_index()
    
    comparison.columns = ['Closure Type', 'Total PnL', 'Avg PnL', 'Std PnL', 'Count']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # PnL por tipo de cierre
        fig_bar = go.Figure()
        
        colors = ['#00cc96', '#636efa']
        
        fig_bar.add_trace(go.Bar(
            x=comparison['Closure Type'],
            y=comparison['Total PnL'],
            marker_color=colors,
            text=comparison['Total PnL'].apply(lambda x: f'${x:,.0f}'),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Total PnL: $%{y:,.2f}<br>Trades: %{customdata}<extra></extra>',
            customdata=comparison['Count']
        ))
        
        fig_bar.update_layout(
            title="Total PnL por Tipo de Cierre",
            xaxis_title="Tipo de Cierre",
            yaxis_title="Total PnL ($)",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Distribución pie chart
        fig_pie = go.Figure()
        
        fig_pie.add_trace(go.Pie(
            labels=comparison['Closure Type'],
            values=comparison['Count'],
            marker=dict(colors=colors),
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
            textinfo='label+percent'
        ))
        
        fig_pie.update_layout(
            title="Distribución de Tipos de Cierre",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Tabla comparativa
    st.subheader("📋 Métricas Comparativas")
    
    display_comparison = comparison.copy()
    display_comparison['Total PnL'] = display_comparison['Total PnL'].apply(lambda x: f"${x:,.2f}")
    display_comparison['Avg PnL'] = display_comparison['Avg PnL'].apply(lambda x: f"${x:.2f}")
    display_comparison['Std PnL'] = display_comparison['Std PnL'].apply(lambda x: f"${x:.2f}")
    display_comparison['Count'] = display_comparison['Count'].astype(int)
    
    st.dataframe(
        display_comparison,
        use_container_width=True,
        hide_index=True
    )
    
    # Análisis temporal
    st.markdown("---")
    st.subheader("⏰ Análisis Temporal")
    
    if 'days_held' in df.columns or ('entry_date' in df.columns and 'exit_date' in df.columns):
        # Calcular días si no existe
        if 'days_held' not in df.columns:
            df['entry_date'] = pd.to_datetime(df['entry_date'])
            df['exit_date'] = pd.to_datetime(df['exit_date'])
            df['days_held'] = (df['exit_date'] - df['entry_date']).dt.days
        
        # Box plot por tipo de cierre
        fig_box = go.Figure()
        
        for closure_type in df['closure_type'].unique():
            subset = df[df['closure_type'] == closure_type]
            
            fig_box.add_trace(go.Box(
                y=subset['days_held'],
                name=closure_type,
                boxmean='sd',
                hovertemplate='<b>%{fullData.name}</b><br>Days Held: %{y}<extra></extra>'
            ))
        
        fig_box.update_layout(
            title="Distribución de Días Mantenidos por Tipo de Cierre",
            yaxis_title="Días Mantenidos",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig_box, use_container_width=True)
        
        # Métricas de tiempo
        col1, col2, col3 = st.columns(3)
        
        early_days = df[df['closure_type'] == 'Early Closure']['days_held'].mean()
        exp_days = df[df['closure_type'] == 'Expiration']['days_held'].mean()
        
        with col1:
            st.metric(
                label="Avg Days (Early)",
                value=f"{early_days:.1f}",
                delta=f"{early_days - exp_days:.1f} vs Exp"
            )
        
        with col2:
            st.metric(
                label="Avg Days (Expiration)",
                value=f"{exp_days:.1f}"
            )
        
        with col3:
            # Capital turnover advantage
            if exp_days > 0:
                turnover_advantage = (exp_days / early_days) if early_days > 0 else 1
                st.metric(
                    label="Turnover Advantage",
                    value=f"{turnover_advantage:.2f}x",
                    delta="Faster capital rotation" if turnover_advantage > 1 else None
                )
    else:
        st.info("ℹ️ No hay información de días mantenidos disponible")
    
    st.markdown("---")
    
    # Timeline de cierres
    st.subheader("📅 Timeline de Cierres")
    
    if 'exit_date' in df.columns:
        df['exit_date'] = pd.to_datetime(df['exit_date'])
        timeline_df = df.groupby([df['exit_date'].dt.date, 'closure_type']).size().reset_index()
        timeline_df.columns = ['Date', 'Closure Type', 'Count']
        
        fig_timeline = px.bar(
            timeline_df,
            x='Date',
            y='Count',
            color='Closure Type',
            title="Frecuencia de Cierres a lo Largo del Tiempo",
            color_discrete_map={'Early Closure': '#00cc96', 'Expiration': '#636efa'},
            barmode='stack'
        )
        
        fig_timeline.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Número de Trades",
            height=400
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.markdown("---")
    
    # Mostrar imagen de análisis si existe
    if images['early_closures'].exists():
        st.subheader("📈 Análisis Detallado de Early Closures")
        st.image(str(images['early_closures']), use_container_width=True)
    else:
        st.warning("⚠️ Imagen de análisis no encontrada. Ejecuta `analyze_early_closures.py`")
    
    # Insights
    with st.expander("💡 Insights"):
        early_total = df[df['closure_type'] == 'Early Closure']['pnl'].sum()
        exp_total = df[df['closure_type'] == 'Expiration']['pnl'].sum()
        
        st.write(f"**PnL Total (Early Closures):** ${early_total:,.2f}")
        st.write(f"**PnL Total (Expirations):** ${exp_total:,.2f}")
        
        if early_days and exp_days:
            st.write(f"**Ventaja de Tiempo:** Los early closures liberan capital {turnover_advantage:.1f}x más rápido")
            st.write(f"**Rotación de Capital:** Early closures permiten más oportunidades de trading")
