FROM python:3.11-slim
WORKDIR /app
COPY shared/ /app/shared_lib/
RUN pip install --no-cache-dir /app/shared_lib/
COPY services/api_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/api_gateway/app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
