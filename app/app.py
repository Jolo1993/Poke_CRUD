from flask import Flask, render_template, jsonify
import requests
from quickwit_client import QuickwitClient
import os


app = Flask(__name__)

quickwit_url = os.getenv('dst_url', 'http://localhost:7280/')
index_id = os.getenv('index_name', 'pokemon')
client = QuickwitClient(quickwit_url)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search')
def search():
    query = requests.args.get('query', '')
    if not query:
        return jsonify({'results': []})

    try:
        response = QuickwitClient.search(index_id,
                                         query=query,
                                         max_hits=20
                                         )
        return jsonify({'results': response.hits})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
