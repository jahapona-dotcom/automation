FROM python:3.10-slim

# Install Chromium and Chromium Driver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement file & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose Port
EXPOSE 5000

# Start Gunicorn server
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]