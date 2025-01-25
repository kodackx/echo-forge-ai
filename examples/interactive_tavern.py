"""
Interactive script to test the tavern adventure.
Run this script to interact with the tavern adventure directly.
"""
import asyncio
import os
from dotenv import load_dotenv

from echoforgeai import Story, StoryConfig
from tavern_adventure import create_characters, create_initial_node

async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize story with OpenAI key from environment
    story = Story(StoryConfig(
        title="The Silver Flagon Tavern",
        api_key=os.getenv("OPENAI_API_KEY")
    ))
    
    # Add characters and initial node
    print("Setting up the tavern scene...")
    for character in await create_characters():
        await story.add_character(character)
    story.graph.add_node(create_initial_node())
    
    # Start the story
    print("\nStarting the story...\n")
    result = await story.start()
    print(result["text"])
    
    # Main interaction loop
    while True:
        try:
            # Display available choices
            if "choices" in result and result["choices"]:
                print("\nWhat would you like to do?")
                for i, choice in enumerate(result["choices"], 1):
                    print(f"{i}. {choice}")
                
                # Get user input
                user_input = input("\nYour choice (or 'quit' to end): ").strip()
                if user_input.lower() == 'quit':
                    break
                
                try:
                    choice_num = int(user_input)
                    if 1 <= choice_num <= len(result["choices"]):
                        # Use the actual choice text for the story advancement
                        chosen_action = result["choices"][choice_num - 1]
                        result = await story.advance(chosen_action)
                        print(f"\n{result['text']}")
                    else:
                        print("Invalid choice number. Please try again.")
                except ValueError:
                    # If the input isn't a number, use it as direct input
                    result = await story.advance(user_input)
                    print(f"\n{result['text']}")
            else:
                print("\nThe story has reached an end. Type 'quit' to exit.")
                if input().lower() == 'quit':
                    break
                    
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    asyncio.run(main()) 