FROM python:3.11-slim
WORKDIR /app
RUN pip install --default-timeout=100 --no-cache-dir --upgrade pip setuptools wheel
COPY shared/ /app/shared_lib/
RUN pip install --default-timeout=100 --no-cache-dir /app/shared_lib/
COPY services/notification_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/notification_service/app ./app
EXPOSE 8005
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
