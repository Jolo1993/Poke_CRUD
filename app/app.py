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


@app.route('/search')
def search_endpoint():
    # Get query and selected indexes
    raw_query = request.args.get('query', '').strip()
    indexes = request.args.getlist('index') or ['pokemon']

    if not raw_query:
        return jsonify({'results': []})

    try:
        # Transform to _all_text search
        search_query = f'_all_text:{raw_query}'

        all_results = []
        total_hits = 0

        # Search each selected index
        for index_id in indexes:
            response = client.search(
                index_id=index_id,
                query=search_query,
                max_hits=20
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

        # Debug the actual structure
        # print(f"Type of response: {type(response)}")
        # print(f"Response content: {response}")

        # Handle different possible structures
        if isinstance(response, dict) and 'indexes' in response:
            indexes_data = response['indexes']
        elif isinstance(response, list):
            indexes_data = response
        else:
            # If unexpected structure, return what we found
            return jsonify({
                'error': 'Unexpected response structure',
                'response_type': str(type(response)),
                'response': response
            }), 500

        # Return formatted index information
        indexes = []
        for index in indexes_data:
            # Safely access data with .get()
            indexes.append({
                'id': index.get('index_id'),
                'doc_count': index.get('num_docs', 0),
                'description': index.get('metadata', {}).get('description', '') if index.get('metadata') else '',
                'created': index.get('created_at')
            })

        return jsonify(indexes)
    except Exception as e:
        print(f"Error listing indexes: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
