#!/bin/sh

echo "[flask] Waiting for database..."
python - <<'PY'
import os, time
import psycopg2

host = os.getenv('PG_DB_HOST','postgres')
port = int(os.getenv('PG_DB_PORT','5432'))
db = os.getenv('PG_DB_NAME','synergy')
user = os.getenv('PG_DB_USER','synergy')
pwd = os.getenv('PG_DB_PASSWORD','synergy')

for i in range(60):
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pwd)
        conn.close()
        print('[flask] DB ready')
        break
    except Exception as e:
        print('[flask] DB not ready yet...', e)
        time.sleep(2)
else:
    print('[flask] DB readiness timed out')
PY

echo "[flask] Starting Flask app..."
exec python flask_app.py
