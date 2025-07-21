from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import weaviate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

    # Step 1: Fetch and parse HTML
    try:
        html = requests.get(url, timeout=10).text
    except Exception as e:
        return jsonify({"error": f"Failed to fetch URL: {str(e)}"}), 500

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]): tag.extract()

    # Step 2: Extract meaningful content from the page (universal)
    seen_texts = set()
    chunks = []
    MIN_WORDS = 20
    SKIP_CLASSES = ['nav', 'menu', 'footer', 'header', 'sidebar', 'breadcrumb', 'social']

    for el in soup.find_all(['article', 'section', 'main', 'div', 'p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        # Skip layout components based on class names
        classes = ' '.join(el.get('class', [])).lower()
        if any(skip in classes for skip in SKIP_CLASSES):
            continue

        # Get clean text
        cleaned_text = ' '.join(el.get_text(separator=" ").split())
        raw_html = str(el)

        # Filter: length + uniqueness
        if len(cleaned_text.split()) >= MIN_WORDS and cleaned_text not in seen_texts:
            seen_texts.add(cleaned_text)
            chunks.append((cleaned_text, raw_html))

    # Handle case when no content is found
    if not chunks:
        return jsonify({"error": "No meaningful content found on page."}), 400


    # Step 3: Reset schema in Weaviate
    try:
        client.schema.delete_all()
        class_obj = {
            "class": "HtmlChunk",
            "vectorizer": "none",
            "properties": [
                {"name": "content", "dataType": ["text"]},
                {"name": "html", "dataType": ["text"]}
            ]
        }
        client.schema.create_class(class_obj)
    except Exception as e:
        return jsonify({"error": f"Failed to setup schema: {str(e)}"}), 500

    # Step 4: Store content with embeddings
    for content, html_block in chunks:
        vector = model.encode(content).tolist()
        client.data_object.create({
            "content": content,
            "html": html_block,
        }, "HtmlChunk", vector=vector)

    # Step 5: Query with vector similarity and certainty score
    query_vector = model.encode(query).tolist()

    try:
        result = client.query.get("HtmlChunk", ["content", "html"]) \
            .with_near_vector({"vector": query_vector}) \
            .with_additional(["certainty"]) \
            .with_limit(10).do()

        raw_matches = result["data"]["Get"]["HtmlChunk"]
        formatted = []

        for match in raw_matches:
            score = round(match["_additional"]["certainty"] * 100)
            formatted.append({
                "content": match["content"],
                "html": match["html"],
                "score": score
            })

        return jsonify(formatted)
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
