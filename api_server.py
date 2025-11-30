from flask import Flask, jsonify
from database import Database
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Enable CORS for all routes
db = Database('complaints.db')

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "API server is running", "endpoints": ["/complaints"]})

@app.route('/complaints', methods=['GET'])
def get_complaints():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints")
    complaints = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(complaints)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
