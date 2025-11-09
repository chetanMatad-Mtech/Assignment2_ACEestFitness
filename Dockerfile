# Use an official lightweight Python image
FROM python:3.9-slim

# Set working directory inside container
WORKDIR /app

# Copy all project files into container
COPY . /app

# Install dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Expose Flask default port
EXPOSE 8080

# Set environment variables for Flask
ENV FLASK_APP=application.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Command to run Flask app
CMD ["python", "Application.py"]

