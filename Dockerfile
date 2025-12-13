FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    curl \
    git \
    make \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @mermaid-js/mermaid-cli@11.4.0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt ./
COPY tools/pdf/requirements-pdf.txt ./requirements-pdf.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-pdf.txt

# Install Playwright and Chromium browser (1.48.0+ for 2025 best practices)
RUN pip install 'playwright==1.48.0' \
    && playwright install --with-deps chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/output /app/docs/examples/generated

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run web application
CMD ["python", "web_demo.py"]
