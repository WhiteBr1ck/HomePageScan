FROM python:3.11-slim

# Install Nmap and curl (for healthcheck)
RUN apt-get update && apt-get install -y nmap curl && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy App
COPY . .

# Create static dir for icons if not exists
RUN mkdir -p static/icons

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
