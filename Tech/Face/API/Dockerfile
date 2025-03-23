# Используем официальный образ Python
FROM python:3.9

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы в контейнер
COPY . /app

# Обновляем пакеты и устанавливаем зависимости для OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir fastapi uvicorn deepface opencv-python-headless tf-keras python-multipart

# Открываем порт
EXPOSE 8000

# Запускаем FastAPI сервер
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]