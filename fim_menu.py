import os
import sys
import time    
import threading
import urllib.request
import urllib.error
import fim_core
from fim_db import FimDatabase
from fim_config import load_config
from fim_alert import AlertManager
from fim_utils import get_text_diff
import subprocess
import threading
import urllib.request

REQUIRED_MODULES = {
    'flask': 'flask',
    'watchdog.observers': 'watchdog',
    'yaml': 'PyYAML',
    'fim_core': None,          # our own modules – not in requirements
    'fim_db': None,
    'fim_config': None,
    'fim_alert': None,
    'fim_utils': None,
}

missing = []
for mod, pip_name in REQUIRED_MODULES.items():
    try:
        __import__(mod)
    except ImportError:
        if pip_name:
            missing.append(pip_name)

if missing:
    print("Some required packages are missing:")
    for m in missing:
        print(f"  - {m}")
    print()
    choice = input("Do you want to install them now? (y/n): ").strip().lower()
    if choice == 'y':
        # Use the same Python interpreter we're running on
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Installation finished. Please restart the menu.\n")
        sys.exit(0)
    else:
        print("Cannot run without required packages. Exiting.")
        sys.exit(1)


WHITE = '\033[1;37m'   
NC    = '\033[0m'      

# dashboard globals 
dashboard_thread = None
dashboard_port = 5050


def clear_screen():
    """Clear the terminal cross‑platform."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    """Display the FIM ASCII art banner in white."""
    clear_screen()
    print(WHITE)
    banner = r"""
     ███████╗ ██╗ ███╗   ███╗
     ██╔════╝ ██║ ████╗ ████║
     █████╗   ██║ ██╔████╔██║
     ██╔══╝   ██║ ██║╚██╔╝██║
     ██║      ██║ ██║ ╚═╝ ██║
     ╚═╝      ╚═╝ ╚═╝     ╚═╝
    FILE INTEGRITY MONITOR (FIM)
    """
    print(banner)
    print(NC)
def stop_dashboard():
    global dashboard_thread
    if dashboard_thread and dashboard_thread.is_alive():
        try:
            # Call the shutdown endpoint using urllib
            req = urllib.request.Request(
                f"http://localhost:{dashboard_port}/shutdown",
                data=b'{}',
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass
        dashboard_thread.join(timeout=3)
        dashboard_thread = None
        print("Dashboard stopped.")
    else:
        print("Dashboard is not running.")


def menu():
    global dashboard_thread

    # Show the banner once when the menu starts
    show_banner()
    print("\n" + "*" * 50)
    while True:
        print("1. Init Baseline")
        print("2. Check Integrity (one-time)")
        print("3. Start Daemon (background)")
        print("4. Show API usage examples. If you want to view it start daemon server and run Api_test.py file")
        print("5. View recent change log (last 20 events)")
        print(f"6. {'Stop' if dashboard_thread and dashboard_thread.is_alive() else 'Start'} Web Dashboard")
        print("7. Send Test Alert")
        print("8. Compute File Diff")
        print("9. Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            d = input("Directory to baseline [press Enter for config default]: ").strip()
            if not d:
                config = load_config()
                d = config['monitor_dir']
            if not os.path.isdir(d):
                print("Invalid directory.")
                continue
            hashes = fim_core.get_all_files_hashes(d)
            path = os.path.join(d, "baseline.json")
            fim_core.save_baseline(hashes, path)
            print(f"Baseline saved to {path} ({len(hashes)} files)")

        elif choice == "2":
            d = input("Directory to check [press Enter for config default]: ").strip()
            if not d:
                config = load_config()
                d = config['monitor_dir']
            base_path = os.path.join(d, "baseline.json")
            if not os.path.isfile(base_path):
                print(f"No baseline found at {base_path}. Run 'Init Baseline' first.")
                continue

            print("\n  Scanning directory, please wait...")
            old = fim_core.load_baseline(base_path)
            new = fim_core.get_all_files_hashes(d)
            report, counts = fim_core.detailed_compare(old, new)

            # ANSI colour codes (safe fallback if terminal doesn't support them)
            RED    = '\033[91m'
            GREEN  = '\033[92m'
            YELLOW = '\033[93m'
            BLUE   = '\033[94m'
            BOLD   = '\033[1m'
            NC     = '\033[0m'

            # Header
            print("\n" + BLUE + BOLD + "=" * 90)
            print(f"  INTEGRITY CHECK REPORT  |  {d}")
            print("=" * 90 + NC)

            # Summary cards
            print(f"  {GREEN}Unchanged{NC}: {counts.get('unchanged', 0):<5}  "
                  f"{RED}New{NC}: {counts['new']:<5}  "
                  f"{RED}Deleted{NC}: {counts['deleted']:<5}  "
                  f"{YELLOW}Modified{NC}: {counts['modified']:<5}  "
                  f"Total baseline: {len(old):<5}  Current scan: {len(new)}")
            print("-" * 90)

            # Column headers
            col1_w = 12   # Status
            col2_w = 42   # File path
            col3_w = 14   # Old hash (first 12)
            col4_w = 14   # New hash (first 12)

            header_line = f"  {'Status':<{col1_w}} {'File':<{col2_w}} {'Old Hash':<{col3_w}} {'New Hash':<{col4_w}}"
            print(header_line)
            print("-" * 90)

            # Row for each file
            for item in report:
                status = item['status'].upper()
                path = item['path']
                old_hash_short = item['old_hash'][:12] if item['old_hash'] else 'N/A'
                new_hash_short = item['new_hash'][:12] if item['new_hash'] else 'N/A'

                # Choose colour based on status
                if status == 'UNCHANGED':
                    colour = GREEN
                elif status == 'NEW':
                    colour = RED
                elif status == 'DELETED':
                    colour = RED
                else:  # MODIFIED
                    colour = YELLOW

                # Truncate file path if too long, but keep it aligned
                if len(path) > col2_w:
                    display_path = path[:col2_w-3] + "..."
                else:
                    display_path = path

                row = f"  {colour}{status:<{col1_w}}{NC} {display_path:<{col2_w}} {old_hash_short:<{col3_w}} {new_hash_short:<{col4_w}}"
                print(row)

            print("-" * 90 + "\n")

        elif choice == "3":
            print("Starting daemon in background...")
            from fim_daemon import start_daemon
            t = threading.Thread(target=start_daemon, daemon=True)
            t.start()
            time.sleep(1)  # Give daemon a moment to start
            print("Daemon is running in background.")
            print("File changes will appear here.")
            print("You can now use the menu normally.")

        elif choice == "4":
            print("\n--- Remote verification examples ---")
            print("1. Health:")
            print("   curl.exe http://localhost:5000/health")
            print("2. Fetch all hashes:")
            print("   curl.exe http://localhost:5000/hashes")
            print("3. Single file hash:")
            print("   curl.exe \"http://localhost:5000/hash?path=ahha.txt\"")
            print("4. Compare baseline (run from folder containing baseline.json):")
            print("   python -c \"import urllib.request,json;data=json.load(open('baseline.json','r'));req=urllib.request.Request('http://localhost:5000/check',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'},method='POST');print(json.loads(urllib.request.urlopen(req).read()))\"")
       
        elif choice == "5":
            config = load_config()
            db_path = config.get('database', {}).get('path', 'fim_events.db')
            if not os.path.exists(db_path):
                print("No event database found. Start the daemon first.")
                continue
            db = FimDatabase(db_path)
            events = db.get_events(20)
            if not events:
                print("No events recorded yet.")
            else:
                print(f"\nLast {len(events)} events:")
                print("-" * 80)
                for ev in events:
                    print(f"{ev[0]} | {ev[1]:8} | {ev[2]}")
                print("-" * 80)

        elif choice == "6":
            if dashboard_thread and dashboard_thread.is_alive():
                stop_dashboard()
            else:
                print("Starting web dashboard...")
                try:
                    from fim_dashboard import create_dashboard
                    app = create_dashboard()
                    dashboard_thread = threading.Thread(
                        target=lambda: app.run(host="0.0.0.0", port=dashboard_port,
                                               debug=False, use_reloader=False),
                        daemon=True
                    )
                    dashboard_thread.start()
                    print(f"Dashboard running at http://localhost:{dashboard_port}")
                    print("You can continue using the menu. Choose 6 again to stop the dashboard.")
                except Exception as e:
                    print(f"Dashboard error: {e}")
                    print("Start the daemon first (option 3) to initialize the database.")
        elif choice == "7":
            config = load_config()
            email_cfg = config.get('alerts', {}).get('email', {})
            syslog_enabled = config.get('alerts', {}).get('syslog', False)

            print("\n--- Alert Configuration ---")
            if syslog_enabled:
                print("Syslog: ENABLED → alerts will be written to local syslog.")
            if email_cfg.get('enabled', False):
                print("Email: ENABLED")
                print(f"  SMTP server: {email_cfg.get('smtp_server')}:{email_cfg.get('smtp_port')}")
                print(f"  From: {email_cfg.get('from_addr')}")
                print(f"  To:   {email_cfg.get('to_addr')}")
            if not syslog_enabled and not email_cfg.get('enabled', False):
                print("No alert methods enabled. Enable syslog or email in config.yaml.")
                continue

            msg = input("Enter alert message (or press Enter for default test): ").strip()
            if not msg:
                msg = "FIM manual test alert – sent from menu option 7."
            print("Sending alert...")
            mgr = AlertManager(config)
            print(f"[LOCAL COPY] {msg}")
            mgr.send_alert(msg, "MANUAL_TEST")
            print("Alert sent. Verify via email inbox or syslog.")

        elif choice == "8":
            file1 = input("Path to the original (old) file: ").strip()
            file2 = input("Path to the new (modified) file: ").strip()
            if not os.path.isfile(file1) or not os.path.isfile(file2):
                print("One or both files do not exist.")
                continue
            try:
                diff_output = get_text_diff(file1, file2)
                if not diff_output:
                    print("Files are identical or diff could not be generated.")
                else:
                    print("\n--- Diff ---")
                    print(diff_output)
            except Exception as e:
                print(f"Error computing diff: {e}")

        elif choice == "9":
            print("Goodbye.Thank you for using FIM. ")
            sys.exit(0)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\nCtrl+C detected.")
        if dashboard_thread and dashboard_thread.is_alive():
            print("The dashboard is still running.")
            a = input("Stop the dashboard and return to menu? (y/n): ").strip().lower()
            if a == 'y':
                stop_dashboard()
                print("Dashboard stopped. Returning to menu...")
                menu()   # restart the menu
            else:
                print("Exiting.")
                sys.exit(0)
        else:
            print("Exiting.")
            sys.exit(0)


