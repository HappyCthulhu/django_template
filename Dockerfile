FROM python:3.13-slim

WORKDIR /app

# python не будет создавать .pyc/__pycache__
ENV PYTHONDONTWRITEBYTECODE=1
# stdout/stderr Python будет писать без буферизации.
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Сначала устанавливаем либы, потом копируем код
# после внесения изменений в код, пересборка будет быстрее, т.к. либы не будут переустанавливаться
RUN pip install uv && \
    mkdir -p /opt/venv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "server.configs.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]


