import os
import mysql.connector
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from dotenv import load_dotenv

# Load env variables
load_dotenv()

print(">> [1/4] Menghubungkan ke Database...")

# Koneksi ke Database (Menggunakan host 'db' karena jalan di dalam network docker)
try:
    conn = mysql.connector.connect(
        host="db",           # Service name di docker-compose
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
except Exception as e:
    print(f"Error koneksi DB: {e}")
    exit()

print(">> [2/4] Fetching Data...")
query = "SELECT ph, soil_percent, pump_status FROM sensor_logs"
df = pd.read_sql(query, conn)
conn.close()

# Cek apakah data cukup
if len(df) < 10:
    print("❌ Data terlalu sedikit (<10 baris). Perbanyak data manual dulu!")
    exit()

print(f"   Total Data: {len(df)} baris")

# --- PREPROCESSING ---
# Hapus data yang pump_status-nya aneh/kosong
df = df.dropna()
# Ubah 'ON' jadi 1, 'OFF' jadi 0
df['target'] = df['pump_status'].apply(lambda x: 1 if x.upper() == 'ON' else 0)

# Fitur (X) dan Target (y)
X = df[['ph', 'soil_percent']]
y = df['target']

# --- TRAINING ---
print(">> [3/4] Melatih Model Random Forest...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --- EVALUASI ---
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"✅ Akurasi Model: {acc * 100:.2f}%")
print("\nLaporan Detail:")
print(classification_report(y_test, y_pred))

# --- SIMPAN ---
print(">> [4/4] Menyimpan Model...")
output_path = "ml_models/model.pkl"

# Pastikan folder ada
if not os.path.exists("ml_models"):
    os.makedirs("ml_models")

joblib.dump(model, output_path)
print(f"🎉 Model baru berhasil disimpan di: {output_path}")
print("   Silakan restart container backend agar model baru terbaca.")