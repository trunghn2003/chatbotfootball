# Use a more complete Python image to avoid missing system libraries
FROM python:3.12

# Install system dependencies for Google Cloud libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc-dev \
    libffi-dev \
    libstdc++6 \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip to the latest version
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with verbose output
RUN pip install --no-cache-dir -r requirements.txt --verbose || { echo "Pip install failed"; exit 1; }

# Copy application code and .env file
COPY app.py .
COPY .env .

# Create directory for credentials that will be mounted at runtime
RUN mkdir -p /app/credentials

# Set environment variable to point to credentials path
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gg.json

# Expose port 5001
EXPOSE 5001

# Command to run the Flask app
CMD ["python", "app.py"]


# docker run -v /path/to/your/service-account-key.json:/app/credentials/service-account-key.json -p 5001:5001 your-image-name
