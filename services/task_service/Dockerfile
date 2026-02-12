FROM python:3.11-slim
WORKDIR /app
COPY shared/ /app/shared_lib/
RUN pip install --no-cache-dir /app/shared_lib/
COPY services/task_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/task_service/app ./app
EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
