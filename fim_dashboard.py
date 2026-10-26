from flask import Flask, render_template_string, request
from fim_db import FimDatabase
from fim_config import load_config
import logging

# Silence Flask's "Press CTRL+C to quit"
logging.getLogger('werkzeug').setLevel(logging.WARNING)

import os

def create_dashboard():
    config = load_config()
    db_path = config.get('database', {}).get('path', 'fim_events.db')
    
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Create empty database if it doesn't exist
    db = FimDatabase(db_path)

    app = Flask(__name__)

#geneatin the result in web by using html templates
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FIM Dashboard</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body { font-family: Arial; margin: 20px; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 100%; word-break: break-all; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .hash { font-family: monospace; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <h1>File Integrity Monitoring – Event Log</h1>
        <p>Total events: {{ count }}</p>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Event</th>
                <th>File</th>
                <th>Old Hash (full)</th>
                <th>New Hash (full)</th>
                <th>Details</th>
            </tr>
            {% for e in events %}
            <tr>
                <td>{{ e[0] }}</td>
                <td>{{ e[1] }}</td>
                <td>{{ e[2] }}</td>
                <td class="hash">{{ e[3] if e[3] else '' }}</td>
                <td class="hash">{{ e[4] if e[4] else '' }}</td>
                <td>{{ e[5] if e[5] else '' }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    @app.route('/')
    def index():
        rows = db.get_events(200)
        return render_template_string(html_template, events=rows, count=len(rows))

    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()
        return "Dashboard stopped."

    return app