# indicators/base_indicator.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseIndicator(ABC):
    """Kelas dasar abstrak untuk semua indikator teknikal."""
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Metode untuk menghitung dan menambahkan kolom indikator ke DataFrame."""
        pass