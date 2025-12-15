# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Install system dependencies (Tesseract and required libs)
# We use a combined command to keep the image smaller and avoid intermediate layers
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (Render handles port routing)
EXPOSE 10000

# Command to run the application using Gunicorn
# This replaces the Procfile for Docker builds
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]