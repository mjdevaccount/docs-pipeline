FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    curl \
    git \
    make \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @mermaid-js/mermaid-cli@11.12.0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt ./
COPY tools/pdf/requirements-pdf.txt ./requirements-pdf.txt
COPY tools/pdf/requirements-cli.txt ./requirements-cli.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-pdf.txt \
    && pip install --no-cache-dir -r requirements-cli.txt

# Install Playwright and Chromium browser (1.48.0+ for 2025 best practices)
# Install system dependencies for Playwright and Puppeteer (mermaid-cli)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-unifont \
    fonts-liberation \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install 'playwright==1.48.0' \
    && playwright install chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/output /app/docs/examples/generated

# Create non-root user for security (required for Puppeteer --no-sandbox flags)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run web application
CMD ["python", "web_demo.py"]
