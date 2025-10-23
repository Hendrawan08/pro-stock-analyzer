# analysis/backtester.py
import pandas as pd
import numpy as np
from constants import COMMISSION, RSI_OVERSOLD, RSI_OVERBOUGHT # <-- Kita butuh konstanta RSI

class Backtester:
    """
    Implementasi Backtesting yang Fleksibel.
    Bisa menguji berbagai strategi.
    """

    def run_test(self, data: pd.DataFrame, strategy_name: str) -> dict:
        """
        Menguji strategi yang dipilih.
        'strategy_name' akan menentukan logika sinyal.
        """
        
        df = data.copy().dropna()
        
        # ==========================================================
        # PERBAIKAN: LOGIKA SINYAL DINAMIS
        # ==========================================================
        
        if strategy_name == "MA_CROSS":
            # Strategi 1: MA Cross (Tahan 1 jika MA_S > MA_L)
            df['Signal'] = np.where(df['MA_S'] > df['MA_L'], 1, 0)
        
        elif strategy_name == "RSI_TREND":
            # Strategi 2: Tren RSI (Tahan 1 jika RSI > 50 (garis tengah))
            df['Signal'] = np.where(df['RSI'] > 50, 1, 0)

        elif strategy_name == "RSI_OVER":
            # Strategi 3: RSI Overbought/Oversold (Beli < 30, Jual > 70)
            # Ini strategi MEAN REVERSION, logikanya beda
            # Kita butuh state: 1 = sedang memegang saham, 0 = sedang cash
            df['Signal'] = 0 # Default: cash
            position = 0
            for i in range(1, len(df)):
                # Jika kita TIDAK pegang saham DAN RSI Oversold -> Beli
                if position == 0 and df['RSI'].iloc[i-1] < RSI_OVERSOLD:
                    position = 1
                # Jika kita PEGGANG saham DAN RSI Overbought -> Jual
                elif position == 1 and df['RSI'].iloc[i-1] > RSI_OVERBOUGHT:
                    position = 0
                
                df.loc[df.index[i], 'Signal'] = position
        
        elif strategy_name == "MACD_TREND":
            # Strategi 4: Tren MACD (Tahan 1 jika MACD > Signal Line)
            df['Signal'] = np.where(df['MACD'] > df['MACD_Signal'], 1, 0)
        
        else:
            # Jika ada error, jangan lakukan apa-apa
            df['Signal'] = 0

        # ==========================================================
        
        df['Position'] = df['Signal'].shift(1) # Posisi sehari setelah sinyal
        df.dropna(inplace=True) # Hapus baris pertama (karena shift)

        # Hitung Keuntungan Harian
        df['Returns'] = df['Close'].pct_change()
        df['Strategy_Returns'] = df['Returns'] * df['Position']

        # Hitung Komisi (sederhana: saat posisi berubah)
        df['Commission'] = np.where(df['Position'] != df['Position'].shift(1), COMMISSION, 0)
        df['Strategy_Returns'] -= df['Commission']
        
        # Hitung Ekuitas Kumulatif
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        
        # --- PERHITUNGAN METRIK LANJUTAN (Tidak diubah) ---
        
        # 1. Hitung Max Drawdown
        peak = df['Cumulative_Returns'].cummax()
        drawdown = (df['Cumulative_Returns'] - peak) / peak
        max_drawdown = drawdown.min() if not drawdown.empty else 0.0

        # 2. Hitung Win Rate & Profit Factor
        trades_log = df[df['Position'] != df['Position'].shift(1)].dropna()
        buy_signals = trades_log[trades_log['Position'] == 1]
        sell_signals = trades_log[trades_log['Position'] == 0]

        win_rate = 0.0
        profit_factor = np.nan 

        if not buy_signals.empty and not sell_signals.empty:
            
            buy_prices = buy_signals['Close']
            sell_prices = sell_signals['Close']
            
            if sell_prices.index[0] < buy_prices.index[0]:
                sell_prices = sell_prices.iloc[1:]
            
            if not sell_prices.empty and buy_prices.index[-1] > sell_prices.index[-1]:
                buy_prices = buy_prices.iloc[:-1]
            
            min_len = min(len(buy_prices), len(sell_prices))
            
            if min_len > 0:
                buy_prices = buy_prices.iloc[:min_len]
                sell_prices = sell_prices.iloc[:min_len]
                
                profits = sell_prices.values - buy_prices.values
                total_trades = len(profits)
                winning_trades = np.sum(profits > 0)
                
                if total_trades > 0:
                    win_rate = winning_trades / total_trades
                
                gross_profit = np.sum(profits[profits > 0])
                gross_loss = np.abs(np.sum(profits[profits < 0]))
                
                if gross_loss > 0:
                    profit_factor = gross_profit / gross_loss
                elif gross_profit > 0:
                    profit_factor = np.inf 
                        
        # --- Akhir Perhitungan Metrik ---
        
        total_return = df['Cumulative_Returns'].iloc[-1] - 1 if not df.empty else 0
        total_return_stock = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) if not df.empty else 0
        
        metrics = {
            "total_return_strategy": total_return,
            "total_return_stock": total_return_stock,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
        }
        
        return metrics