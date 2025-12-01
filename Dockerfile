FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pandoc \
    curl \
    git \
    # WeasyPrint dependencies (Pango, Fontconfig, Cairo)
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @mermaid-js/mermaid-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt ./
COPY tools/pdf/requirements-pdf.txt ./requirements-pdf.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-pdf.txt

# Install Playwright and Chromium browser
RUN pip install playwright>=1.40.0 \
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

