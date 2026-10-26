# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app


# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .


RUN mkdir -p /app/data

EXPOSE 5000 5050

CMD ["python", "fim_menu.py"]
