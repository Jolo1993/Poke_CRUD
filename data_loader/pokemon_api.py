import requests as req
import os
from quickwit_client import QuickwitClient
from typing import Dict
import time

# Environment variables with defaults
index = os.environ.get('index_name', 'pokemon_index')
dst_url = os.environ.get('dst_url', 'http://localhost:7280/api/v1')
src_url = os.environ.get('src_url', 'https://pokeapi.co/api/v2/pokemon')
pokemon_id = 1


def load(url):
    print(f"DEBUG: Making request to {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = req.get(url, headers=headers)
    print(f"DEBUG: Response status code: {response.status_code}")

    if response.status_code == 200:
        return response.json()
    else:
        print(f"DEBUG: Response error: {response.text[:100]}...")
        response.raise_for_status()


def upload_data(index_name, data):
    try:
        print(f"DEBUG: Initializing QuickwitClient with base_url={dst_url}")
        client = QuickwitClient(base_url=dst_url)

        print(f"DEBUG: Preparing to upload document to index: {index_name}")
        print(f"DEBUG: Document sample (first 100 chars): {
              str(data)[:100]}...")

        # Use ingest method instead of index_documents
        result = client.ingest(index_name, data)
        print(f"DEBUG: Upload completed with result: {result}")
        return True
    except Exception as e:
        print(f"ERROR during upload: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    src_url = src_url.rstrip('/')

    print(f"Starting Pokemon loader with source: {src_url}")
    print(f"Index name: {index}")
    print(f"Destination URL: {dst_url}")

    while True:
        pokemon_url = f"{src_url}/{pokemon_id}"
        try:
            # Manual test (optional)
            print(
                f"You can test this URL manually with: curl -s '{pokemon_url}' | head")

            # API request with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    data = load(pokemon_url)
                    break  # Success - exit retry loop
                except req.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"Request failed, retrying in {
                              wait_time}s... ({e})")
                        time.sleep(wait_time)
                    else:
                        raise  # Re-raise after all retries failed

            # Did we get data?
            if not data:
                print(f"No data received for Pokemon #{pokemon_id}")
                break

            # Upload
            print(f"Processing Pokemon #{pokemon_id}: {
                  data.get('name', 'unknown')}")
            upload_data(index, data)
            print(f"Successfully loaded Pokemon #{pokemon_id}")

            # Rate limiting - be nice to the API
            time.sleep(1)
        except req.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Pokemon #{
                      pokemon_id} not found - we've reached the end")
                break
            else:
                print(f"HTTP Error: {e}")
                break
        except Exception as e:
            print(f"Error: {e}")
            print(f"Current URL: {pokemon_url}")
            break

        # Next Pokemon
        pokemon_id += 1024
