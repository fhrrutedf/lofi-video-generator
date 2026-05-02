FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Set workdir
WORKDIR /app

# Copy requirements first (for layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[api,all]" && \
    pip install --no-cache-dir psycopg2-binary arabic-reshaper python-bidi

# Copy application
COPY lofi_gen/ ./lofi_gen/

# Create directories
RUN mkdir -p output temp

# Expose ports
EXPOSE 8000 8501

# Default command (uses api_v2 with DB + auth)
CMD ["uvicorn", "lofi_gen.api_v2:app", "--host", "0.0.0.0", "--port", "8000"]
