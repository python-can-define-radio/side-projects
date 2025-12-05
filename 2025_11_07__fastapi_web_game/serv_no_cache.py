from pathlib import Path
from flask import Flask, send_from_directory, make_response

app = Flask(__name__)
# Define the directory where your files are located (current working directory)
ROOT_DIR = Path(__file__).parent

@app.route('/<path:filename>')
def serve_files(filename):
    """Serve files from the root directory and add no-cache header."""
    response = make_response(send_from_directory(ROOT_DIR, filename))
    response.headers['Cache-Control'] = 'no-cache'
    # response.headers['Pragma'] = 'no-cache' # For compatibility
    # response.headers['Expires'] = '0'       # For compatibility
    return response

@app.route('/')
def serve_index():
    """Serve index.html specifically for the homepage request."""
    response = make_response(send_from_directory(ROOT_DIR, 'index.html'))
    response.headers['Cache-Control'] = 'no-cache'
    # response.headers['Pragma'] = 'no-cache'
    # response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    # Running with Flask's development server (better than http.server)
    app.run(debug=True, port=8000)
