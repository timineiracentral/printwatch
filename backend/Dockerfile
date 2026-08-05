FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

COPY app/ ./app/
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY scripts/migrate_db.py ./scripts/migrate_db.py
COPY scripts/ensure_db_schema.py ./scripts/ensure_db_schema.py

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
