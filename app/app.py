import os
from flask import Flask, render_template, jsonify, request
from quickwit_client import QuickwitClient
import logging

app = Flask(__name__)

# Configuration
QUICKWIT_URL = os.getenv('QUICKWIT_URL', 'http://localhost:7280/')
DEFAULT_INDEX = 'pokemon'
DEFAULT_MAX_HITS = 20
DEBUG_MODE = os.getenv('DEBUG_MODE', False)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
# Initialize client
try:
    client = QuickwitClient(QUICKWIT_URL)
except Exception as e:
    app.logger.error(f"Failed to initialize QuickwitClient: {e}")
    client = None


@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search_endpoint():
    """Handle search requests and return formatted results."""
    # Get JSON data from the request
    data = request.get_json()
    app.logger.debug(f"Search request received: {data}")

    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    raw_query = data.get('query', '').strip()
    indexes = data.get('indexes', [DEFAULT_INDEX])
    max_hits = data.get('max_hits', DEFAULT_MAX_HITS)

    if not raw_query:
        return jsonify({'results': [], 'total': 0})

    try:
        search_query = raw_query
        app.logger.debug(f"Search query: {search_query}")

        all_results = []
        total_hits = 0

        # Search each selected index
        for index_id in indexes:
            response = client.search(
                index_id=index_id,
                query=search_query,
                max_hits=max_hits
            )

            # Process results - extract the nested 'documents' object
            if response and 'hits' in response:
                for hit in response['hits']:
                    # The actual Pokemon data is inside 'documents', not 'document'
                    if 'documents' in hit:
                        all_results.append(hit['documents'])
                    else:
                        all_results.append(hit)

                total_hits += response.get('num_hits', 0)

        app.logger.debug(f"Found {total_hits} results")
        if all_results:
            app.logger.debug(f"First result structure: {all_results[0]}")

        return jsonify({
            'query': raw_query,
            'indexes': indexes,
            'results': all_results,
            'total': total_hits
        })
    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/indexes')
def list_indexes():
    """Retrieve and return available indexes."""
    try:
        if not client:
            return jsonify({'error': 'QuickwitClient not initialized'}), 500

        # Get all indexes
        response = client.list_indexes()

        # Return formatted index information
        indexes = []
        for index in response:
            index_config = index.get('index_config', {})
            index_id = index_config.get('index_id', 'Unknown')
            indexes.append({
                'id': index_id,
                'description': index_config.get('search_settings', {}).get('default_search_fields', [])
            })

        return jsonify(indexes)
    except Exception as e:
        app.logger.error(f"Error listing indexes: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the application with debug mode from environment
    app.run(host='0.0.0.0', port=int(
        os.getenv('PORT', 5000)), debug=DEBUG_MODE)
