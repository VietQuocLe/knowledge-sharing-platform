FROM python:3.11-slim

# 1. Cài đặt LibreOffice Writer (headless) và font hỗ trợ tiếng Việt
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    fonts-noto \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy source code
COPY . .

# 4. Khởi chạy Uvicorn server (hỗ trợ dynamic port trên Cloud, fallback port 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]