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
        
    def get_history(self, limit=20):
        # Mengambil 20 data terakhir
        if self.conn is None or not self.conn.is_connected():
            self.connect()
        try:
            cursor = self.conn.cursor(dictionary=True)
            # Sesuaikan query ini dengan struktur tabel Anda
            # Contoh query SQLite/MySQL standar
            query = "SELECT * FROM sensor_logs ORDER BY id DESC LIMIT %s"
            cursor.execute(query, (limit,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"[DB Error] {e}")
            return []

    def delete_latest_log(self):
        """Menghapus 1 data terakhir dari database"""
        if self.conn is None or not self.conn.is_connected():
            self.connect()

        try:
            cursor = self.conn.cursor()
            # Ambil ID terakhir
            cursor.execute("SELECT id FROM sensor_logs ORDER BY id DESC LIMIT 1")
            last_id = cursor.fetchone()
            if last_id:
                # Hapus data berdasarkan ID terakhir
                delete_query = "DELETE FROM sensor_logs WHERE id = %s"
                cursor.execute(delete_query, (last_id[0],))
                self.conn.commit()
                print(f">> [DB] Data dengan ID {last_id[0]} telah dihapus.")
                return {"status": "deleted", "deleted_id": last_id[0]}
            else:
                print(">> [DB] Tidak ada data untuk dihapus.")
                return {"status": "not_found", "message": "No data to delete"}
        except Exception as e:
            print(f">> [DB DELETE ERROR] {e}")
            return {"status": "error", "message": str(e)}
        finally:
            if self.conn.is_connected():
                cursor.close()

    def delete_log_by_id(self, log_id: int):
        """Menghapus data log berdasarkan ID."""
        if self.conn is None or not self.conn.is_connected():
            self.connect()

        try:
            cursor = self.conn.cursor()
            # Cek dulu apakah data dengan ID tersebut ada
            check_query = "SELECT id FROM sensor_logs WHERE id = %s"
            cursor.execute(check_query, (log_id,))
            data_exists = cursor.fetchone()

            if data_exists:
                # Hapus data berdasarkan ID
                delete_query = "DELETE FROM sensor_logs WHERE id = %s"
                cursor.execute(delete_query, (log_id,))
                self.conn.commit()
                print(f">> [DB] Data dengan ID {log_id} telah dihapus.")
                return {"status": "deleted", "deleted_id": log_id}
            else:
                print(f">> [DB] Data dengan ID {log_id} tidak ditemukan.")
                return {"status": "not_found", "message": f"Log with ID {log_id} not found."}
        except Exception as e:
            print(f">> [DB DELETE ERROR] {e}")
            return {"status": "error", "message": str(e)}
        finally:
            if self.conn.is_connected():
                cursor.close()
                
    # ... code database.py sebelumnya ...

    def delete_log_by_id(self, log_id):
        """Menghapus satu baris log berdasarkan ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Cek dulu apakah data ada
            cursor.execute("SELECT id FROM sensor_logs WHERE id = %s", (log_id,))
            if not cursor.fetchone():
                return {"status": "not_found", "message": f"Log ID {log_id} tidak ditemukan"}

            # Hapus data
            cursor.execute("DELETE FROM sensor_logs WHERE id = %s", (log_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            return {"status": "success", "message": f"Log ID {log_id} berhasil dihapus"}
            
        except Exception as e:
            print(f"[DB Error] Gagal delete: {e}")
            return {"status": "error", "message": str(e)}