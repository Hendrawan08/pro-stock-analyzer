# trading_log_tracker.py

import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
import logging

# Setup logging konfigurasi dasar
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


class TradingLogTracker:
    """
    Mengelola database simulasi trading (trading_log.xlsx).
    - Memuat / menyimpan log trading ke file Excel.
    - Menambah dan menutup posisi trading.
    - Mengambil data semua trade atau hanya posisi terbuka.
    """

    FILE_PATH = Path("trading_log.xlsx")
    COLUMNS = [
        'id', 'timestamp_open', 'symbol', 'status',
        'entry_price', 'lots', 'tp_price', 'sl_price',
        'timestamp_close', 'exit_price', 'pnl_rp'
    ]

    def __init__(self):
        self.trades_df = self.load_trades()

    def load_trades(self) -> pd.DataFrame:
        """Memuat log trading dari file Excel."""
        if self.FILE_PATH.exists():
            try:
                df = pd.read_excel(self.FILE_PATH)
                for col in self.COLUMNS:
                    if col not in df.columns:
                        df[col] = pd.Series(dtype="object")
                df = df[self.COLUMNS]
                logging.info(f"Berhasil memuat data dari {self.FILE_PATH}")
                return df
            except Exception as e:
                logging.error(f"Gagal memuat {self.FILE_PATH}: {e}")
                return self._create_empty_df()
        else:
            logging.warning(f"File {self.FILE_PATH} tidak ditemukan, membuat baru.")
            return self._create_empty_df()

    def _create_empty_df(self) -> pd.DataFrame:
        """Membuat DataFrame kosong jika file tidak ada."""
        return pd.DataFrame(columns=self.COLUMNS)

    def save_trades(self) -> None:
        """Menyimpan DataFrame ke file Excel."""
        try:
            self.trades_df.to_excel(self.FILE_PATH, index=False)
            logging.info(f"Data trading disimpan ke {self.FILE_PATH}")
        except Exception as e:
            logging.error(f"Gagal menyimpan {self.FILE_PATH}: {e}")

    def add_trade(self, symbol: str, entry_price: float, lots: float,
                  tp_price: float, sl_price: float) -> str:
        """
        Menambahkan posisi trading baru (status OPEN).
        Mengembalikan ID unik trade.
        """
        if lots <= 0 or entry_price <= 0:
            raise ValueError("Lots dan entry_price harus lebih besar dari 0.")

        trade_id = str(uuid.uuid4())
        timestamp = datetime.now()

        new_trade = pd.DataFrame([{
            'id': trade_id,
            'timestamp_open': timestamp,
            'symbol': symbol.upper(),
            'status': 'OPEN',
            'entry_price': entry_price,
            'lots': lots,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'timestamp_close': pd.NaT,
            'exit_price': None,
            'pnl_rp': None
        }])

        self.trades_df = pd.concat([self.trades_df, new_trade], ignore_index=True)
        self.save_trades()
        return trade_id

    def close_trade(self, trade_id: str, exit_price: float, status: str) -> tuple[bool, float]:
        """
        Menutup posisi (PROFIT atau LOSS) dengan harga exit.
        Mengembalikan tuple (berhasil, nilai_pnl).
        """
        if exit_price <= 0:
            raise ValueError("Exit price harus lebih besar dari 0.")

        idx = self.trades_df[self.trades_df['id'] == trade_id].index

        if not idx.empty:
            idx = idx[0]
            trade = self.trades_df.iloc[idx]

            entry_value = float(trade['entry_price']) * float(trade['lots']) * 100
            exit_value = exit_price * float(trade['lots']) * 100
            pnl = exit_value - entry_value

            self.trades_df.at[idx, 'status'] = status.upper()
            self.trades_df.at[idx, 'exit_price'] = exit_price
            self.trades_df.at[idx, 'pnl_rp'] = pnl
            self.trades_df.at[idx, 'timestamp_close'] = datetime.now()

            self.save_trades()
            logging.info(f"Trade {trade_id} ditutup dengan PnL: {pnl:.2f}")
            return True, pnl

        logging.warning(f"Trade ID {trade_id} tidak ditemukan.")
        return False, 0.0

    def get_all_trades(self) -> pd.DataFrame:
        """Mengambil semua data trading, diurutkan terbaru di atas."""
        return self.trades_df.sort_values(by="timestamp_open", ascending=False)

    def get_open_positions(self) -> pd.DataFrame:
        """Mengambil semua posisi yang masih OPEN."""
        return self.trades_df[self.trades_df['status'] == 'OPEN'].copy()
