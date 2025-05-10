FROM python:3.10-slim

ENV QUICKWIT_URL=http://localhost:7280



WORKDIR /app

# Install dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy local library
COPY local_libs/ /local_libs/
RUN pip install -e /local_libs/

# Copy data loader code
COPY data_loader/ .
COPY schema.json .

# Run the application
CMD ["python", "pokemon_api.py"]

