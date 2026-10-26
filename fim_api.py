from flask import Flask, request, jsonify
import fim_core
from functools import wraps

def create_api(store, db=None, api_token=None):
    app = Flask(__name__)

    def require_token(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if api_token:
                token = request.headers.get('Authorization', '').replace('Bearer ', '')
                if token != api_token:
                    return jsonify({"error": "Unauthorized"}), 401
            return f(*args, **kwargs)
        return decorated

    @app.route('/hashes', methods=['GET'])
    @require_token
    def get_hashes():
        return jsonify(store.get_all())

    @app.route('/hash', methods=['GET'])
    @require_token
    def get_single_hash():
        path = request.args.get('path')
        if not path:
            return jsonify({"error": "Missing 'path' parameter"}), 400
        current = store.get_all()
        if path in current:
            return jsonify({path: current[path]})
        return jsonify({"error": "File not found"}), 404

    @app.route('/check', methods=['POST'])
    @require_token
    def check_baseline():
        baseline = request.get_json()
        if not baseline:
            return jsonify({"error": "Invalid JSON"}), 400
        current = store.get_all()
        diff = fim_core.compare_baselines(baseline, current)
        return jsonify(diff)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "running", "count": len(store.get_all())})

    @app.route('/history', methods=['GET'])
    @require_token
    def get_history():
        if not db:
            return jsonify({"error": "Database not enabled"}), 503
        limit = request.args.get('limit', 50)
        try:
            limit = int(limit)
        except ValueError:
            limit = 50
        rows = db.get_events(limit)
        events = []
        for row in rows:
            events.append({
                "timestamp": row[0],
                "event": row[1],
                "file": row[2],
                "old_hash": row[3],
                "new_hash": row[4],
                "diff": row[5]
            })
        return jsonify(events)

    return app