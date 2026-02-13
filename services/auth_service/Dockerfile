FROM python:3.11-slim

WORKDIR /app

# Install shared library
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
COPY shared/ /app/shared_lib/
RUN pip install --no-cache-dir /app/shared_lib/

# Install service dependencies
COPY services/auth_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/auth_service/app ./app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
