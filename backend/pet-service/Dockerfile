# Multi-stage Dockerfile for Pet Service API
# Optimized for Azure deployment with minimal size and security

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for Azure SDK compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 msuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/msuser/.local

# Copy application code
COPY --chown=msuser:msuser . .

# Switch to non-root user
USER msuser

# Make sure scripts are in PATH
ENV PATH=/home/msuser/.local/bin:$PATH

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Default environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]