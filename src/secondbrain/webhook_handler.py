from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def handle_webhook(event):
    try:
        logger.info(f"Received webhook event: {event}")
        # Your existing webhook handling logic here
    except Exception as e:
        logger.error(f"Error handling webhook event: {e}", exc_info=True)
        raise

@app.route('/webhook', methods=['POST'])
def webhook():
    # ...existing webhook code...
    return jsonify({"status": "success"}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)