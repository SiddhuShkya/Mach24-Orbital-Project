# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose Streamlit port
EXPOSE 8050

# Run Streamlit
CMD ["streamlit", "run", "src/main.py", "--server.port=8050", "--server.address=0.0.0.0", "--server.headless=true"]
