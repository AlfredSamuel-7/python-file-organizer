#!/usr/bin/env python3
"""
Automated File Organizer + Duplicate Remover
Author: Alfred Samuel (template)
Description:
 - Organize files in a directory by extension (create subfolders)
 - Identify and optionally remove duplicate files (based on SHA256 hash)
 - Generate a CSV/JSON report
 - Supports dry-run and safety checks
"""

import argparse
import hashlib
import os
import shutil
import sys
import csv
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ---------------------------
# Utility functions
# ---------------------------

def compute_hash(path, chunk_size=8192):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def safe_mkdir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def is_same_file(a, b):
    # quick size check then full hash compare
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    return compute_hash(a) == compute_hash(b)

# ---------------------------
# Core features
# ---------------------------

def scan_files(root, recursive=True, ignore_dirs=None):
    ignore_dirs = set(ignore_dirs or [])
    files = []
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        # skip .git and Library-like folders
        if any(ig in dirpath for ig in ignore_dirs):
            continue
        for fname in filenames:
            full = Path(dirpath) / fname
            if not full.is_file():
                continue
            files.append(full)
        if not recursive:
            break
    return files

def categorize_by_extension(files):
    by_ext = defaultdict(list)
    for p in files:
        ext = p.suffix.lower().lstrip('.') or 'no_ext'
        by_ext[ext].append(p)
    return by_ext

def organize_files(root, target_dir=None, dry_run=False, move=True, ignore_dirs=None):
    """
    Move files into folders under target_dir (or root).
    Folder names are the extension (e.g., 'pdf', 'jpg', 'no_ext').
    If move=False, copies instead of moves.
    """
    files = scan_files(root, recursive=True, ignore_dirs=ignore_dirs)
    target_dir = Path(target_dir or root)
    ops = []
    for f in files:
        rel_path = f.relative_to(root)
        # skip if already in an extension folder directly under target_dir
        if len(rel_path.parts) >= 2 and rel_path.parts[0].lower() == f.suffix.lower().lstrip('.'):
            continue
        ext = f.suffix.lower().lstrip('.') or 'no_ext'
        folder = target_dir / ext
        safe_mkdir(folder)
        dest = folder / f.name
        # ensure unique filename at destination
        counter = 1
        while dest.exists():
            # if same file, skip
            if is_same_file(str(dest), str(f)):
                ops.append({'action': 'skip_same', 'src': str(f), 'dest': str(dest)})
                break
            name = f.stem + f"_{counter}" + f.suffix
            dest = folder / name
            counter += 1
        else:
            ops.append({'action': 'copy' if not move else 'move', 'src': str(f), 'dest': str(dest)})
            if not dry_run:
                if move:
                    shutil.move(str(f), str(dest))
                else:
                    shutil.copy2(str(f), str(dest))
    return ops

def find_duplicates(root, ignore_dirs=None):
    files = scan_files(root, recursive=True, ignore_dirs=ignore_dirs)
    size_map = defaultdict(list)
    for f in files:
        try:
            size_map[f.stat().st_size].append(f)
        except (OSError, PermissionError):
            continue

    duplicates = []  # list of lists
    for size, group in size_map.items():
        if len(group) < 2:
            continue
        hash_map = defaultdict(list)
        for p in group:
            try:
                h = compute_hash(p)
                hash_map[h].append(p)
            except (OSError, PermissionError):
                continue
        for h, plist in hash_map.items():
            if len(plist) > 1:
                duplicates.append((h, plist))
    return duplicates

def remove_duplicates(duplicates, keep='first', dry_run=False):
    """
    duplicates: list of tuples (hash, [Path,...])
    keep: 'first' or 'latest' or 'largest' (default first)
    """
    removed = []
    for h, plist in duplicates:
        # sort by mtime
        sorted_list = sorted(plist, key=lambda p: p.stat().st_mtime)
        if keep == 'first':
            keeper = sorted_list[0]
            to_remove = sorted_list[1:]
        elif keep == 'latest':
            keeper = sorted_list[-1]
            to_remove = sorted_list[:-1]
        else:
            keeper = sorted_list[0]
            to_remove = sorted_list[1:]

        for p in to_remove:
            removed.append({'hash': h, 'removed': str(p), 'kept': str(keeper)})
            if not dry_run:
                try:
                    os.remove(p)
                except Exception as e:
                    removed[-1]['error'] = str(e)
    return removed

def generate_report(ops, duplicates, removed, out_file=None):
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'operations': ops,
        'duplicates_found': [{'hash': h, 'paths': [str(x) for x in ps]} for h, ps in duplicates],
        'removed': removed
    }
    if out_file:
        out_path = Path(out_file)
        if out_path.suffix.lower() == '.json':
            out_path.write_text(json.dumps(report, indent=2))
        elif out_path.suffix.lower() == '.csv':
            # simplify CSV: operations + removed count
            with open(out_path, 'w', newline='', encoding='utf-8') as csvf:
                writer = csv.writer(csvf)
                writer.writerow(['timestamp', report['timestamp']])
                writer.writerow([])
                writer.writerow(['Operation', 'Source', 'Destination'])
                for op in ops:
                    writer.writerow([op.get('action'), op.get('src'), op.get('dest')])
                writer.writerow([])
                writer.writerow(['Removed', 'Path', 'Kept'])
                for r in removed:
                    writer.writerow([r.get('hash'), r.get('removed'), r.get('kept')])
        else:
            out_path.write_text(json.dumps(report, indent=2))
    return report

# ---------------------------
# Command line interface
# ---------------------------

def parse_args():
    p = argparse.ArgumentParser(description="File Organizer & Duplicate Remover")
    p.add_argument('root', nargs='?', default='.', help='Root folder to operate on')
    p.add_argument('--organize', action='store_true', help='Organize files by extension into subfolders')
    p.add_argument('--move', action='store_true', help='Move files instead of copying when organizing (default behavior with --organize)')
    p.add_argument('--dry-run', action='store_true', help='Do not modify files, show actions only')
    p.add_argument('--duplicates', action='store_true', help='Scan for duplicate files')
    p.add_argument('--remove-duplicates', action='store_true', help='Remove duplicates (use with --duplicates) - keeps the first file by default')
    p.add_argument('--keep', choices=['first', 'latest'], default='first', help='Which duplicate to keep when removing')
    p.add_argument('--report', help='Write a JSON/CSV report to specified file')
    p.add_argument('--ignore', nargs='*', default=['.git', 'Library', 'node_modules'], help='Directories to ignore')
    p.add_argument('--no-recursive', dest='recursive', action='store_false', help='Do not recurse into subfolders')
    p.add_argument('--version', action='version', version='file-organizer 1.0')
    return p.parse_args()

def main():
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Error: root path does not exist: {root}")
        sys.exit(1)

    ops = []
    duplicates = []
    removed = []

    if args.organize:
        print(f"{'DRY RUN: ' if args.dry_run else ''}Organizing files under: {root}")
        ops = organize_files(root, target_dir=root, dry_run=args.dry_run, move=args.move, ignore_dirs=args.ignore)
        print(f"Organize operations: {len(ops)}")

    if args.duplicates:
        print("Scanning for duplicates...")
        duplicates = find_duplicates(root, ignore_dirs=args.ignore)
        print(f"Duplicate groups found: {len(duplicates)}")
        for h, plist in duplicates:
            print(f"Hash: {h} -> {len(plist)} files")
            for p in plist:
                print("  ", p)

    if args.remove_duplicates:
        if not duplicates:
            duplicates = find_duplicates(root, ignore_dirs=args.ignore)
        print(f"{'DRY RUN: ' if args.dry_run else ''}Removing duplicates (keep={args.keep})...")
        removed = remove_duplicates(duplicates, keep=args.keep, dry_run=args.dry_run)
        print(f"Files removed: {len(removed)}")

    if args.report:
        report = generate_report(ops, duplicates, removed, out_file=args.report)
        print(f"Report written to: {args.report}")
    else:
        report = generate_report(ops, duplicates, removed, out_file=None)
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
