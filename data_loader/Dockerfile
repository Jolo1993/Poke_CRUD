FROM python:3.12-slim

WORKDIR /app

RUN addgroup -r appuser && useradd -r -g appuser appuser

ENV QUICKWIT_URL=http://localhost:7280
ENV DATA_URL=https://pokeapi.co/api/v2/pokemon
# Install dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy local library
COPY local_libs/ /local_libs/
RUN pip install -e /local_libs/

# Copy data loader code
COPY data_loader/ .
COPY schema.json .

USER appuser

# Run the application
CMD ["python", "pokemon_api.py"]

