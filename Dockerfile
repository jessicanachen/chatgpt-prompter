# Use an official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Run both FastAPI and Bot via a startup script or command
CMD ["bash", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & python run_bot.py"]
