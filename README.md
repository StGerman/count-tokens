# Count Tokens

A fast CLI tool that counts tokens in git-tracked files using tiktoken encoding, perfect for estimating LLM API costs before processing your codebase.

## Why Count Tokens?

When working with LLMs, understanding token usage helps you:
- **Estimate API costs** before sending large codebases to models
- **Stay within context limits** for different LLM models
- **Optimize prompts** by identifying the largest files
- **Budget effectively** for AI-assisted development workflows

## Installation

### From PyPI (when published)

```bash
pip install count-tokens
```

### From Source

```bash
git clone <repository-url>
cd count_tokens
poetry install
```

## Quick Start

```bash
# Count tokens in your current repository
count-tokens

# Get just the summary without file breakdown
count-tokens --no-files

# Focus on specific file types
count-tokens --extensions .py .js .ts .md
```

## Usage Examples

### Basic Token Counting
```bash
count-tokens
```
```
Top 4 files by token count:
============================================================
   1,209 tokens | src/main.py
     639 tokens | docs/api.md
     290 tokens | README.md
     138 tokens | config.yaml
============================================================

Total tokens: 2,276
Total files: 4
Average per file: 569 tokens

Cost estimates (per API call):
  Claude Sonnet 4    $0.0068
  Claude Opus 4      $0.0341
  GPT-4o             $0.0057
  GPT-4o mini        $0.0003
  GPT-4 Turbo        $0.0228
```

### Summary Only
```bash
count-tokens --no-files
```
Perfect for CI/CD pipelines or when you just need the totals.

### Custom File Types
```bash
count-tokens --extensions .py .js .md
```
Focus on specific languages or documentation files.

### Different Encodings
```bash
count-tokens --encoding o200k_base
```
Use different tiktoken encodings (cl100k_base, o200k_base, etc.).

### Show More Files
```bash
count-tokens --top 50
```
Display up to 50 files instead of the default 30.

## Supported File Types

The tool automatically detects and counts tokens in 25+ common file extensions:

**Languages:** `.py` `.js` `.ts` `.jsx` `.tsx` `.java` `.go` `.rb` `.php` `.c` `.cpp` `.h` `.cs` `.swift` `.kt` `.rs` `.scala` `.r` `.m` `.sh`

**Config & Data:** `.yml` `.yaml` `.json` `.xml` `.toml` `.sql`

**Web & Docs:** `.html` `.css` `.scss` `.vue` `.md`

## Features

✅ **Git Integration** - Only counts committed/tracked files  
✅ **Smart Filtering** - Supports 25+ code file extensions  
✅ **Cost Estimation** - Real-time pricing for popular LLM APIs  
✅ **Flexible Encodings** - Works with all tiktoken encodings  
✅ **Top Files View** - Identify your largest files quickly  
✅ **Error Resilient** - Gracefully handles unreadable files  
✅ **Fast Performance** - Optimized for large repositories  

## Development

### Setup
```bash
# Install dependencies
poetry install

# Run during development
poetry run count-tokens
# or make executable and run directly
chmod +x count_tokens.py
./count_tokens.py
```

### Building & Publishing
```bash
# Build package
poetry build

# Publish to PyPI
poetry publish
```

### Testing
```bash
# Test on current repository
poetry run count-tokens

# Test with different options
poetry run count-tokens --no-files --encoding o200k_base
```

## Requirements

- **Python 3.11+**
- **Git repository** (uses `git ls-files` to find tracked files)
- **tiktoken** library for token encoding

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details.