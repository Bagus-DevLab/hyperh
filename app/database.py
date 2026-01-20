import mysql.connector
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DBManager:
    def __init__(self):
        # Konfigurasi database dari .env
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "smart_farming")

    def get_connection(self):
        """
        Membuat koneksi baru ke database setiap kali dipanggil.
        Lebih aman untuk mencegah error 'MySQL Server has gone away'.
        """
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return conn
        except mysql.connector.Error as err:
            print(f"[DB Error] Gagal konek: {err}")
            return None

    def insert_log(self, device_id, ph, soil_percent, soil_adc, pump_status):
        conn = self.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO sensor_logs (device_id, ph, soil_percent, soil_adc, pump_status) 
                VALUES (%s, %s, %s, %s, %s)
            """
            val = (device_id, ph, soil_percent, soil_adc, pump_status)
            cursor.execute(sql, val)
            conn.commit()
            print(">> [DB] Data Disimpan.")
        except Exception as e:
            print(f">> [DB ERROR] {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_latest_data(self):
        """Mengambil 1 data terakhir untuk ditampilkan di Flutter"""
        conn = self.get_connection()
        if not conn: return None

        try:
            cursor = conn.cursor(dictionary=True) # Output JSON
            query = "SELECT * FROM sensor_logs ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(f">> [DB READ ERROR] {e}")
            return None
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def get_history(self, limit=20):
        """Mengambil history data dalam bentuk List"""
        conn = self.get_connection()
        if not conn: return []

        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM sensor_logs ORDER BY id DESC LIMIT %s"
            cursor.execute(query, (limit,))
            result = cursor.fetchall()
            return result
        except Exception as e:
            print(f"[DB Error] {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def delete_latest_log(self):
        """Menghapus 1 data terakhir dari database"""
        conn = self.get_connection()
        if not conn: return {"status": "error", "message": "DB Connection failed"}

        try:
            cursor = conn.cursor()
            # Ambil ID terakhir
            cursor.execute("SELECT id FROM sensor_logs ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            if not row:
                return {"status": "not_found", "message": "Data kosong"}
            
            last_id = row[0]
            # Hapus data
            cursor.execute("DELETE FROM sensor_logs WHERE id = %s", (last_id,))
            conn.commit()
            print(f">> [DB] Data ID {last_id} dihapus.")
            return {"status": "success", "message": "Data terakhir dihapus"}

        except Exception as e:
            print(f">> [DB DELETE ERROR] {e}")
            return {"status": "error", "message": str(e)}
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def delete_log_by_id(self, log_id):
        """Menghapus satu baris log berdasarkan ID"""
        conn = self.get_connection()
        if not conn: return {"status": "error", "message": "DB Connection failed"}

        try:
            cursor = conn.cursor()
            
            # Cek dulu apakah data ada
            cursor.execute("SELECT id FROM sensor_logs WHERE id = %s", (log_id,))
            if not cursor.fetchone():
                return {"status": "not_found", "message": f"Log ID {log_id} tidak ditemukan"}

            # Hapus data
            cursor.execute("DELETE FROM sensor_logs WHERE id = %s", (log_id,))
            conn.commit()
            
            return {"status": "success", "message": f"Log ID {log_id} berhasil dihapus"}
            
        except Exception as e:
            print(f"[DB Error] Gagal delete: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()