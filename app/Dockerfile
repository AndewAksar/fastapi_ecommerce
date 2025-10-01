# Используем базовый образ Python 3.13.3
FROM python:3.13.3

# устанавливаем переменные окружения
ENV HOME=/home/fast \
    APP_HOME=/home/fast/app \
    PYTHONPATH="$PYTHONPATH:/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# создаем домашнюю директорию для пользователя(/home/fast) и директорию для проекта(/home/fast/app)
# создаем группу fast
# создаем отдельного пользователя fast
RUN mkdir -p $APP_HOME \
    && groupadd -r fast \
    && useradd -r -g fast fast

# устанавливаем рабочую директорию
WORKDIR $HOME

# Копирование requirements.txt для кэширования зависимостей
COPY requirements.txt .

# Обновление pip
# Установка зависимостей из списка requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# копирование проекта FastAPI в рабочую директорию
COPY app app
ADD alembic.ini .

# Изменение владельца для всех директорий и файлов проекта на пользователя fast
RUN chown -R fast:fast $APP_HOME

# изменение рабочего пользователя на fast
USER fast