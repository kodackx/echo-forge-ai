# HearthKin 2

A flexible Python library for creating immersive, dynamic story-driven experiences with LLMs.

## Features

- Advanced narrative management with branching storylines
- Character personality and dialogue generation
- Embeddings-based memory system
- Plugin architecture for custom mechanics
- Multi-modal support (text, audio, images)

## Installation

HearthKin 2 uses [uv](https://github.com/astral-sh/uv) for package management. First, install uv if you haven't already:

```bash
pip install uv
```

Then install HearthKin 2:

```bash
# Create and activate a new virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# For development
uv pip install -r requirements-dev.txt
```

## Quick Start

Check out the examples directory for sample applications:

```bash
cd examples
cp .env.example .env
# Edit .env and add your OpenAI API key
python tavern_adventure.py
```

## Development

Format and lint the code:

```bash
black .
isort .
ruff check .
```

Run tests:

```bash
pytest
```

## License

MIT License - see LICENSE file for details.
