import os
import threading
import time
from pathlib import Path
from watchdog.observers import Observer
from fim_watchdog import FIMEventHandler, initial_scan
from fim_api import create_api
from fim_db import FimDatabase
from fim_alert import AlertManager
from fim_config import load_config
import logging

# Using logging to ignore werkzeug messages
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


# Daemon function defined
def start_daemon(config_path="config.yaml"):
    config = load_config(config_path)
    raw_dir = config['monitor_dir']
    root_dir = str(Path(raw_dir).resolve())

    # Remove trailing backslash/slash if present
    root_dir = root_dir.rstrip("\\/")

    print(f"[*] Monitor directory: {root_dir}")
    if not os.path.isdir(root_dir):
        print(f"[!] ERROR: Directory does not exist: {root_dir}")
        return

    store = initial_scan(root_dir)
    print(f"[*] Watching {len(store.get_all())} files in real time.")

    db_path = config.get('database', {}).get('path', 'fim_events.db')
    db = FimDatabase(db_path)
    alert = AlertManager(config)

    event_handler = FIMEventHandler(
        store, root_dir, db, alert,
        diff_enabled=config.get('diff', {}).get('enabled', True),
        max_diff_size=config.get('diff', {}).get('max_size_kb', 1024) * 1024
    )

    # Start observer
    observer = Observer()
    try:
        observer.schedule(event_handler, root_dir, recursive=True)
        observer.start()
    except Exception as e:
        print(f"[!] Failed to start file observer: {e}")
        print("    Check that the directory exists and you have read permissions.")
        return

    # API integration
    api_token = os.environ.get('FIM_API_TOKEN', config.get('api', {}).get('token', ''))
    api = create_api(store, db, api_token)

    # SSL context (if enabled)
    context = None
    if config.get('api', {}).get('ssl', False):
        import ssl
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('cert.pem', 'key.pem')

    # Thread to run the API server
    api_thread = threading.Thread(
        target=lambda: api.run(
            host=config['api'].get('host', '0.0.0.0'),
            port=config['api'].get('port', 5000),
            debug=True,
            use_reloader=False,
            ssl_context=context
        ),
        daemon=True
    )
    api_thread.start()

    # Status messages
    print(f"[*] Daemon active. API on http://{config['api'].get('host', '0.0.0.0')}:{config['api'].get('port', 5000)}")
    print("[*] File changes will appear below.")
    print()

    # Keep the daemon running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        print("[*] Daemon stopped.")