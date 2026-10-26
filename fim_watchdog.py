import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import fim_core
from fim_db import FimDatabase
from fim_alert import AlertManager


class HashStore:
    """Thread‑safe in‑memory store of file hashes."""

    def __init__(self):
        self._hashes = {}
        self._lock = threading.Lock()

    def update(self, rel_path: str, file_path: str):
        try:
            h = fim_core.compute_file_hash(file_path)
            with self._lock:
                self._hashes[rel_path] = h
        except RuntimeError:
            pass

    def remove(self, rel_path: str):
        with self._lock:
            self._hashes.pop(rel_path, None)

    def get_all(self):
        with self._lock:
            return dict(self._hashes)


class FIMEventHandler(FileSystemEventHandler):
    def __init__(self, store: HashStore, root_dir: str, db: FimDatabase,
                 alert: AlertManager, diff_enabled=True, max_diff_size=1024 * 1024):
        self.store = store
        self.root = Path(root_dir).resolve()
        self.db = db
        self.alert = alert
        self.diff_enabled = diff_enabled
        self.max_diff_size = max_diff_size

    def _rel(self, path: str) -> str:
        p = Path(path)
        if not p.is_absolute():
            p = self.root / p
        return str(p.relative_to(self.root))

    def on_created(self, event):
        if not event.is_directory:
            rel = self._rel(event.src_path)
            new_hash = fim_core.compute_file_hash(event.src_path)
            self.store._hashes[rel] = new_hash
            msg = f"[*] FILE CREATED: {rel}"
            print(msg)
            self.db.log_event("CREATED", rel, new_hash=new_hash)
            self.alert.send_alert(f"New file created: {rel}")

    def on_modified(self, event):
        if not event.is_directory:
            rel = self._rel(event.src_path)
            old_hash = self.store._hashes.get(rel, None)
            new_hash = fim_core.compute_file_hash(event.src_path)
            if old_hash != new_hash:
                self.store._hashes[rel] = new_hash
                msg = f"[*] FILE MODIFIED: {rel}"
                print(msg)
                self.db.log_event("MODIFIED", rel, old_hash=old_hash, new_hash=new_hash)
                self.alert.send_alert(f"File modified: {rel}")

    def on_deleted(self, event):
        if not event.is_directory:
            rel = self._rel(event.src_path)
            old_hash = self.store._hashes.pop(rel, None)
            msg = f"[*] FILE DELETED: {rel}"
            print(msg)
            self.db.log_event("DELETED", rel, old_hash=old_hash)
            self.alert.send_alert(f"File deleted: {rel}")

    def on_moved(self, event):
        if not event.is_directory:
            src_rel = self._rel(event.src_path)
            dest_rel = self._rel(event.dest_path)
            old_hash = self.store._hashes.pop(src_rel, None)
            new_hash = fim_core.compute_file_hash(event.dest_path)
            self.store._hashes[dest_rel] = new_hash
            msg = f"[*] FILE RENAMED: {src_rel} -> {dest_rel}"
            print(msg)
            self.db.log_event("RENAMED", dest_rel, old_hash=old_hash, new_hash=new_hash,
                              diff=f"moved from {src_rel}")
            self.alert.send_alert(f"File renamed: {src_rel} -> {dest_rel}")


def initial_scan(root_dir: str) -> HashStore:
    store = HashStore()
    hashes = fim_core.get_all_files_hashes(root_dir)
    store._hashes = hashes
    return store