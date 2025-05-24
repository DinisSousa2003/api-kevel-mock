# Use official Python image
FROM python:3.10.8-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY ./app /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Run FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
