# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server file
COPY server.py .

# Expose the port the app runs on
EXPOSE 8000

# Set environment variable for BudgetKey API base URL
ENV BUDGETKEY_API_BASE=https://next.obudget.org

# Run the server
CMD ["fastmcp", "run", "server.py", "--transport", "http", "--no-banner", "--host", "0.0.0.0", "--port", "8000"]
