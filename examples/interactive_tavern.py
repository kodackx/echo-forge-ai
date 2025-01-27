"""
Interactive script to test the tavern adventure.
Run this script to interact with the tavern adventure directly.
"""
import asyncio
import os
import argparse
from dotenv import load_dotenv

from echoforgeai import Story, StoryConfig
from tavern_adventure import create_characters, create_initial_node, create_player_character


def parse_args():
    parser = argparse.ArgumentParser(description="Interactive tavern adventure example")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--debug-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set debug logging level")
    return parser.parse_args()


async def main():
    # Parse command line arguments
    args = parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize story with OpenAI key from environment and debug settings
    story = Story(StoryConfig(
        title="The Silver Flagon Tavern",
        api_key=os.getenv("OPENAI_API_KEY"),
        debug_mode=args.debug,
        debug_level=args.debug_level
    ))
    
    # Create player character first
    player = await create_player_character()
    await story.add_character(player)
    
    # Add NPC characters and initial node
    print("\nSetting up the tavern scene...")
    for character in await create_characters():
        await story.add_character(character)
    story.graph.add_node(create_initial_node())
    
    # Start the story
    print(f"\nWelcome, {player.name}!")
    print("\nStarting the story...\n")
    result = await story.start()
    print(result["text"])
    
    # Main interaction loop
    while True:
        try:
            print(f"\nWhat would you like to do, {player.name}? (type 'quit' to end)")
            user_input = input("> ").strip()
            
            if user_input.lower() == 'quit':
                break
                
            result = await story.advance(user_input)
            print(f"\n{result['text']}")
                    
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break


if __name__ == "__main__":
    asyncio.run(main()) 