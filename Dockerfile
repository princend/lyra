# 使用官方的 Python 基本映像
FROM python:3.12

# 設定工作目錄
WORKDIR /app

# 安装系统依赖工具
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0   

# 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製 Django 應用程式
COPY . .
# 設定環境變數
ENV PORT 8000
ENV PYTHONUNBUFFERED TRUE

# 使用 gunicorn 啟動服務
# CMD exec gunicorn --bind :$PORT --workers=2 lyra.wsgi:application
# EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
