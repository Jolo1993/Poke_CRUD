#!/usr/bin/env python3
"""
Pokemon Data Loader for Quickwit
Fetches Pokemon data from PokeAPI and indexes it in Quickwit.
"""
import json
import logging
import os
import time
import traceback
from typing import Dict, Optional, Tuple, Any
import requests
import yaml
from quickwit_client import QuickwitClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables with defaults
QUICKWIT_URL = os.getenv('QUICKWIT_URL', 'http://localhost:7280/')
POKEMON_API_URL = os.getenv(
    'DATA_URL', 'https://pokeapi.co/api/v2/pokemon').rstrip('/')
DEFAULT_INDEX_NAME = os.getenv('INDEX_NAME', 'pokemon')
POKEMON_AMOUNT = int(os.getenv('POKEMON', '10'))
SCHEMA_PATH = "schema.json"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


def get_index_name() -> str:
    """Get index name from environment variable."""
    return os.environ.get("INDEX_NAME", DEFAULT_INDEX_NAME)


def load_schema(schema_path: str) -> Optional[Dict[str, Any]]:
    """
    Load schema file and extract index_id.

    Args:
        schema_path: Path to schema file (JSON or YAML)

    Returns:
        Dict containing the schema or None if loading fails
    """
    try:
        _, ext = os.path.splitext(schema_path)
        with open(schema_path, 'r') as file:
            if ext.lower() in ['.yaml', '.yml']:
                schema = yaml.safe_load(file)
            else:
                schema = json.load(file)

        # Extract index_id from schema
        index_id = schema.get("index_id")
        if not index_id:
            logger.error("No index_id found in schema file")
            return None

        return schema
    except Exception as e:
        logger.error(f"Error loading schema: {type(e).__name__}: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        return None


def validate_version(schema: Optional[Dict[str, Any]], env_index_name: Optional[str] = None) -> bool:
    """
    Validate that schema version matches environment.

    Args:
        schema: The loaded schema dictionary
        env_index_name: The expected index name

    Returns:
        True if version is valid, False otherwise
    """
    if not schema:
        return False

    if not env_index_name:
        env_index_name = get_index_name()

    schema_index_id = schema.get("index_id")

    if schema_index_id != env_index_name:
        logger.warning(
            f"Version mismatch - Schema index_id '{schema_index_id}' "
            f"doesn't match environment '{env_index_name}'"
        )
        return False

    return True


def check_index(schema_path: str, dst_url: str = QUICKWIT_URL) -> Tuple[bool, bool]:
    """
    Check if index exists and validate schema version.

    Args:
        schema_path: Path to schema file
        dst_url: Quickwit server URL

    Returns:
        tuple: (index_exists, version_valid)
    """
    # Load and validate schema
    schema = load_schema(schema_path)
    if not schema:
        return False, False

    env_index_name = get_index_name()
    version_valid = validate_version(schema, env_index_name)

    # Check if index exists
    try:
        client = QuickwitClient(base_url=dst_url)
        response = client.get_index(env_index_name)
        index_exists = response is not None

        logger.info(f"Index '{env_index_name}' {
                    'exists' if index_exists else 'does not exist'}")

        if index_exists and not version_valid:
            logger.warning(
                "Using existing index but version doesn't match schema!")

        return index_exists, version_valid
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.info(f"Index '{env_index_name}' does not exist")
            return False, version_valid
        # Re-raise other HTTP errors
        logger.error(f"Error checking index: {e}")
        return False, version_valid
    except Exception as e:
        logger.error(f"Error checking index: {type(e).__name__}: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        return False, version_valid


def create_index(schema_path: str, dst_url: str = QUICKWIT_URL, force: bool = False) -> bool:
    """
    Create index from schema file with version validation.

    Args:
        schema_path: Path to schema file
        dst_url: Quickwit server URL
        force: If True, create even if versions don't match

    Returns:
        bool: True if creation was successful
    """
    # Load schema
    schema = load_schema(schema_path)
    if not schema:
        return False

    # Validate version
    env_index_name = get_index_name()
    version_valid = validate_version(schema, env_index_name)

    if not version_valid and not force:
        logger.error(
            f"Version mismatch - Schema uses '{schema.get('index_id')}' but "
            f"environment expects '{
                env_index_name}'. Use force=True to override this check."
        )
        return False

    # Create index
    try:
        client = QuickwitClient(base_url=dst_url)
        client.create_index(schema)
        logger.info(f"Successfully created index '{schema.get('index_id')}'")
        return True
    except Exception as e:
        logger.error(f"Error creating index: {type(e).__name__}: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        return False


def fetch_data(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch data from the given URL with proper headers.

    Args:
        url: The URL to fetch data from

    Returns:
        Dict containing the JSON response or None if fetch fails

    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()

    logger.debug(f"Response error: {response.text[:100]}...")
    response.raise_for_status()
    return None


def upload_data(index_name: str, data: Dict[str, Any]) -> bool:
    """
    Upload data to Quickwit index.

    Args:
        index_name: Name of the index to upload to
        data: Data to upload

    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        client = QuickwitClient(base_url=QUICKWIT_URL)
        client.ingest(index_name, data)
        return True
    except Exception as e:
        logger.error(f"Error during upload: {type(e).__name__}: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        return False


def fetch_and_load_pokemon(pokemon_id: int, index_name: str) -> bool:
    """
    Fetch Pokemon data and load it into the index.

    Args:
        pokemon_id: Pokemon ID to fetch
        index_name: Index to load data into

    Returns:
        bool: True if successful, False otherwise
    """
    pokemon_url = f"{POKEMON_API_URL}/{pokemon_id}"

    # API request with retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            data = fetch_data(pokemon_url)

            if not data:
                logger.warning(f"No data received for Pokemon #{pokemon_id}")
                return False

            logger.info(f"Processing Pokemon #{pokemon_id}: {
                        data.get('name', 'unknown')}")
            if upload_data(index_name, data):
                logger.info(f"Successfully loaded Pokemon #{pokemon_id}")
                return True
            else:
                logger.error(f"Failed to upload Pokemon #{pokemon_id}")
                return False

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(
                    f"Pokemon #{pokemon_id} not found - we've reached the end")
                return False
            elif attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Request failed, retrying in {
                               wait_time}s... ({e})")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP Error after {max_retries} attempts: {e}")
                return False
        except Exception as e:
            logger.error(f"Error processing Pokemon #{pokemon_id}: {e}")
            return False

    return False


def main() -> None:
    """Main function to orchestrate the Pokemon data loading process."""
    index_name = get_index_name()

    logger.info(f"Starting Pokemon loader with source: {POKEMON_API_URL}")
    logger.info(f"Index name: {index_name}")
    logger.info(f"Destination URL: {QUICKWIT_URL}")

    # Check and create index if needed
    index_exists, version_valid = check_index(SCHEMA_PATH, QUICKWIT_URL)

    if not index_exists:
        logger.info(f"Index '{index_name}' doesn't exist, creating...")
        if not create_index(SCHEMA_PATH, QUICKWIT_URL):
            logger.error("Failed to create index. Aborting data load.")
            return
        logger.info(f"Successfully created index '{index_name}'")
    elif not version_valid:
        logger.warning(
            f"Index '{index_name}' exists but version mismatch detected!")
        logger.warning(
            "Continuing with existing index despite version mismatch...")
    else:
        logger.info(f"Using existing index '{index_name}'")

    # Load Pokemon data
    pokemon_id = 1
    successful_loads = 0

    while pokemon_id <= POKEMON_AMOUNT:
        if fetch_and_load_pokemon(pokemon_id, index_name):
            successful_loads += 1
        else:
            # If we get a 404, we might have reached the end of available Pokemon
            if pokemon_id > 1:  # Only break if we've successfully loaded at least one
                break

        # Rate limiting - be nice to the API
        time.sleep(1)
        pokemon_id += 1

    logger.info(f"Pokemon loading complete. Loaded {
                successful_loads} Pokemon.")


if __name__ == "__main__":
    main()
