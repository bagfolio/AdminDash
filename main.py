from app import app  # noqa: F401
from routes import register_routes
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Register all routes
register_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
