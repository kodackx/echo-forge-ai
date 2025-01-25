# HearthKin 2 Examples

This directory contains example applications demonstrating the capabilities of HearthKin 2.

## Tavern Adventure

A simple interactive story set in a medieval tavern that showcases:
- Character personality and dialogue generation
- Memory-based storytelling
- Dynamic branching narratives
- Character relationships and goals

### Running the Example

1. Make sure you have HearthKin 2 installed:
```bash
# From the project root
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

2. Set up your configuration:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```
   - Alternatively, you can set the API key as an environment variable:
     ```bash
     export OPENAI_API_KEY=your_api_key_here
     ```

3. Run the example:
```bash
python tavern_adventure.py
```

### Configuration Options

The example supports several configuration options that can be set in the `.env` file:

```env
# Required
OPENAI_API_KEY=your_api_key_here

# Optional
MODEL_NAME=gpt-4-turbo-preview  # Override default model
EMBEDDING_MODEL=text-embedding-3-small  # Override default embedding model
MAX_MEMORY_ITEMS=1000  # Override default memory limit
```

### Story Overview

You find yourself entering the Silver Flagon tavern on a quiet evening. The story features two main NPCs:

- **Old Tom (The Bartender)**: A friendly and observant tavern keeper who knows all the local gossip
- **The Stranger**: A mysterious figure with a secret mission

Your choices will influence:
- How the characters react to you
- What information they share
- The direction of the story
- Potential side quests and secrets

### Example Interaction

```
The warm light of the Silver Flagon tavern welcomes you as you step in from the cold evening air...

What would you like to do?
1. Approach the bar and greet Old Tom
2. Find a quiet table near the mysterious stranger
3. Look around the tavern for other interesting patrons

Your choice: 1

Old Tom smiles warmly as you approach...
```

## Adding More Examples

Feel free to contribute your own examples! Some ideas:
- A detective story using the memory system
- A political intrigue game showcasing relationship dynamics
- A multi-character conversation demonstrating personality traits
- A branching quest system with requirements 