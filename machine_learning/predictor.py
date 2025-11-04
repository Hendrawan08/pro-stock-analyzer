# machine_learning/predictor.py (fixed & more robust column handling)

import pandas as pd
import numpy as np
from typing import Tuple

# --- Impor Scikit-Learn ---
try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.calibration import CalibratedClassifierCV
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False
    LogisticRegression = None
    RandomForestClassifier = None
    GradientBoostingClassifier = None
    VotingClassifier = None
    StandardScaler = None
    train_test_split = None
    accuracy_score = None
    CalibratedClassifierCV = None


class MLPredictor:
    """
    Ensemble predictor, robust terhadap variasi nama kolom.
    Output: (accuracy, 'BUY:0.723') atau (accuracy, 'SELL:0.123')
    """

    # NOTE: we will accept many possible column names and fallback to computed indicators where possible.
    def __init__(self, prediction_horizon: int = 5, test_size: float = 0.2, random_state: int = 42):
        if not SKLEARN_AVAILABLE:
            raise ImportError("Scikit-learn tidak ditemukan. Jalankan: pip install scikit-learn")

        self.PREDICTION_HORIZON = int(prediction_horizon)
        self.TEST_SIZE = float(test_size)
        self.RANDOM_STATE = int(random_state)

        self.scaler = StandardScaler()

        self.model_lr = LogisticRegression(solver='liblinear', C=0.1, random_state=self.RANDOM_STATE, class_weight='balanced')
        self.model_rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=self.RANDOM_STATE, n_jobs=-1, class_weight='balanced')
        self.model_gb = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=self.RANDOM_STATE)

        # base ensemble (will be wrapped by CalibratedClassifierCV during training if possible)
        self.ensemble = VotingClassifier(estimators=[('lr', self.model_lr), ('rf', self.model_rf), ('gb', self.model_gb)], voting='soft')

        # model aktif (bisa jadi CalibratedClassifierCV atau fallback)
        self.active_model_ = None

    # -------------------------
    # Utility: flexible column finder
    # -------------------------
    @staticmethod
    def _find_column_by_keywords(cols, keywords):
        """Return first column name that contains any of the keywords (case-insensitive)"""
        cols_l = [c.lower() for c in cols]
        for kw in keywords:
            kw = kw.lower()
            for i, c in enumerate(cols_l):
                if kw in c:
                    return cols[i]
        return None

    @staticmethod
    def _ensure_numeric_series(s):
        return pd.to_numeric(s, errors='coerce')

    # -------------------------
    # Prepare raw dataframe: normalize columns & compute fallback indicators
    # -------------------------
    def _normalize_and_prepare_input(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Accept dataframes with many naming conventions. Returns a dataframe that
        contains at least these normalized columns (lowercase):
          - close, rsi, macd, macd_signal, percent_k, percent_d, ma_s, ma_m, ma_l, bb_high, bb_low, volume
        Where missing indicators are computed as fallback from close (MA, BB).
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input harus pandas.DataFrame")

        df = data.copy()
        # lowercase columns for flexible matching
        df.columns = [str(c).lower() for c in df.columns]

        # find close
        close_col = self._find_column_by_keywords(df.columns, ['close', 'adj close', 'adjclose'])
        if close_col is None:
            raise ValueError("Kolom 'close' tidak ditemukan dalam DataFrame input.")

        # ensure numeric
        df[close_col] = pd.to_numeric(df[close_col], errors='coerce')

        # RSI candidate
        rsi_col = self._find_column_by_keywords(df.columns, ['rsi'])
        # MACD candidates
        macd_hist_col = self._find_column_by_keywords(df.columns, ['macdh', 'macd_h', 'macd_hist', 'macd_histogram'])
        macd_val_col = self._find_column_by_keywords(df.columns, ['macd', 'macd_12', 'macd_12_26', 'macd_12_26_9'])
        macd_sig_col = self._find_column_by_keywords(df.columns, ['macds', 'macd_s', 'macd_signal'])

        # Stochastic %K %D
        pctk_col = self._find_column_by_keywords(df.columns, ['%k', 'percent_k', 'stoch_k', 'k_'])
        pctd_col = self._find_column_by_keywords(df.columns, ['%d', 'percent_d', 'stoch_d', 'd_'])

        # MA candidates (short/medium/long)
        ma_s_col = self._find_column_by_keywords(df.columns, ['ma_s', 'ma_short', 'ema9', 'ma9', 'ema5', 'ma5'])
        ma_m_col = self._find_column_by_keywords(df.columns, ['ma_m', 'ma_mid', 'ma20', 'ma21', 'ema20', 'ma50', 'ema50'])
        ma_l_col = self._find_column_by_keywords(df.columns, ['ma_l', 'ma_long', 'ma50', 'ma100', 'ma200', 'ema200'])

        # Bollinger bands
        bb_high_col = self._find_column_by_keywords(df.columns, ['bbu', 'bb_high', 'bbupper', 'bb_up'])
        bb_low_col = self._find_column_by_keywords(df.columns, ['bbl', 'bb_low', 'bblower', 'bb_low'])

        # volume
        vol_col = self._find_column_by_keywords(df.columns, ['volume', 'vol'])

        # Create a normalized frame 'norm' with required names
        norm = pd.DataFrame(index=df.index)
        norm['close'] = df[close_col]

        # RSI: if found use it, else compute simple RSI(14)
        if rsi_col and rsi_col in df.columns:
            norm['rsi'] = self._ensure_numeric_series(df[rsi_col])
        else:
            # compute fallback RSI(14)
            close = norm['close']
            delta = close.diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            roll_up = up.ewm(alpha=1/14, adjust=False).mean()
            roll_down = down.ewm(alpha=1/14, adjust=False).mean()
            rs = roll_up / roll_down.replace(0, 1e-8)
            norm['rsi'] = 100 - (100 / (1 + rs))

        # MACD & signal: try smart mapping, else compute simple MACD(12,26,9)
        macd_val = None
        macd_sig = None
        if macd_val_col and macd_val_col in df.columns and macd_sig_col and macd_sig_col in df.columns:
            macd_val = self._ensure_numeric_series(df[macd_val_col])
            macd_sig = self._ensure_numeric_series(df[macd_sig_col])
        elif macd_hist_col and macd_hist_col in df.columns:
            # sometimes TA libs give macdh directly (hist), so try to reconstruct approximate macd and signal:
            macd_hist = self._ensure_numeric_series(df[macd_hist_col])
            # best-effort: set macd_hist as MACD - SIGNAL; we'll set MACD as macd_hist + signal (approx)
            # but signal unknown; fallback: set MACD=macd_hist and signal=0 to still provide a numeric value
            macd_val = macd_hist
            macd_sig = pd.Series(0.0, index=macd_hist.index)
        else:
            # compute MACD manually
            close = norm['close']
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_val = ema12 - ema26
            macd_sig = macd_val.ewm(span=9, adjust=False).mean()

        norm['macd'] = macd_val
        norm['macd_signal'] = macd_sig

        # %K / %D (stochastic) fallback: if not found, set NaN (not critical)
        if pctk_col and pctk_col in df.columns:
            norm['pctk'] = self._ensure_numeric_series(df[pctk_col])
        else:
            norm['pctk'] = np.nan
        if pctd_col and pctd_col in df.columns:
            norm['pctd'] = self._ensure_numeric_series(df[pctd_col])
        else:
            norm['pctd'] = np.nan

        # Moving averages: use found columns or compute MA short=9/medium=20/long=50 as fallback
        if ma_s_col and ma_s_col in df.columns:
            norm['ma_s'] = self._ensure_numeric_series(df[ma_s_col])
        else:
            norm['ma_s'] = norm['close'].rolling(window=9, min_periods=1).mean()

        if ma_m_col and ma_m_col in df.columns:
            norm['ma_m'] = self._ensure_numeric_series(df[ma_m_col])
        else:
            norm['ma_m'] = norm['close'].rolling(window=20, min_periods=1).mean()

        if ma_l_col and ma_l_col in df.columns:
            norm['ma_l'] = self._ensure_numeric_series(df[ma_l_col])
        else:
            norm['ma_l'] = norm['close'].rolling(window=50, min_periods=1).mean()

        # Bollinger bands: use found, otherwise compute 20,2
        if bb_high_col and bb_high_col in df.columns and bb_low_col and bb_low_col in df.columns:
            norm['bb_high'] = self._ensure_numeric_series(df[bb_high_col])
            norm['bb_low'] = self._ensure_numeric_series(df[bb_low_col])
        else:
            m = norm['close'].rolling(window=20, min_periods=1).mean()
            s = norm['close'].rolling(window=20, min_periods=1).std().fillna(0)
            norm['bb_high'] = m + 2 * s
            norm['bb_low'] = m - 2 * s

        # volume
        if vol_col and vol_col in df.columns:
            norm['volume'] = pd.to_numeric(df[vol_col], errors='coerce')
        else:
            norm['volume'] = np.nan

        # final cleanup
        norm = norm.reset_index(drop=True)
        return norm

    # -------------------------
    # Preprocess into features X and target y
    # -------------------------
    def _prepare_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        # normalize input and ensure required computed features exist
        df = self._normalize_and_prepare_input(data)

        # create future close and binary target (1 if price up after horizon)
        df['future_close'] = df['close'].shift(-self.PREDICTION_HORIZON)
        df['target'] = (df['future_close'] > df['close']).astype(int)

        # compute BB pct safely
        bb_range = (df['bb_high'] - df['bb_low']).replace(0, np.nan)
        bb_pct = (df['close'] - df['bb_low']) / bb_range
        bb_pct = bb_pct.replace([np.inf, -np.inf], np.nan)

        volatility = df['close'].rolling(self.PREDICTION_HORIZON, min_periods=1).std()

        features = pd.DataFrame({
            'rsi': df['rsi'],
            'macd_hist': (df['macd'] - df['macd_signal']),
            'pctk': df['pctk'],
            'pctd': df['pctd'],
            'ma_s_vs_m': (df['ma_s'] > df['ma_m']).astype(int),
            'ma_m_vs_l': (df['ma_m'] > df['ma_l']).astype(int),
            'price_vs_ma_m': (df['close'] > df['ma_m']).astype(int),
            'bb_pct': bb_pct,
            'volatility_n': volatility
        }, index=df.index)

        full = pd.concat([features, df['target']], axis=1)
        full = full.dropna()
        if full.empty:
            raise ValueError("Hasil preprocessing menghasilkan 0 baris setelah dropna (cek data input).")

        X_clean = full.drop(columns=['target'])
        y_clean = full['target'].astype(int)
        return X_clean, y_clean

    # -------------------------
    # Predict (train internally every call) — keep behaviour but robust
    # -------------------------
    def predict(self, data: pd.DataFrame) -> Tuple[float, str]:
        """
        Returns: (accuracy, 'BUY:0.723') or (accuracy, 'SELL:0.123')
        Tries to calibrate ensemble; falls back gracefully.
        """
        try:
            X, y = self._prepare_data(data)
        except Exception as e:
            return 0.0, f"Data Error: {e}"

        if len(X) < 50:
            return 0.0, "Data N/A"

        # split (no shuffle for time-series)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=self.TEST_SIZE, shuffle=False)

        if len(np.unique(y_train)) < 2:
            return 0.0, "No Variation"

        # scale features where needed
        self.scaler.fit(X_train)
        X_train_s = self.scaler.transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        accuracy = 0.0
        train_msgs = []
        model_trained_on_scaled = False

        # Try: train calibrated ensemble first
        try:
            calibrator = CalibratedClassifierCV(base_estimator=self.ensemble, cv=3)
            calibrator.fit(X_train_s, y_train)
            y_pred = calibrator.predict(X_test_s)
            accuracy = float(accuracy_score(y_test, y_pred))
            self.active_model_ = calibrator
            model_trained_on_scaled = True
        except Exception as e_cal:
            train_msgs.append(f"CalibEnsembleErr:{e_cal}")
            # fallback sequence
            tried = False
            # Try GBC (unscaled)
            try:
                self.model_gb.fit(X_train, y_train)
                try:
                    cal_gb = CalibratedClassifierCV(base_estimator=self.model_gb, cv=3)
                    cal_gb.fit(X_train, y_train)
                    y_pred = cal_gb.predict(X_test)
                    accuracy = float(accuracy_score(y_test, y_pred))
                    self.active_model_ = cal_gb
                except Exception:
                    y_pred = self.model_gb.predict(X_test)
                    accuracy = float(accuracy_score(y_test, y_pred))
                    self.active_model_ = self.model_gb
                model_trained_on_scaled = False
                tried = True
            except Exception as e_gb:
                train_msgs.append(f"GBErr:{e_gb}")
            if not tried:
                # Try RF
                try:
                    self.model_rf.fit(X_train, y_train)
                    try:
                        cal_rf = CalibratedClassifierCV(base_estimator=self.model_rf, cv=3)
                        cal_rf.fit(X_train, y_train)
                        y_pred = cal_rf.predict(X_test)
                        accuracy = float(accuracy_score(y_test, y_pred))
                        self.active_model_ = cal_rf
                    except Exception:
                        y_pred = self.model_rf.predict(X_test)
                        accuracy = float(accuracy_score(y_test, y_pred))
                        self.active_model_ = self.model_rf
                    model_trained_on_scaled = False
                    tried = True
                except Exception as e_rf:
                    train_msgs.append(f"RFErr:{e_rf}")
            if not tried:
                # Try LR (requires scaled)
                try:
                    self.model_lr.fit(X_train_s, y_train)
                    try:
                        cal_lr = CalibratedClassifierCV(base_estimator=self.model_lr, cv=3)
                        cal_lr.fit(X_train_s, y_train)
                        y_pred = cal_lr.predict(X_test_s)
                        accuracy = float(accuracy_score(y_test, y_pred))
                        self.active_model_ = cal_lr
                        model_trained_on_scaled = True
                    except Exception:
                        y_pred = self.model_lr.predict(X_test_s)
                        accuracy = float(accuracy_score(y_test, y_pred))
                        self.active_model_ = self.model_lr
                        model_trained_on_scaled = True
                except Exception as e_lr:
                    train_msgs.append(f"LRErr:{e_lr}")
                    # if everything failed, return with message
                    return 0.0, f"Model Error: {' | '.join(train_msgs)}"

        # prepare last row features
        last_features_raw = X.iloc[[-1]]
        last_features_scaled = self.scaler.transform(last_features_raw)

        # predict and get calibrated probability if possible
        try:
            use_scaled = model_trained_on_scaled
            last_input = last_features_scaled if use_scaled else last_features_raw

            final_code = int(self.active_model_.predict(last_input)[0])

            ml_prob = None
            if hasattr(self.active_model_, 'predict_proba'):
                try:
                    probs = self.active_model_.predict_proba(last_input)[0]
                    # find index for class 1
                    if hasattr(self.active_model_, 'classes_'):
                        classes = list(self.active_model_.classes_)
                        if 1 in classes:
                            idx1 = classes.index(1)
                            ml_prob = float(probs[idx1])
                        else:
                            ml_prob = float(probs[-1])
                    else:
                        ml_prob = float(probs[-1])
                except Exception:
                    ml_prob = None
            elif hasattr(self.active_model_, 'decision_function'):
                try:
                    dfv = float(self.active_model_.decision_function(last_input)[0])
                    ml_prob = 1.0 / (1.0 + np.exp(-dfv))
                except Exception:
                    ml_prob = None

            if ml_prob is None:
                ml_prob = float(accuracy)

        except Exception as e_pred:
            return float(accuracy), f"Pred Error: {e_pred}"

        final_signal = "BUY" if final_code == 1 else "SELL"
        ml_prob = max(0.0, min(1.0, float(ml_prob)))
        ml_pred_str = f"{final_signal}:{ml_prob:.3f}"
        return float(accuracy), ml_pred_str
