FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-cache

COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONASYNCIODEBUG=0

CMD uvicorn project.api.app:app --host 0.0.0.0 --port $PORT --proxy-headers --no-access-log --log-level warning --timeout-keep-alive 300 --limit-concurrency 100