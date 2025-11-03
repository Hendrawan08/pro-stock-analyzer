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
    Ensemble predictor:
    - Logistic Regression
    - Random Forest
    - Gradient Boosting

    Perbaikan: menambahkan CalibratedClassifierCV agar probabilitas (confidence) lebih realistis.
    Output tetap: (accuracy, 'BUY:0.723') atau (accuracy, 'SELL:0.123')
    """

    REQUIRED_COLS = [
        'Close', 'RSI', 'MACD', 'MACD_Signal', '%K', '%D',
        'MA_S', 'MA_M', 'MA_L', 'BB_High', 'BB_Low'
    ]

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

        # base ensemble (will be wrapped by CalibratedClassifierCV during training)
        self.ensemble = VotingClassifier(estimators=[('lr', self.model_lr), ('rf', self.model_rf), ('gb', self.model_gb)], voting='soft')

        # model aktif (bisa jadi CalibratedClassifierCV atau fallback)
        self.active_model_ = None

    def _validate_and_prepare_df(self, data: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input harus pandas.DataFrame")
        missing = [c for c in self.REQUIRED_COLS if c not in data.columns]
        if missing:
            raise ValueError(f"DataFrame tidak memiliki kolom required: {missing}")
        df = data.copy()
        for c in self.REQUIRED_COLS:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        return df

    def _prepare_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        df = self._validate_and_prepare_df(data)
        df['Future_Close'] = df['Close'].shift(-self.PREDICTION_HORIZON)
        df['Target'] = (df['Future_Close'] > df['Close']).astype(int)

        bb_range = (df['BB_High'] - df['BB_Low']).replace(0, np.nan)
        bb_pct = (df['Close'] - df['BB_Low']) / bb_range
        bb_pct = bb_pct.replace([np.inf, -np.inf], np.nan)
        volatility = df['Close'].rolling(self.PREDICTION_HORIZON).std()

        features = pd.DataFrame({
            'RSI': df['RSI'],
            'MACD_Hist': (df['MACD'] - df['MACD_Signal']),
            '%K': df['%K'],
            '%D': df['%D'],
            'MA_S_vs_M': (df['MA_S'] > df['MA_M']).astype(int),
            'MA_M_vs_L': (df['MA_M'] > df['MA_L']).astype(int),
            'Price_vs_MA_M': (df['Close'] > df['MA_M']).astype(int),
            'BB_Pct': bb_pct,
            'Volatility_N': volatility
        }, index=df.index)

        full = pd.concat([features, df['Target']], axis=1)
        full = full.dropna()
        if full.empty:
            raise ValueError("Hasil preprocessing menghasilkan 0 baris setelah dropna (cek data input).")

        X_clean = full.drop(columns=['Target'])
        y_clean = full['Target'].astype(int)
        return X_clean, y_clean

    def predict(self, data: pd.DataFrame) -> Tuple[float, str]:
        """
        Kembalian: (accuracy, 'BUY:0.723') atau (accuracy, 'SELL:0.123')
        - Melatih dengan CalibratedClassifierCV(ensemble, cv=3) untuk probabilitas lebih andal.
        - Jika kalibrasi/ensemble gagal, fallback ke GBC / RF / LR (dengan usaha kalibrasi bila memungkinkan).
        """
        try:
            X, y = self._prepare_data(data)
        except Exception as e:
            return 0.0, f"Data Error: {e}"

        if len(X) < 50:
            return 0.0, "Data N/A"

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=self.TEST_SIZE, shuffle=False)

        if len(np.unique(y_train)) < 2:
            return 0.0, "No Variation"

        # scale features (LR needs scaled; ensemble wrapped by calibrator will handle scaling input)
        self.scaler.fit(X_train)
        X_train_s = self.scaler.transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        accuracy = 0.0
        train_msgs = []

        # Try: train calibrated ensemble
        try:
            # CalibratedClassifierCV fits base estimator internally using cross-val on X_train_s
            calibrator = CalibratedClassifierCV(base_estimator=self.ensemble, cv=3)
            calibrator.fit(X_train_s, y_train)
            y_pred = calibrator.predict(X_test_s)
            accuracy = float(accuracy_score(y_test, y_pred))
            self.active_model_ = calibrator
            model_trained_on_scaled = True
        except Exception as e_cal:
            train_msgs.append(f"CalibEnsembleErr:{e_cal}")
            # FALLBACK sequence (try GBC with calibration, then RF, then LR)
            tried = False
            try:
                self.model_gb.fit(X_train, y_train)
                # try to calibrate GBC
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
                try:
                    self.model_lr.fit(X_train_s, y_train)
                    cal_lr = None
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
                    return 0.0, f"Model Error: {' | '.join(train_msgs)}"

        # prepare last row
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
