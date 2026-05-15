FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema para OpenCV y librerías de visión
RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# En producción:
#   1. Aplica migraciones de base de datos (Alembic)
#   2. Levanta el servidor en el puerto asignado por Render ($PORT)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
