# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies for pdf2image and tesseract
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create necessary directories
RUN mkdir -p data uploads models

# Expose the port the app runs on
EXPOSE 8080

# Define environment variable
ENV FLASK_APP=app.py
ENV PORT=8080

# Run the application
# Note: Using gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
