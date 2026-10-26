#importing the libaries
import hashlib
import json
import os
from pathlib import Path
from typing import Dict

#function compute_file_hash was defined for the file evaluation

#ref: https://medium.com/@jaredpmedeiros/a-beginner-friendly-cyber-security-project-python-fim-12431ca77925
def compute_file_hash(filepath: str, chunk_size: int = 65536) -> str:
#Compute SHA-256 hash of a file in binary chunks
    sha = hashlib.sha256()
    #using exceptions 
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha.update(chunk)
        return sha.hexdigest()
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Cannot read {filepath}: {e}")

#used to get the hashes of all files 
def get_all_files_hashes(root_dir: str) -> Dict[str, str]:
#it Walks root_dir recursively and return {relative_path: sha256}
    root = Path(root_dir).resolve()
    hashes = {}
    for entry in root.rglob('*'):
        if entry.is_file():
            relative = str(entry.relative_to(root))
            try:
                hashes[relative] = compute_file_hash(str(entry))
            except RuntimeError as e:
                print(f"Warning: {e}")
    return hashes

def save_baseline(hash_dict: Dict[str, str], output_path: str = "baseline.json"):
    with open(output_path, 'w') as f:
        json.dump(hash_dict, f, indent=2)

def load_baseline(baseline_path: str = "baseline.json") -> Dict[str, str]:
    try:
        with open(baseline_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Baseline error: {e}")
    
#function created for comparing two files
def compare_baselines(old: Dict[str, str], new: Dict[str, str]):
    #Return dict of new, deleted, modified files."""
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    new_files = sorted(new_keys - old_keys)
    deleted_files = sorted(old_keys - new_keys)
    modified_files = sorted(
        k for k in old_keys & new_keys if old[k] != new[k]
    )
    return {
        "new": new_files,
        "deleted": deleted_files,
        "modified": modified_files
    }


def detailed_compare(old: Dict[str, str], new: Dict[str, str]):
    """
    Returns a sorted list of dicts, each describing a file's status:
        path, status, old_hash, new_hash
    Status can be 'unchanged', 'new', 'deleted', 'modified'.
    Also returns counts.
    """
    all_paths = set(old.keys()) | set(new.keys())
    report = []
    counts = {'unchanged': 0, 'new': 0, 'deleted': 0, 'modified': 0}

    for p in sorted(all_paths):
        if p in old and p in new:
            if old[p] == new[p]:
                status = 'unchanged'
            else:
                status = 'modified'
            report.append({
                'path': p,
                'status': status,
                'old_hash': old[p],
                'new_hash': new[p]
            })
            counts[status] += 1          # used for increments for both unchanged and modified files

        elif p in new:
            report.append({
                'path': p,
                'status': 'new',
                'old_hash': None,
                'new_hash': new[p]
            })
            counts['new'] += 1

        else:  # only in old
            report.append({
                'path': p,
                'status': 'deleted',
                'old_hash': old[p],
                'new_hash': None
            })
            counts['deleted'] += 1

    return report, counts