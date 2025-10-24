# visualization/plotter.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from constants import RSI_OVERBOUGHT, RSI_OVERSOLD, STOCH_OVERBOUGHT, STOCH_OVERSOLD, MA_CONFIG

class PlotlyPlotter:

    def plot_price_chart(self, data: pd.DataFrame, ticker: str) -> go.Figure:
        """
        Grafik BARU: Hanya menampilkan Harga, MA, BB, Pola, dan Volume.
        """
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.01, row_heights=[0.8, 0.2]
        )

        # --- GRAFIK HARGA (ROW 1) ---
        fig.add_trace(go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            name='Harga', increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
            showlegend=False
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MA_S'], name='MA Pendek', line=dict(color='#ffe082', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MA_M'], name='MA Menengah', line=dict(color='#4fc3f7', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MA_L'], name='MA Panjang', line=dict(color='#ab47bc', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name='BB Upper', line=dict(color='#a9a9a9', width=1, dash='dot'), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name='BB Lower', line=dict(color='#a9a9a9', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)', mode='lines', showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=[data.index[-1]], y=[None], name='Bollinger Bands', line=dict(color='#a9a9a9', width=1, dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=data.index[data['DB_Signal'] == True], y=data['Low'][data['DB_Signal'] == True], name='Double Bottom (Beli)', mode='markers', 
            marker=dict(symbol='triangle-up', size=10, color='lime', line=dict(width=1, color='DarkGreen'))
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=data.index[data['DT_Signal'] == True], y=data['High'][data['DT_Signal'] == True], name='Double Top (Jual)', mode='markers', 
            marker=dict(symbol='triangle-down', size=10, color='red', line=dict(width=1, color='DarkRed'))
        ), row=1, col=1)

        # --- GRAFIK VOLUME (ROW 2) ---
        volume_colors = np.where(data['Close'] >= data['Open'], '#26a69a', '#ef5350')
        fig.add_trace(go.Bar(
            x=data.index, y=data['Volume'], name='Volume', 
            marker_color=volume_colors, marker_opacity=0.6, showlegend=False
        ), row=2, col=1)
        
        # --- LAYOUT UMUM ---
        fig.update_layout(
            title=f'Grafik Harga & Volume ({ticker})',
            xaxis_rangeslider_visible=False, 
            height=600, 
            hovermode='x unified',
            template="plotly_dark", 
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10), itemwidth=30),
            # ==========================================================
            # UPGRADE V2.1: Aktifkan Mode Pan (Geser) secara default
            # ==========================================================
            dragmode='pan' 
        )
        
        fig.update_xaxes(showgrid=False, zeroline=False, row=1, col=1)
        fig.update_xaxes(showgrid=True, zeroline=False, showticklabels=True, row=2, col=1) 
        fig.update_yaxes(title_text='Harga & MA', row=1, col=1)
        fig.update_yaxes(title_text='Volume', row=2, col=1)
        
        return fig

    def plot_indicators_chart(self, data: pd.DataFrame) -> go.Figure:
        """
        Grafik BARU: Hanya menampilkan RSI, MACD, dan Stochastic.
        """
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            vertical_spacing=0.02, row_heights=[0.33, 0.33, 0.34]
        )

        # --- GRAFIK RSI (ROW 1) ---
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#ff9800')), row=1, col=1)
        fig.add_hline(y=RSI_OVERBOUGHT, line_width=1, line_dash="dash", line_color='red', row=1, col=1, showlegend=False)
        fig.add_hline(y=RSI_OVERSOLD, line_width=1, line_dash="dash", line_color='green', row=1, col=1, showlegend=False)

        # --- GRAFIK MACD (ROW 2) ---
        colors = np.where(data["MACD_Hist"] >= 0, '#26a69a', '#ef5350')
        fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], name='Histogram', marker_color=colors, opacity=0.6, showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD Line', line=dict(color='#2196f3')), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal Line', line=dict(color='#ffc107', dash='dot')), row=2, col=1)

        # --- GRAFIK STOCHASTIC (ROW 3) ---
        fig.add_trace(go.Scatter(x=data.index, y=data['%K'], name='%K', line=dict(color='#00e676')), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['%D'], name='%D', line=dict(color='#ff1744', dash='dot')), row=3, col=1)
        fig.add_hline(y=STOCH_OVERBOUGHT, line_width=1, line_dash="dash", line_color='red', row=3, col=1, showlegend=False)
        fig.add_hline(y=STOCH_OVERSOLD, line_width=1, line_dash="dash", line_color='green', row=3, col=1, showlegend=False)

        # --- LAYOUT UMUM ---
        fig.update_layout(
            title='Indikator Momentum',
            height=500, 
            hovermode='x unified',
            template="plotly_dark", 
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10), itemwidth=30),
            # ==========================================================
            # UPGRADE V2.1: Aktifkan Mode Pan (Geser) secara default
            # ==========================================================
            dragmode='pan'
        )
        
        fig.update_xaxes(showgrid=False, zeroline=False, row=1, col=1)
        fig.update_xaxes(showgrid=False, zeroline=False, row=2, col=1)
        fig.update_xaxes(showgrid=True, zeroline=False, showticklabels=True, row=3, col=1) 
        fig.update_yaxes(title_text='RSI', range=[0, 100], row=1, col=1)
        fig.update_yaxes(title_text='MACD', row=2, col=1)
        fig.update_yaxes(title_text='Stoch', range=[0, 100], row=3, col=1)
        
        return fig
