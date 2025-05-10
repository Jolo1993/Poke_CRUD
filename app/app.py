from quickwit_client import QuickwitClient
import os
from flask import Flask, render_template, jsonify, request
# Now you can import your modules


app = Flask(__name__)

quickwit_url = os.getenv('dst_url', 'http://localhost:7280/')
index_id = os.getenv('index_name', 'pokemon')
client = QuickwitClient(quickwit_url)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search_endpoint():
    # Handle POST request with JSON payload
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    raw_query = data.get('query', '').strip()
    indexes = data.get('indexes', ['pokemon'])
    max_hits = data.get('max_hits', 20)

    if not raw_query:
        return jsonify({'results': []})

    try:
        # Transform to _all_text search if needed
        if ':' not in raw_query:
            search_query = f'_all_text:{raw_query}'
        else:
            search_query = raw_query  # Keep as-is if it already has field:value format

        all_results = []
        total_hits = 0

        # Search each selected index
        for index_id in indexes:
            try:
                # Use your client's search method directly
                response = client.search(
                    index_id=index_id,
                    query=search_query,
                    max_hits=max_hits
                )

                # Process results from this index
                index_results = []
                for hit in response.get('hits', []):
                    # Extract document (handle nested structure if needed)
                    if 'documents' in hit.get('document', {}):
                        doc = hit['document']['documents']
                    else:
                        doc = hit['document']

                    # Add index info to result
                    doc['_index'] = index_id
                    index_results.append(doc)

                # Add to combined results
                all_results.extend(index_results)
                total_hits += response.get('num_hits', 0)

            except Exception as index_error:
                print(f"Error searching index {index_id}: {str(index_error)}")
                # Continue with other indexes if one fails

        return jsonify({
            'query': raw_query,
            'indexes': indexes,
            'results': all_results,
            'total': total_hits
        })

    except Exception as e:
        print(f"Search error: {str(e)}")
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

            # Get checkpoint info (might indicate number of docs)
            checkpoint = index.get('checkpoint', {})
            # Rough approximation of doc count based on checkpoint
            doc_count = sum(1 for cp in checkpoint.values() if cp)

            indexes.append({
                'id': index_id,
                'doc_count': doc_count,
                'description': index_config.get('search_settings', {}).get('default_search_fields', [])
            })

        return jsonify(indexes)
    except Exception as e:
        print(f"Error listing indexes: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
