# Use official Python image
FROM python:3.10-slim

# Install system dependencies, including Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for headless Chrome
ENV CHROME_BIN=/usr/bin/google-chrome-stable \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install
COPY requirements_bot.txt .
RUN pip install --no-cache-dir -r requirements_bot.txt

# Copy project files
COPY . .

# Run start script
CMD ["sh", "start.sh"]
