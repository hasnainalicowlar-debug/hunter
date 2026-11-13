import os
import sys
import webbrowser

# Set path to current directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from api.server import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    url = f"http://localhost:{port}"
    print("=" * 60)
    print("PAKISTAN FOOD BUSINESS & RESTAURANT POS PLATFORM")
    print("=" * 60)
    print(f"Server running at: {url}")
    print("Opening browser automatically...")
    print("Press CTRL+C in this terminal to stop the server.")
    print("=" * 60)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    app.run(host='0.0.0.0', port=port, debug=False)

