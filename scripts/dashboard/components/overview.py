"""
Overview Tab - Métricas generales y visualizaciones principales
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

def render(df, images):
    """
    Renderiza el tab de Overview con métricas principales
    
    Args:
        df: DataFrame con los datos del backtest
        images: Dict con rutas a las imágenes generadas
    """
    st.header("📈 Overview - Resumen General del Backtest")
    
    # Métricas principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_trades = len(df)
    winning_trades = len(df[df['pnl'] > 0])
    losing_trades = len(df[df['pnl'] < 0])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    total_pnl = df['pnl'].sum()
    avg_pnl = df['pnl'].mean()
    
    # Calcular ROI (asumiendo capital inicial de $20,000)
    capital = 20000
    roi = (total_pnl / capital * 100)
    
    with col1:
        st.metric(
            label="Total Trades",
            value=total_trades,
            delta=f"{winning_trades} wins"
        )
    
    with col2:
        st.metric(
            label="Win Rate",
            value=f"{win_rate:.1f}%",
            delta="Perfect!" if win_rate == 100 else None
        )
    
    with col3:
        st.metric(
            label="Total PnL",
            value=f"${total_pnl:,.2f}",
            delta=f"Avg: ${avg_pnl:.2f}"
        )
    
    with col4:
        st.metric(
            label="ROI",
            value=f"{roi:.1f}%",
            delta=f"On ${capital:,}"
        )
    
    with col5:
        # Calcular Sharpe Ratio si es posible
        if 'pnl' in df.columns and len(df) > 1:
            returns = df['pnl'] / capital
            sharpe = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() > 0 else 0
            st.metric(
                label="Sharpe Ratio",
                value=f"{sharpe:.2f}",
                delta="Excelente" if sharpe > 3 else "Bueno" if sharpe > 1 else None
            )
        else:
            st.metric(label="Sharpe Ratio", value="N/A")
    
    st.markdown("---")
    
    # Equity Curve
    st.subheader("💰 Equity Curve")
    
    # Calcular equity acumulada
    df_sorted = df.sort_values('entry_date')
    df_sorted['cumulative_pnl'] = df_sorted['pnl'].cumsum()
    df_sorted['equity'] = capital + df_sorted['cumulative_pnl']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_sorted['entry_date'],
        y=df_sorted['equity'],
        mode='lines+markers',
        name='Equity',
        line=dict(color='#00cc96', width=2),
        marker=dict(size=6),
        hovertemplate='<b>Date</b>: %{x}<br><b>Equity</b>: $%{y:,.2f}<extra></extra>'
    ))
    
    # Línea de capital inicial
    fig.add_hline(
        y=capital,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Capital Inicial: ${capital:,}",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="Evolución del Capital a lo Largo del Tiempo",
        xaxis_title="Fecha",
        yaxis_title="Equity ($)",
        hovermode='x unified',
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Distribución de PnL
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribución de PnL")
        
        fig_hist = go.Figure()
        
        fig_hist.add_trace(go.Histogram(
            x=df['pnl'],
            nbinsx=20,
            marker_color='#636efa',
            name='PnL Distribution',
            hovertemplate='<b>PnL Range</b>: %{x}<br><b>Count</b>: %{y}<extra></extra>'
        ))
        
        fig_hist.update_layout(
            title="Distribución de Resultados por Trade",
            xaxis_title="PnL ($)",
            yaxis_title="Frecuencia",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Performance por Strategy")
        
        if 'strategy' in df.columns:
            strategy_pnl = df.groupby('strategy')['pnl'].agg(['sum', 'mean', 'count']).reset_index()
            strategy_pnl.columns = ['Strategy', 'Total PnL', 'Avg PnL', 'Trades']
            strategy_pnl = strategy_pnl.sort_values('Total PnL', ascending=False)
            
            fig_bar = go.Figure()
            
            fig_bar.add_trace(go.Bar(
                x=strategy_pnl['Strategy'],
                y=strategy_pnl['Total PnL'],
                marker_color='#00cc96',
                text=strategy_pnl['Total PnL'].apply(lambda x: f'${x:,.0f}'),
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Total PnL: $%{y:,.2f}<extra></extra>'
            ))
            
            fig_bar.update_layout(
                title="PnL Total por Estrategia",
                xaxis_title="Estrategia",
                yaxis_title="Total PnL ($)",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("ℹ️ No hay información de estrategias en el dataset")
    
    st.markdown("---")
    
    # Mostrar imagen de análisis general si existe
    if images['analysis_results'].exists():
        st.subheader("📈 Análisis Detallado de Resultados")
        st.image(str(images['analysis_results']), use_container_width=True)
    else:
        st.warning("⚠️ Imagen de análisis no encontrada. Ejecuta `analyze_backtest_results.py`")
    
    # Información adicional
    with st.expander("ℹ️ Información del Dataset"):
        st.write(f"**Total de registros:** {len(df)}")
        st.write(f"**Columnas disponibles:** {', '.join(df.columns.tolist())}")
        st.write(f"**Rango de fechas:** {df['entry_date'].min()} a {df['entry_date'].max()}")
        st.write(f"**Tickers únicos:** {df['ticker'].nunique() if 'ticker' in df.columns else 'N/A'}")
