"""
Core Story class that serves as the main entry point for HearthKin 2.
"""
from typing import Dict, List, Optional, Union
from pydantic import BaseModel

from echoforgeai.graph.story_graph import StoryGraph, StoryNode
from echoforgeai.memory.vector_store import MemoryBank
from echoforgeai.core.character import Character
from echoforgeai.core.llm_service import LLMService


class StoryConfig(BaseModel):
    """Configuration for a Story instance."""
    title: str
    description: Optional[str] = None
    default_llm_provider: str = "openai"
    memory_backend: str = "faiss"
    enable_multimodal: bool = False
    enable_critique: bool = True
    max_memory_items: int = 1000
    api_key: Optional[str] = None


class Story:
    """
    Main story controller that manages the narrative flow, characters, and story state.
    """
    
    def __init__(self, config: StoryConfig):
        """Initialize a new story with the given configuration."""
        self.config = config
        self.graph = StoryGraph()
        self.memory = MemoryBank(
            backend=config.memory_backend,
            max_items=config.max_memory_items
        )
        self.characters: Dict[str, Character] = {}
        self.current_node: Optional[StoryNode] = None
        self.llm = LLMService(
            provider=config.default_llm_provider,
            api_key=config.api_key
        )
        
    async def add_character(self, character: Character) -> None:
        """Add a character to the story."""
        self.characters[character.name] = character
        character.bind_memory_bank(self.memory)
        character.bind_llm_service(self.llm)
        
    async def advance(self, user_input: str) -> dict:
        """
        Advance the story based on user input.
        Returns a dict containing the next story beat, available choices, and any generated content.
        """
        if not self.current_node:
            raise RuntimeError("Story hasn't been started. Call start() first.")
            
        # Retrieve relevant memories
        relevant_memories = await self.memory.retrieve_relevant(user_input)
        
        # Get character contexts
        character_contexts = {
            name: char.get_context()
            for name, char in self.characters.items()
        }
        
        # Generate next story beat using LLM
        llm_response = await self.llm.generate_story_beat(
            current_content=self.current_node.content,
            user_input=user_input,
            memories=[m.content for m in relevant_memories],
            character_contexts=character_contexts
        )
        
        # Update character states based on metadata
        if llm_response.metadata.get("character_updates"):
            for char_name, updates in llm_response.metadata["character_updates"].items():
                if char_name in self.characters:
                    await self.characters[char_name].apply_updates(updates)
        
        # Create and store the new story beat
        next_beat = await self.graph.process_input(
            self.current_node,
            user_input,
            relevant_memories,
            llm_response
        )
        
        # Update current node
        self.current_node = next_beat.next_node
        
        # Store new memories from this interaction
        await self.memory.store(next_beat.to_memory())
        
        return {
            "text": next_beat.text,
            "choices": next_beat.available_choices,
            "generated_content": next_beat.generated_content
        }
        
    async def start(self, entry_node_id: Optional[str] = None) -> dict:
        """Start the story from the specified entry node or the default start node."""
        self.current_node = self.graph.get_entry_node(entry_node_id)
        initial_beat = await self.graph.get_initial_beat(self.current_node)
        
        return {
            "text": initial_beat.text,
            "choices": initial_beat.available_choices,
            "generated_content": initial_beat.generated_content
        }
        
    def save_state(self) -> dict:
        """Save the current story state."""
        return {
            "config": self.config.model_dump(),
            "current_node_id": self.current_node.id if self.current_node else None,
            "memory": self.memory.export_state(),
            "graph": self.graph.export_state(),
            "characters": {
                name: char.export_state()
                for name, char in self.characters.items()
            }
        }
        
    @classmethod
    async def load_state(cls, state: dict) -> "Story":
        """Load a story from a saved state."""
        config = StoryConfig(**state["config"])
        story = cls(config)
        
        # Restore state
        await story.memory.import_state(state["memory"])
        await story.graph.import_state(state["graph"])
        
        # Restore characters
        for char_name, char_state in state["characters"].items():
            character = Character.from_state(char_state)
            await story.add_character(character)
        
        if state["current_node_id"]:
            story.current_node = story.graph.get_node(state["current_node_id"])
            
        return story 