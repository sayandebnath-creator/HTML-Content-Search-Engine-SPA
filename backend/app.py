from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import weaviate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from frontend

# Load model and connect to Weaviate
model = SentenceTransformer('all-MiniLM-L6-v2')
client = weaviate.Client("http://localhost:8080")

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    url = data.get('url')
    query = data.get('query')

    if not url or not query:
        return jsonify({"error": "Missing URL or query"}), 400

    try:
        html = requests.get(url, timeout=10).text
    except Exception as e:
        return jsonify({"error": f"Failed to fetch URL: {str(e)}"}), 500

    # Parse and clean HTML
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]): tag.extract()
    text = soup.get_text(separator=" ")
    text = ' '.join(text.split())  # Clean whitespace

    # Chunking (roughly 1000 characters per chunk)
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]

    # Reset schema
    try:
        client.schema.delete_all()
        class_obj = {
            "class": "HtmlChunk",
            "vectorizer": "none",
            "properties": [{"name": "content", "dataType": ["text"]}]
        }
        client.schema.create_class(class_obj)
    except Exception as e:
        return jsonify({"error": f"Failed to setup schema: {str(e)}"}), 500

    # Store chunks with embeddings
    for chunk in chunks:
        vector = model.encode(chunk).tolist()
        client.data_object.create({
            "content": chunk
        }, "HtmlChunk", vector=vector)

    # Query
    query_vector = model.encode(query).tolist()
    try:
        result = client.query.get("HtmlChunk", ["content"]) \
            .with_near_vector({"vector": query_vector}) \
            .with_limit(10).do()
        matches = result["data"]["Get"]["HtmlChunk"]
        return jsonify(matches)
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
