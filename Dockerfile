FROM python:3.14-slim AS construccion
COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM python:3.14-slim
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=construccion --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PORT=8000
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ['PORT'] + '/health', timeout=4)"
CMD ["sh", "-c", "uvicorn gestion_documental.api.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
