FROM python:3.12-slim

WORKDIR /src
COPY pyproject.toml README.md ./
COPY monolith ./monolith
RUN pip install --no-cache-dir -e .

WORKDIR /src/monolith
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
