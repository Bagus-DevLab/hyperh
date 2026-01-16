import os
import joblib
import pandas as pd

# Pastikan nama class-nya MLEngine (Huruf Besar M, L, E)
class MLEngine:
    def __init__(self):
        self.model_path = "ml_models/model.pkl"
        self.model = None
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(">> [AI] Model Loaded!")
            except:
                print(">> [AI] Gagal load model.")
        else:
            print(">> [AI] Model belum ada. Mode Monitoring.")

    def predict(self, ph, soil):
        if self.model:
            # Gunakan DataFrame untuk prediksi agar sesuai format training
            df = pd.DataFrame([[ph, soil]], columns=['ph', 'soil_percent'])
            prediction = self.model.predict(df)[0]
            return "ON" if prediction == 1 else "OFF"
        return "UNKNOWN"