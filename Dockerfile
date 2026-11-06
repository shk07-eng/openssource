FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_PATH=/app/data/expenses.db

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY static ./static
RUN mkdir -p /app/data \
    && python -m compileall -q app \
    && python -c "from app.main import app; print(app.title)"
EXPOSE 8000
VOLUME ["/app/data"]
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host ${HOST} --port ${PORT}"]
