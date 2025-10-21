"""
Performance Tab - Análisis detallado por ticker
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render(df, images):
    """
    Renderiza el tab de Performance por Ticker
    
    Args:
        df: DataFrame con los datos del backtest
        images: Dict con rutas a las imágenes generadas
    """
    st.header("🎯 Performance por Ticker")
    
    if 'ticker' not in df.columns:
        st.error("❌ La columna 'ticker' no está disponible en el dataset")
        return
    
    # Calcular métricas por ticker
    ticker_stats = df.groupby('ticker').agg({
        'pnl': ['sum', 'mean', 'std', 'count'],
        'premium_collected': 'sum' if 'premium_collected' in df.columns else 'mean'
    }).reset_index()
    
    ticker_stats.columns = ['Ticker', 'Total PnL', 'Avg PnL', 'Std PnL', 'Trades', 'Total Premium']
    
    # Calcular win rate por ticker
    win_rates = df.groupby('ticker').apply(
        lambda x: (len(x[x['pnl'] > 0]) / len(x) * 100) if len(x) > 0 else 0
    ).reset_index()
    win_rates.columns = ['Ticker', 'Win Rate (%)']
    
    # Merge
    ticker_stats = ticker_stats.merge(win_rates, on='Ticker')
    ticker_stats = ticker_stats.sort_values('Total PnL', ascending=False)
    
    # Métricas destacadas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_ticker = ticker_stats.iloc[0]
        st.metric(
            label="🥇 Mejor Ticker",
            value=best_ticker['Ticker'],
            delta=f"${best_ticker['Total PnL']:,.2f}"
        )
    
    with col2:
        most_traded = ticker_stats.loc[ticker_stats['Trades'].idxmax()]
        st.metric(
            label="📊 Más Operado",
            value=most_traded['Ticker'],
            delta=f"{int(most_traded['Trades'])} trades"
        )
    
    with col3:
        best_wr = ticker_stats.loc[ticker_stats['Win Rate (%)'].idxmax()]
        st.metric(
            label="🎯 Mejor Win Rate",
            value=best_wr['Ticker'],
            delta=f"{best_wr['Win Rate (%)']:.1f}%"
        )
    
    st.markdown("---")
    
    # Filtros
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_tickers = st.multiselect(
            "Filtrar por Ticker:",
            options=sorted(df['ticker'].unique().tolist()),
            default=sorted(df['ticker'].unique().tolist())
        )
    
    with col2:
        sort_by = st.selectbox(
            "Ordenar por:",
            ['Total PnL', 'Win Rate (%)', 'Trades', 'Avg PnL']
        )
    
    # Filtrar y ordenar
    filtered_stats = ticker_stats[ticker_stats['Ticker'].isin(selected_tickers)]
    filtered_stats = filtered_stats.sort_values(sort_by, ascending=False)
    
    # Tabla de ranking
    st.subheader("📊 Ranking de Tickers")
    
    # Formatear tabla para display
    display_df = filtered_stats.copy()
    display_df['Total PnL'] = display_df['Total PnL'].apply(lambda x: f"${x:,.2f}")
    display_df['Avg PnL'] = display_df['Avg PnL'].apply(lambda x: f"${x:.2f}")
    display_df['Win Rate (%)'] = display_df['Win Rate (%)'].apply(lambda x: f"{x:.1f}%")
    display_df['Trades'] = display_df['Trades'].astype(int)
    
    st.dataframe(
        display_df[['Ticker', 'Total PnL', 'Win Rate (%)', 'Trades', 'Avg PnL']],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Total PnL por Ticker")
        
        fig_bar = go.Figure()
        
        # Colores según PnL positivo/negativo
        colors = ['#00cc96' if x > 0 else '#ef553b' for x in filtered_stats['Total PnL']]
        
        fig_bar.add_trace(go.Bar(
            x=filtered_stats['Ticker'],
            y=filtered_stats['Total PnL'],
            marker_color=colors,
            text=filtered_stats['Total PnL'].apply(lambda x: f'${x:,.0f}'),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>PnL: $%{y:,.2f}<extra></extra>'
        ))
        
        fig_bar.update_layout(
            xaxis_title="Ticker",
            yaxis_title="Total PnL ($)",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Win Rate por Ticker")
        
        fig_wr = go.Figure()
        
        fig_wr.add_trace(go.Bar(
            x=filtered_stats['Ticker'],
            y=filtered_stats['Win Rate (%)'],
            marker_color='#636efa',
            text=filtered_stats['Win Rate (%)'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>'
        ))
        
        # Línea de referencia en 50%
        fig_wr.add_hline(
            y=50,
            line_dash="dash",
            line_color="gray",
            annotation_text="50%",
            annotation_position="right"
        )
        
        fig_wr.update_layout(
            xaxis_title="Ticker",
            yaxis_title="Win Rate (%)",
            showlegend=False,
            height=400,
            yaxis_range=[0, 110]
        )
        
        st.plotly_chart(fig_wr, use_container_width=True)
    
    st.markdown("---")
    
    # Scatter plot: PnL vs Trades
    st.subheader("📈 Relación PnL vs Número de Trades")
    
    fig_scatter = go.Figure()
    
    fig_scatter.add_trace(go.Scatter(
        x=filtered_stats['Trades'],
        y=filtered_stats['Total PnL'],
        mode='markers+text',
        marker=dict(
            size=filtered_stats['Win Rate (%)'],
            color=filtered_stats['Win Rate (%)'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Win Rate (%)"),
            line=dict(width=1, color='white')
        ),
        text=filtered_stats['Ticker'],
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>Trades: %{x}<br>PnL: $%{y:,.2f}<extra></extra>'
    ))
    
    fig_scatter.update_layout(
        xaxis_title="Número de Trades",
        yaxis_title="Total PnL ($)",
        height=500,
        hovermode='closest'
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.markdown("---")
    
    # Detalle por ticker individual
    st.subheader("🔍 Análisis Individual por Ticker")
    
    selected_ticker = st.selectbox(
        "Selecciona un ticker para análisis detallado:",
        options=sorted(df['ticker'].unique().tolist())
    )
    
    ticker_data = df[df['ticker'] == selected_ticker].copy()
    ticker_data = ticker_data.sort_values('entry_date')
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_pnl = ticker_data['pnl'].sum()
    avg_pnl = ticker_data['pnl'].mean()
    win_rate = (len(ticker_data[ticker_data['pnl'] > 0]) / len(ticker_data) * 100)
    total_trades = len(ticker_data)
    
    with col1:
        st.metric("Total PnL", f"${total_pnl:,.2f}")
    with col2:
        st.metric("Avg PnL", f"${avg_pnl:.2f}")
    with col3:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col4:
        st.metric("Trades", total_trades)
    
    # Equity curve por ticker
    ticker_data['cumulative_pnl'] = ticker_data['pnl'].cumsum()
    
    fig_equity = go.Figure()
    
    fig_equity.add_trace(go.Scatter(
        x=ticker_data['entry_date'],
        y=ticker_data['cumulative_pnl'],
        mode='lines+markers',
        name=selected_ticker,
        line=dict(color='#00cc96', width=2),
        marker=dict(size=6),
        hovertemplate='<b>Date</b>: %{x}<br><b>Cumulative PnL</b>: $%{y:,.2f}<extra></extra>'
    ))
    
    fig_equity.update_layout(
        title=f"Equity Curve - {selected_ticker}",
        xaxis_title="Fecha",
        yaxis_title="PnL Acumulado ($)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_equity, use_container_width=True)
    
    # Mostrar imagen de parámetros si existe
    if images['ticker_parameters'].exists():
        st.markdown("---")
        st.subheader("⚙️ Análisis de Parámetros por Ticker")
        st.image(str(images['ticker_parameters']), use_container_width=True)
