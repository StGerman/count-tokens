#!/usr/bin/env python3
"""
Token counter for files respecting .gitignore patterns.

Counts tokens in code files using tiktoken encoding, automatically
excluding files based on .gitignore patterns. Provides per-file 
breakdown and cost estimates for LLM API calls.

Usage:
    ./count_tokens.py                           # Basic usage
    ./count_tokens.py --no-files                # Summary only
    ./count_tokens.py --encoding o200k_base     # Different encoding
    ./count_tokens.py --extensions .py .js      # Custom extensions
    ./count_tokens.py --top 50                  # Show top 50 files

Requirements:
    pip install tiktoken pathspec
"""

import sys
from pathlib import Path
from typing import List, Tuple, Set

import tiktoken
import pathspec

# Default code file extensions
DEFAULT_EXTENSIONS = (
    '.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.java', '.go',
    '.rb', '.php', '.c', '.cpp', '.h', '.cs', '.swift', '.kt',
    '.rs', '.scala', '.r', '.m', '.sh', '.yml', '.yaml', '.json',
    '.xml', '.html', '.css', '.scss', '.vue', '.sql', '.toml'
)

# Cost per token (input) for common models
COST_PER_TOKEN = {
    'Claude Sonnet 4': 0.000003,
    'Claude Opus 4': 0.000015,
    'GPT-4o': 0.0000025,
    'GPT-4o mini': 0.00000015,
    'GPT-4 Turbo': 0.00001,
}


def load_gitignore_patterns() -> pathspec.PathSpec:
    """Load .gitignore patterns from current directory and parent directories."""
    patterns = []
    
    # Common patterns to always ignore
    default_patterns = [
        '.git/',
        '.git/**',
        '**/.git/',
        '**/.git/**',
    ]
    patterns.extend(default_patterns)
    
    # Look for .gitignore files from current directory up to root
    current_path = Path.cwd()
    for path in [current_path] + list(current_path.parents):
        gitignore_path = path / '.gitignore'
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    gitignore_patterns = f.read().splitlines()
                    # Filter out comments and empty lines
                    gitignore_patterns = [
                        line.strip() for line in gitignore_patterns
                        if line.strip() and not line.strip().startswith('#')
                    ]
                    patterns.extend(gitignore_patterns)
            except Exception as e:
                print(f"Warning: Could not read {gitignore_path} ({e})", file=sys.stderr)
    
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)


def get_files_respecting_gitignore() -> List[str]:
    """Get list of files in current directory, respecting .gitignore patterns."""
    gitignore_spec = load_gitignore_patterns()
    files = []
    
    # Walk through all files in current directory
    for path in Path.cwd().rglob('*'):
        if path.is_file():
            # Convert to relative path for gitignore matching
            relative_path = path.relative_to(Path.cwd())
            relative_path_str = str(relative_path)
            
            # Check if file should be ignored
            if not gitignore_spec.match_file(relative_path_str):
                files.append(relative_path_str)
    
    return sorted(files)


def count_file_tokens(
    filepath: str,
    encoding: tiktoken.Encoding
) -> int:
    """
    Count tokens in a single file.

    Args:
        filepath: Path to file
        encoding: tiktoken encoding instance

    Returns:
        Token count, or 0 if file cannot be read
    """
    try:
        content = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        return len(encoding.encode(content))
    except Exception as e:
        print(f"Warning: Skipped {filepath} ({e})", file=sys.stderr)
        return 0


def count_tokens(
    encoding_name: str = "cl100k_base",
    extensions: Tuple[str, ...] = DEFAULT_EXTENSIONS,
    show_files: bool = True,
    top_n: int = 30
) -> None:
    """
    Count tokens in all files, respecting .gitignore patterns.

    Args:
        encoding_name: tiktoken encoding name
        extensions: Tuple of file extensions to include
        show_files: Whether to show per-file breakdown
        top_n: Number of top files to display
    """
    encoding = tiktoken.get_encoding(encoding_name)
    files = get_files_respecting_gitignore()

    # Count tokens per file
    file_counts: List[Tuple[str, int]] = []
    for filepath in files:
        if not filepath.endswith(extensions):
            continue

        tokens = count_file_tokens(filepath, encoding)
        if tokens > 0:
            file_counts.append((filepath, tokens))

    # Sort by token count descending
    file_counts.sort(key=lambda x: x[1], reverse=True)

    total_tokens = sum(tokens for _, tokens in file_counts)

    # Display results
    if show_files and file_counts:
        print(f"Top {min(top_n, len(file_counts))} files by token count:")
        print("=" * 60)
        for path, tokens in file_counts[:top_n]:
            print(f"{tokens:>8,} tokens | {path}")
        print("=" * 60)

    print(f"\nTotal tokens: {total_tokens:,}")
    print(f"Total files: {len(file_counts)}")
    if file_counts:
        print(f"Average per file: {total_tokens // len(file_counts):,} tokens")

    # Cost estimates
    print("\nCost estimates (per API call):")
    for model, cost in COST_PER_TOKEN.items():
        print(f"  {model:<18} ${total_tokens * cost:.4f}")


def main() -> None:
    """Parse arguments and run token counting."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Count tokens in files respecting .gitignore patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--encoding',
        default='cl100k_base',
        help='Tiktoken encoding name (default: cl100k_base)'
    )
    parser.add_argument(
        '--no-files',
        action='store_true',
        help='Hide per-file breakdown'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=30,
        help='Number of top files to show (default: 30)'
    )
    parser.add_argument(
        '--extensions',
        nargs='+',
        help='Custom file extensions (e.g., .py .js .md)'
    )

    args = parser.parse_args()

    extensions = tuple(args.extensions) if args.extensions else DEFAULT_EXTENSIONS

    count_tokens(
        encoding_name=args.encoding,
        extensions=extensions,
        show_files=not args.no_files,
        top_n=args.top
    )


if __name__ == "__main__":
    main()
