from quickwit_client import QuickwitClient
import os
from flask import Flask, render_template, jsonify, request
# Now you can import your modules


app = Flask(__name__)

quickwit_url = os.getenv('dst_url', 'http://localhost:7280/')
client = QuickwitClient(quickwit_url)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search_endpoint():
    # Get JSON data from the request
    data = request.get_json()
    app.logger.debug(f"Search request received: {data}")
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    raw_query = data.get('query', '').strip()

    # Get indexes from request or use pokemon as fallback
    indexes = data.get('indexes', ['pokemon'])
    max_hits = data.get('max_hits', 20)

    if not raw_query:
        return jsonify({'results': []})

    try:
        # Transform to _all_text search if needed
        if ':' not in raw_query:
            search_query = f'documents.name:{raw_query}'
        else:
            search_query = raw_query

        all_results = []
        total_hits = 0
        app.logger.debug(f"Transformed query: {search_query}")
        # Search each selected index
        for index_id in indexes:
            response = client.search(
                index_id=index_id,
                query=search_query,
                max_hits=max_hits
            )
            app.logger.debug(f"Raw response from Quickwit: {response}")
            # Process results
            if response and 'hits' in response:
                for hit in response['hits']:
                    doc = hit.get('document', {})
                    doc['_index'] = index_id  # Add index name to each result
                    all_results.append(doc)

                total_hits += response.get('num_hits', 0)

        return jsonify({
            'query': raw_query,
            'indexes': indexes,
            'results': all_results,
            'total': total_hits
        })
        app.logger.debug(f"Returning {len(all_results)} results")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/indexes')
def list_indexes():
    try:
        # Get all indexes
        response = client.list_indexes()

        # Return formatted index information
        indexes = []
        for index in response:
            # Extract the correct fields from the nested structure
            index_config = index.get('index_config', {})
            index_id = index_config.get('index_id', 'Unknown')
            indexes.append({
                'id': index_id,
                'description': index_config.get('search_settings', {}).get('default_search_fields', [])
            })

        return jsonify(indexes)
    except Exception as e:
        print(f"Error listing indexes: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
