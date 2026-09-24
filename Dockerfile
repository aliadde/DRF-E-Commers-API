FROM python:3.13-slim

RUN pip install uv

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .


CMD ["uv", "run", "python", "src/manage.py", "runserver", "0.0.0.0:8000"]
