import os
import argparse
import fnmatch

# --- Configuration ---
DEFAULT_EXCLUDE_FILE_TYPES = ['*lock.json'] # '*.yml', 'recursive_print.py', '*lock.json', '*.svg', '*.md', '*.txt', 'Dockerfile', '.*ignore', '*.sh', '.flake8']
EXCLUDE_DIR = ['node_modules', '.git'] # 'volume-init', 'tests', 'build', '.pytest_cache', '.git', '*venv', '__pycache__', 'e2e', 'models']
# ---------------------

BASE_DIR = None


def should_exclude(path_parts, exclude_list):
    return any(part in exclude_list for part in path_parts)


def print_tree(root, prefix=""):
    """Recursively print directory tree, respecting EXCLUDE_DIR and PermissionError."""
    try:
        entries = sorted(os.listdir(root))
    except PermissionError:
        print(prefix + '[Permission Denied]: ' + os.path.basename(root))
        return

    # Skip showing this script in its own listing
    entries = [e for e in entries if e != os.path.basename(__file__)]

    for index, name in enumerate(entries):
        path = os.path.join(root, name)
        connector = '└── ' if index == len(entries) - 1 else '├── '
        print(prefix + connector + name)

        if os.path.isdir(path):
            rel_parts = os.path.relpath(path, start=BASE_DIR).split(os.sep)
            if should_exclude(rel_parts, EXCLUDE_DIR):
                # Print directory name but do not descend into it
                continue

            extension = '    ' if index == len(entries) - 1 else '│   '
            print_tree(path, prefix + extension)


def file_excluded(filename, exclude_patterns):
    """Return True if filename matches any pattern in exclude_patterns."""
    return any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns)


def print_contents(root, exclude_patterns, dry_run=False):
    """Find and print contents of files, excluding those matching patterns."""
    for dirpath, dirnames, filenames in os.walk(
        root,
        topdown=True,
        onerror=lambda e: print(f"[Permission Denied]: {e.filename}")
    ):
        # Skip excluded directories
        rel_dir = os.path.relpath(dirpath, start=BASE_DIR)
        parts = rel_dir.split(os.sep) if rel_dir != '.' else []
        if should_exclude(parts, EXCLUDE_DIR):
            dirnames[:] = []  # Don't descend into excluded dirs
            continue

        for filename in filenames:
            if file_excluded(filename, exclude_patterns):
                continue

            rel_path = os.path.relpath(os.path.join(dirpath, filename), start=BASE_DIR)
            if dry_run:
                print(rel_path)
            else:
                print(f"\n=== {rel_path} ===")
                try:
                    with open(os.path.join(dirpath, filename), 'r', encoding='utf-8') as f:
                        print(f.read())
                except PermissionError:
                    print(f"[Permission Denied]: {rel_path}")
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Recursively print tree and contents of files, excluding specified types."
    )
    parser.add_argument(
        'target', nargs='?', default='.',
        help='Target directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--exclude-file', '-x',
        action='append', default=None,
        help=(
            'File pattern(s) to exclude (wildcards OK or exact names). '
            'Can be used multiple times. E.g. -x "*.yml" -x "README.md"'
        )
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Only print the matched filenames, not their contents'
    )
    args = parser.parse_args()

    global BASE_DIR
    BASE_DIR = os.path.abspath(args.target)
    exclude_patterns = args.exclude_file if args.exclude_file else DEFAULT_EXCLUDE_FILE_TYPES

    print(f"Base Directory: {BASE_DIR}")
    print_tree(BASE_DIR)
    print("\n" + ("DRY RUN: Filenames only" if args.dry_run else "Printing file contents") + "\n")
    print_contents(BASE_DIR, exclude_patterns, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
