# visualization/plotter.py (V9.2 - Tambah VWAP)

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from constants import MA_SHORT_WINDOW, MA_MEDIUM_WINDOW, MA_LONG_WINDOW # Pastikan diimpor

class PlotlyPlotter:

    def plot_price_chart(self, data: pd.DataFrame, ticker_symbol: str):
        """Plots the main price chart with Candlesticks, Volume, and MAs."""
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # Candlestick chart
        fig.add_trace(go.Candlestick(x=data.index,
                                     open=data['Open'], high=data['High'],
                                     low=data['Low'], close=data['Close'],
                                     name='Candlestick'),
                      row=1, col=1)

        # Moving Averages
        ma_cols = {'MA_S': f'MA {MA_SHORT_WINDOW}', 'MA_M': f'MA {MA_MEDIUM_WINDOW}', 'MA_L': f'MA {MA_LONG_WINDOW}'}
        ma_colors = {'MA_S': 'yellow', 'MA_M': 'cyan', 'MA_L': 'magenta'}
        for col, name in ma_cols.items():
            if col in data.columns:
                fig.add_trace(go.Scatter(x=data.index, y=data[col],
                                         mode='lines', name=name,
                                         line=dict(color=ma_colors[col], width=1)),
                              row=1, col=1)

        # --- TAMBAHKAN PLOTTING VWAP (V9.2) ---
        if 'VWAP_20' in data.columns:
             fig.add_trace(go.Scatter(x=data.index, y=data['VWAP_20'],
                                      mode='lines', name='VWAP 20',
                                      line=dict(color='orange', width=1, dash='dash')),
                           row=1, col=1)
        # ------------------------------------

        # Volume chart
        fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color='lightblue'),
                      row=2, col=1)

        # Layout adjustments
        fig.update_layout(
            title=f'Grafik Harga & Volume: {ticker_symbol}',
            yaxis_title='Harga (Rp)',
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            margin=dict(l=50, r=50, t=50, b=20) # Lebih rapat
        )
        fig.update_yaxes(title_text="Volume", row=2, col=1)

        return fig

    def plot_indicators_chart(self, data: pd.DataFrame):
        """Plots RSI and MACD indicators."""
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)

        # RSI chart
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='lightgreen')), row=1, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)", row=1, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)", row=1, col=1)

        # MACD chart
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='blue')), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal Line', line=dict(color='orange')), row=2, col=1)
        # MACD Histogram
        colors = ['green' if val >= 0 else 'red' for val in data['MACD_Hist']]
        fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], name='Histogram', marker_color=colors), row=2, col=1)

        # Layout adjustments
        fig.update_layout(
            title='Indikator Momentum: RSI & MACD',
            template='plotly_dark',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
             margin=dict(l=50, r=50, t=50, b=20)
        )
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=1, col=1)
        fig.update_yaxes(title_text="MACD", row=2, col=1)

        return fig