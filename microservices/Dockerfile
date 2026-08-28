FROM python:3.12-slim

WORKDIR /src
COPY pyproject.toml README.md ./
COPY monolith ./monolith
COPY microservices ./microservices
RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/src/microservices:/src/monolith
WORKDIR /src/microservices
EXPOSE 8000
# CMD is set per Compose service (uvicorn <pkg>.main:app)
