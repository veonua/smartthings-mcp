FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv pip install --system --prod

COPY src ./src

CMD ["uv", "run", "src/mcp_smartthings/server.py"]
