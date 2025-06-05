# Use official Python image
FROM python:3.10.8-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /app

# Copy the rest of the application
COPY . .

# Expose Locust Web UI port
EXPOSE 8089
