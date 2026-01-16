CREATE TABLE IF NOT EXISTS sensor_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    device_id VARCHAR(50),
    ph FLOAT,
    soil_percent INT,
    soil_adc INT,
    pump_status VARCHAR(10)
);