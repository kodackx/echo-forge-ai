"""
A simple example demonstrating HearthKin 2's capabilities with a tavern adventure.
"""
import asyncio
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from echoforgeai import Story, Character, StoryNode, PersonalityModel, PersonalityTrait, CharacterGoal, StoryConfig


def load_config() -> dict:
    """Load configuration from .env file or environment variables."""
    # Try to load from .env file
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try the example file
        example_path = Path(__file__).parent / '.env.example'
        if example_path.exists():
            load_dotenv(example_path)
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please set it in .env file or "
            "as OPENAI_API_KEY environment variable."
        )
    
    return {
        'api_key': api_key,
        'model_name': os.getenv('MODEL_NAME', 'gpt-4-turbo-preview'),
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
        'max_memory_items': int(os.getenv('MAX_MEMORY_ITEMS', '1000'))
    }


async def create_characters():
    """Create the NPC characters for the tavern."""
    
    # The bartender
    bartender_personality = PersonalityModel(
        traits={
            "friendly": PersonalityTrait(
                name="friendly",
                intensity=0.8,
                description="Warm and welcoming to customers"
            ),
            "observant": PersonalityTrait(
                name="observant",
                intensity=0.9,
                description="Notices details about customers and remembers them"
            ),
            "diplomatic": PersonalityTrait(
                name="diplomatic",
                intensity=0.7,
                description="Good at managing tensions between patrons"
            )
        },
        goals=[
            CharacterGoal(
                description="Keep the tavern running smoothly",
                priority=0.9,
                is_long_term=True
            ),
            CharacterGoal(
                description="Learn about the latest town gossip",
                priority=0.6,
                is_long_term=False
            )
        ],
        archetype="Mentor",
        background="Has run the Silver Flagon for 20 years, knows everyone in town"
    )
    
    # The mysterious stranger
    stranger_personality = PersonalityModel(
        traits={
            "mysterious": PersonalityTrait(
                name="mysterious",
                intensity=0.9,
                description="Keeps to themselves, speaks in riddles"
            ),
            "intelligent": PersonalityTrait(
                name="intelligent",
                intensity=0.8,
                description="Well-educated and perceptive"
            ),
            "cautious": PersonalityTrait(
                name="cautious",
                intensity=0.7,
                description="Careful about revealing too much"
            )
        },
        goals=[
            CharacterGoal(
                description="Find a trustworthy adventurer for a secret mission",
                priority=0.9,
                is_long_term=True
            )
        ],
        archetype="Mysterious Benefactor",
        background="A cloaked figure with an elegant accent and expensive taste"
    )
    
    bartender = Character(
        name="Old Tom",
        personality=bartender_personality,
        initial_knowledge=[
            "The Silver Flagon tavern has been in business for over 50 years",
            "The mysterious stranger has been coming in every night for the past week",
            "The town guard captain is getting suspicious of the stranger",
            "There are rumors of ancient ruins in the nearby forest"
        ]
    )
    
    stranger = Character(
        name="The Stranger",
        personality=stranger_personality,
        initial_knowledge=[
            "The location of a valuable artifact in the nearby ruins",
            "Dark forces are also seeking the artifact",
            "The town guard captain is corrupt and working with the dark forces",
            "Old Tom can be trusted, but discretion is essential"
        ]
    )
    
    return [bartender, stranger]


def create_initial_node() -> StoryNode:
    """Create the starting node for the story."""
    return StoryNode(
        title="Entering the Silver Flagon",
        content="""The warm light of the Silver Flagon tavern welcomes you as you step in from the cold evening air. 
The smell of hearth-cooked stew and fresh bread fills your nostrils. Behind the bar, Old Tom, the proprietor, 
polishes a mug while keeping a watchful eye on his patrons. In a shadowy corner, a cloaked figure sits alone, 
occasionally sipping from an ornate goblet.

The tavern is relatively quiet tonight, perfect for either a peaceful drink or perhaps something more interesting. 
As a newcomer, you can feel Old Tom's observant gaze taking note of your arrival, while the mysterious stranger 
seems to briefly glance in your direction before returning to their drink.""",
        is_entry_point=True,
        tags={"tavern", "evening", "peaceful"}
    )


async def create_player_character() -> Character:
    """Create the player character through a simple dialogue."""
    print("\nBefore you enter the tavern, let's establish who you are...")
    
    # Get basic info
    name = input("\nWhat is your character's name? ").strip()
    background = input("\nBriefly describe your background (e.g., 'A wandering merchant', 'A retired soldier'): ").strip()
    
    # Define some basic personality traits
    print("\nRate the following traits from 0.0 to 1.0:")
    traits = {
        "brave": float(input("How brave are you? (0.0-1.0): ").strip()),
        "curious": float(input("How curious are you? (0.0-1.0): ").strip()),
        "diplomatic": float(input("How diplomatic are you? (0.0-1.0): ").strip())
    }
    
    # Create personality model
    personality = PersonalityModel(
        traits={
            name: PersonalityTrait(
                name=name,
                intensity=value,
                description=f"Character's level of {name}"
            )
            for name, value in traits.items()
        },
        goals=[
            CharacterGoal(
                description="Find adventure and opportunity in the tavern",
                priority=0.8,
                is_long_term=True
            )
        ],
        archetype="Player Character",
        background=background
    )
    
    # Create the character
    return Character(
        name=name,
        personality=personality,
        initial_knowledge=[
            f"You are {name}, {background}",
            "You've heard rumors about the Silver Flagon tavern being a place where interesting opportunities arise",
            "You're new to this town and looking to make a name for yourself"
        ]
    )


async def main():
    """Run the tavern adventure example."""
    try:
        # Load configuration
        config = load_config()
        
        # Initialize the story
        story_config = StoryConfig(
            title="The Silver Flagon Mystery",
            description="A simple tavern adventure that might lead to something more...",
            api_key=config['api_key'],
            max_memory_items=config['max_memory_items']
        )
        
        story = Story(story_config)
        
        # Add characters
        for character in await create_characters():
            await story.add_character(character)
        
        # Set up the initial story node
        story.graph.add_node(create_initial_node())
        
        # Start the story
        result = await story.start()
        print("\n" + result["text"] + "\n")
        print("What would you like to do?")
        for i, choice in enumerate(result["choices"], 1):
            print(f"{i}. {choice}")
        
        # Main interaction loop
        while True:
            try:
                user_input = input("\nYour choice (or 'quit' to end): ").strip()
                if user_input.lower() == "quit":
                    break
                    
                result = await story.advance(user_input)
                print("\n" + result["text"] + "\n")
                
                if result["choices"]:
                    print("What would you like to do?")
                    for i, choice in enumerate(result["choices"], 1):
                        print(f"{i}. {choice}")
                else:
                    print("The story has reached an end. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
                
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 