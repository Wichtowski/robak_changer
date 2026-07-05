FROM python:3.11-slim

WORKDIR /app

# Copy project
COPY . .

# Install deps if requirements.txt exists
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip setuptools wheel \
    && bash -c 'if [ -f requirements.txt ]; then pip install -r requirements.txt; fi'

ENV PYTHONUNBUFFERED=1

# Default command — adjust to your actual entrypoint if needed
CMD ["python", "main.py"]
