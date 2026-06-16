# ⚡ qnote

> A fast, beautiful CLI note-taking tool for developers

[![Tests](https://github.com/OnlinePerson/coup/actions/workflows/tests.yml/badge.svg)](https://github.com/OnlinePerson/coup/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Capture thoughts, commands, snippets, and ideas without leaving your terminal. **qnote** stores everything locally in SQLite — no cloud, no account, no noise.

```
$ qn add "Fix the auth bug before deploy" --tag work --tag urgent
✓ Note #1 saved   #work  #urgent

$ qn list
╭─────┬────────────────────────────────────┬──────────────┬────────────╮
│ ID  │ Note                               │ Tags         │ Created    │
├─────┼────────────────────────────────────┼──────────────┼────────────┤
│ 1   │ Fix the auth bug before deploy     │ #work #urgent│ 2024-01-15 │
╰─────┴────────────────────────────────────┴──────────────┴────────────╯
```

## Features

- **Add** notes with multiple tags
- **List** notes with optional tag filter
- **Search** full-text across all notes
- **Show** a single note in full
- **Delete** notes by ID
- **Export** to Markdown or JSON
- **Tags** overview with counts
- SQLite storage at `~/.qnote/notes.db` — yours forever
- Beautiful output with [Rich](https://github.com/Textualize/rich)

## Installation

```bash
# From PyPI (once published)
pip install qnote

# From source
git clone https://github.com/OnlinePerson/coup
cd coup
pip install -e .
```

## Usage

```bash
# Add a note
qn add "remember to update the docs"
qn add "kubectl get pods -n prod" --tag k8s --tag ops

# List notes (newest first)
qn list
qn list --tag k8s
qn list --limit 5

# Full-text search
qn search "kubectl"

# Show a note in full
qn show 3

# Delete a note
qn delete 3
qn delete 3 --yes   # skip confirmation

# All tags with counts
qn tags

# Export
qn export                      # markdown to stdout
qn export --format json
qn export --format md --output notes.md
```

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

## License

MIT
