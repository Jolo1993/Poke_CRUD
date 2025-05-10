FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy local library
COPY local_libs/ /local_libs/
RUN pip install -e /local_libs/

# Copy application code
COPY app/ .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]

