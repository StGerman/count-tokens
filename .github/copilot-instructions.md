# Copilot Instructions - Token Counter

## Project Overview
Single-purpose CLI tool that counts tokens in git-tracked files using tiktoken. Primary use case is estimating LLM API costs for codebases. Installable via pip with Poetry managing builds and dependencies.

## Architecture
- **Single file application**: `count_tokens.py` contains all functionality
- **Git-centric workflow**: Only processes files tracked by git (`git ls-files`)
- **tiktoken integration**: Uses OpenAI's tiktoken library for accurate token counting
- **Poetry dependency management**: Standard Poetry setup with CLI script entry point
- **pip installable**: Distributed as proper Python package

## Development Workflows

### Installation & Usage
```bash
# Install from source
poetry install
poetry run count-tokens

# Install via pip (after build/publish)
pip install count-tokens
count-tokens

# Direct execution during development
./count_tokens.py
python count_tokens.py
```

### Building & Publishing
```bash
poetry build          # Creates wheel and sdist in dist/
poetry publish         # Publishes to PyPI (requires auth)
poetry install         # Install locally for testing
```

## Key Patterns & Conventions

### CLI Entry Point
- Main script entry via `count_tokens:main` in `pyproject.toml`
- CLI command name: `count-tokens` (hyphenated for shell compatibility)
- Direct execution still supported via shebang

### File Processing Pattern
```python
# Always check git tracking first
files = get_tracked_files()  # Uses subprocess to call 'git ls-files'

# Filter by extensions, count tokens, sort by count
for filepath in files:
    if not filepath.endswith(extensions):
        continue
    tokens = count_file_tokens(filepath, encoding)
```

### Error Handling Strategy
- **Silent file skipping**: Files that can't be read are warned but don't crash
- **Git repository validation**: Exits early if not in a git repo
- **Graceful encoding errors**: Uses `errors='ignore'` when reading files

### Extension Configuration
- `DEFAULT_EXTENSIONS` tuple covers common code file types
- Always use tuples for extensions (not lists) for `str.endswith()` compatibility
- Custom extensions via `--extensions` argument override defaults entirely

## Dependencies
- **tiktoken**: Core tokenization library
- **subprocess**: Git integration (stdlib)
- **pathlib**: File operations (stdlib)
- **argparse**: CLI interface (stdlib)

## Output Format Conventions
- Token counts formatted with commas (`:,`)
- Fixed-width columns for alignment (`{tokens:>8,} tokens | {path}`)
- Consistent separator lines (`"=" * 60`)
- Cost estimates to 4 decimal places (`:.4f`)

## Key Implementation Details
- Uses `tiktoken.get_encoding()` with configurable encoding names
- Sorts files by token count descending for "top N" display
- Calculates averages using integer division (`//`)
- File reading uses UTF-8 with error tolerance