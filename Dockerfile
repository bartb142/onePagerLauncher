FROM python:3.12-slim

WORKDIR /app
COPY . .

# Update pip
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]