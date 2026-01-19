import os
import json
import ssl
import threading
import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from datetime import datetime, timedelta # <--- TAMBAHAN 1

# === ABSOLUTE IMPORTS ===
from app.database import DBManager
from app.ml_engine import MLEngine
from app.models import ControlRequest

load_dotenv()

# Setup App
app = FastAPI(title="Smart Farming System")
db = DBManager()
ai = MLEngine()

# Setup MQTT Config
BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT"))
USER = os.getenv("MQTT_USER")
PASS = os.getenv("MQTT_PASSWORD")
TOPIC_DATA = os.getenv("MQTT_TOPIC_DATA")
TOPIC_CMD = os.getenv("MQTT_TOPIC_CMD")

# --- LOGIKA MQTT ---
def on_connect(client, userdata, flags, rc):
    print(f">> [MQTT] Terhubung (rc={rc})")
    client.subscribe(TOPIC_DATA)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[SENSOR] pH: {payload.get('ph')} | Soil: {payload.get('soil_percent')}%")
        
        # 1. Simpan ke Database
        db.insert_log(
            payload.get('device_id', 'ESP32'),
            payload.get('ph', 0),
            payload.get('soil_percent', 0),
            payload.get('soil_adc', 0),
            payload.get('pump_status', 'OFF')
        )

    except Exception as e:
        print(f"[ERROR MQTT] {e}")

# Inisialisasi Client
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(USER, PASS)
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
mqtt_client.tls_set_context(context)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Jalankan MQTT di Thread Background
def run_mqtt():
    try:
        mqtt_client.connect(BROKER, PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"MQTT Connection Failed: {e}")

@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=run_mqtt)
    t.daemon = True
    t.start()

# --- ENDPOINTS API ---

@app.get("/")
def index():
    return {"status": "System Online", "db": "Connected"}

@app.post("/control")
def control_pump(req: ControlRequest):
    """
    Kirim JSON: {"action": "ON"} atau {"action": "OFF"}
    """
    action = req.action.upper()
    if action not in ["ON", "OFF"]:
        raise HTTPException(400, "Action harus ON atau OFF")
    
    # Publish ke ESP32
    mqtt_client.publish(TOPIC_CMD, action)
    print(f">> [API] User mengirim perintah: {action}")
    
    return {"status": "sent", "action": action}

# === ENDPOINT BARU: DASHBOARD ===
@app.get("/dashboard")
def get_dashboard_data():
    latest_data = db.get_latest_data()

    # Default value (jika DB kosong)
    response = {
        "device_id": "ESP32",
        "device_status": "OFFLINE", # <--- Default OFFLINE
        "last_seen_seconds_ago": -1,
        "timestamp": None,
        "sensor": {"ph": 7.0, "soil_percent": 0, "soil_adc": 0},
        "pump_status": "OFF",
        "ai_analysis": {
            "suggestion": "OFF", 
            "message": "Menunggu data...",
            "is_critical": False
        }
    }

    if latest_data:
        ph_val = float(latest_data.get('ph', 7.0))
        soil_val = int(latest_data.get('soil_percent', 0))
        timestamp_db = latest_data.get('timestamp') # Harus format datetime object dari DB

        # --- LOGIKA CEK STATUS DEVICE (ONLINE/OFFLINE) ---
        # Jika data terakhir diterima kurang dari 60 detik yang lalu, anggap ONLINE
        # Sesuaikan '60' dengan interval pengiriman ESP32 kamu.
        
        is_online = False
        seconds_ago = 0
        
        if timestamp_db:
            # Hitung selisih waktu sekarang dengan waktu data terakhir
            now = datetime.now()
            diff = now - timestamp_db
            seconds_ago = int(diff.total_seconds())

            # Ambang batas toleransi (misal 30 detik)
            if seconds_ago < 30: 
                is_online = True
        
        # -------------------------------------------------

        response["device_status"] = "ONLINE" if is_online else "OFFLINE"
        response["last_seen_seconds_ago"] = seconds_ago
        response["timestamp"] = str(timestamp_db)
        response["device_id"] = latest_data.get('device_id')
        response["sensor"]["ph"] = ph_val
        response["sensor"]["soil_percent"] = soil_val
        response["sensor"]["soil_adc"] = latest_data.get('soil_adc')
        response["pump_status"] = latest_data.get('pump_status')

        # Analisis AI
        ai_suggestion = ai.predict(ph_val, soil_val)
        
        info_message = "Kondisi Ideal"
        if ai_suggestion == "ON":
            if soil_val < 30:
                info_message = "Tanah Kering! AI menyarankan Siram."
            elif ph_val < 5.0:
                info_message = "pH Asam! AI menyarankan Siram."
            else:
                info_message = "AI menyarankan Pompa ON."
        else:
            info_message = "Kondisi Aman. Hemat Air."

        response["ai_analysis"] = {
            "suggestion": ai_suggestion,
            "message": info_message,
            "is_critical": True if ai_suggestion == "ON" else False
        }

    return response

@app.get("/history")
def get_history_log():
    # Ambil 50 data terakhir
    data = db.get_history(limit=50)
    return {"status": "success", "data": data}