FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc and buffer outputs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PORT=5000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Initialize database and train models
RUN python database/seed.py
RUN python model/train_model.py

# Expose port
EXPOSE 5000

# Run production server
CMD ["python", "server_production.py"]
