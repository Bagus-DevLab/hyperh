FROM python:3.9-slim

WORKDIR /code

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh folder proyek ke dalam container
COPY . .

# Jalankan uvicorn dari folder root
# app.main:app artinya: masuk folder 'app', cari file 'main.py', jalankan objek 'app'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]