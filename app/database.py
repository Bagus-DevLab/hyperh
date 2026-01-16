import mysql.connector
import os
import time

class DBManager:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        retries = 5
        while retries > 0:
            try:
                self.conn = mysql.connector.connect(
                    host=os.getenv("DB_HOST"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    database=os.getenv("DB_NAME")
                )
                print(">> [DB] Terhubung ke MySQL!")
                return
            except mysql.connector.Error as err:
                print(f">> [DB] Menunggu database... ({err})")
                time.sleep(5)
                retries -= 1

    def insert_log(self, device_id, ph, soil_percent, soil_adc, pump_status):
        if self.conn is None or not self.conn.is_connected():
            self.connect()
        
        try:
            cursor = self.conn.cursor()
            sql = "INSERT INTO sensor_logs (device_id, ph, soil_percent, soil_adc, pump_status) VALUES (%s, %s, %s, %s, %s)"
            val = (device_id, ph, soil_percent, soil_adc, pump_status)
            cursor.execute(sql, val)
            self.conn.commit()
            print(">> [DB] Data Disimpan.")
            cursor.close()
        except Exception as e:
            print(f">> [DB ERROR] {e}")
            
    # ... (kode connect dan insert_log biarkan saja) ...

    # === TAMBAHKAN FUNGSI INI DI DALAM CLASS DBMANAGER ===
    def get_latest_data(self):
        """Mengambil 1 data terakhir untuk ditampilkan di Flutter"""
        if self.conn is None or not self.conn.is_connected():
            self.connect()

        try:
            cursor = self.conn.cursor(dictionary=True) # dictionary=True agar outputnya jadi JSON (key:value)
            # Ambil data paling baru berdasarkan ID terakhir
            query = "SELECT * FROM sensor_logs ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print(f">> [DB READ ERROR] {e}")
            return None