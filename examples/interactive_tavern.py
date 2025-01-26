"""
Interactive script to test the tavern adventure.
Run this script to interact with the tavern adventure directly.
"""
import asyncio
import os
from dotenv import load_dotenv

from echoforgeai import Story, StoryConfig
from tavern_adventure import create_characters, create_initial_node, create_player_character

async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize story with OpenAI key from environment
    story = Story(StoryConfig(
        title="The Silver Flagon Tavern",
        api_key=os.getenv("OPENAI_API_KEY")
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