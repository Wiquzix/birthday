FROM python:3.11.9-slim

WORKDIR /app

# Устанавливаем необходимые пакеты
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    python3-pip \
    python3.11-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Устанавливаем зависимости с использованием pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Добавляем директорию в PYTHONPATH
ENV PYTHONPATH=/app

CMD ["python", "app/main.py"] 
