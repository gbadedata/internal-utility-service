from flask import Flask, jsonify
from database import get_users
import config

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "message": "Internal Utility Service Running",
        "environment": config.ENVIRONMENT,
        "db_host": config.DB_HOST  #leaking config info
    })

@app.route("/users")
def users():
    return jsonify(get_users())

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  #debug mode ON
