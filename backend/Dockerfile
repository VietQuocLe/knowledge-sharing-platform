FROM python:3.11-slim

# 1. Cài đặt LibreOffice Writer (headless) và font hỗ trợ tiếng Việt
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    fonts-noto \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Cài đặt thư viện Python (không cần sửa requirements.txt vì gọi soffice qua subprocess)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy mã nguồn
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]