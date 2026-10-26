import difflib
import os
from pathlib import Path

def get_text_diff(filepath_old, filepath_new, max_size=1024*1024):
    """
    Return a unified diff string between two files,
    or None if they are identical / cannot be read.
    Skip if file is too large to avoid memory issues.
    """
    try:
        size = os.path.getsize(filepath_new)
        if size > max_size:
            return "[File too large, diff skipped]"
        with open(filepath_old, 'r', encoding='utf-8', errors='ignore') as f:
            old_lines = f.readlines()
        with open(filepath_new, 'r', encoding='utf-8', errors='ignore') as f:
            new_lines = f.readlines()
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=filepath_old,
            tofile=filepath_new
        )
        return ''.join(diff)
    except Exception as e:
        return f"[Diff error: {e}]"