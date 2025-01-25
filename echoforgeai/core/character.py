"""
Character class that manages personality traits, memory, and dialogue generation.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from echoforgeai.memory.vector_store import MemoryBank
from echoforgeai.core.llm_service import LLMService


class PersonalityTrait(BaseModel):
    """A single personality trait with its intensity."""
    name: str
    intensity: float = Field(ge=0.0, le=1.0)
    description: Optional[str] = None


class CharacterGoal(BaseModel):
    """A character's goal, either short-term or long-term."""
    description: str
    priority: float = Field(ge=0.0, le=1.0)
    is_long_term: bool = False
    progress: float = Field(ge=0.0, le=1.0, default=0.0)


class PersonalityModel(BaseModel):
    """
    A character's personality model incorporating traits, goals, and relationships.
    """
    traits: Dict[str, PersonalityTrait]
    goals: List[CharacterGoal]
    relationships: Dict[str, float] = Field(default_factory=dict)  # character_name -> sentiment
    archetype: Optional[str] = None
    background: Optional[str] = None


class Character:
    """
    Represents a character in the story with personality, memory, and dialogue generation capabilities.
    """
    
    def __init__(
        self,
        name: str,
        personality: PersonalityModel,
        initial_knowledge: Optional[List[str]] = None
    ):
        """Initialize a character with their personality and initial knowledge."""
        self.name = name
        self.personality = personality
        self._memory: Optional[MemoryBank] = None
        self._llm: Optional[LLMService] = None
        self._initial_knowledge = initial_knowledge or []
        
    def bind_memory_bank(self, memory_bank: MemoryBank) -> None:
        """Bind a memory bank to this character and initialize their knowledge."""
        self._memory = memory_bank
        # Store initial knowledge
        for knowledge in self._initial_knowledge:
            self._memory.store_sync(
                knowledge,
                metadata={"character": self.name, "type": "initial_knowledge"}
            )
            
    def bind_llm_service(self, llm_service: LLMService) -> None:
        """Bind an LLM service to this character."""
        self._llm = llm_service
            
    async def speak(
        self,
        topic: str,
        context: Optional[dict] = None,
        style: Optional[str] = None
    ) -> str:
        """
        Generate dialogue for this character based on their personality and memories.
        
        Args:
            topic: The topic or prompt for the dialogue
            context: Additional context about the current scene/situation
            style: Optional style override (e.g., "angry", "formal", etc.)
            
        Returns:
            Generated dialogue string
        """
        if not self._memory:
            raise RuntimeError("Character must be bound to a memory bank before speaking")
        if not self._llm:
            raise RuntimeError("Character must be bound to an LLM service before speaking")
            
        # Retrieve relevant memories
        memories = await self._memory.retrieve_relevant(
            topic,
            filter_metadata={"character": self.name}
        )
        
        # Generate dialogue using LLM
        return await self._llm.generate_dialogue(
            character_name=self.name,
            personality=self.personality.model_dump(),
            topic=topic,
            memories=[m.content for m in memories],
            context=context,
            style=style
        )
        
    def get_context(self) -> dict:
        """Get the character's current context for story generation."""
        return {
            "personality": self.personality.model_dump(),
            "relationships": self.personality.relationships,
            "goals": [g.model_dump() for g in self.personality.goals]
        }
        
    async def apply_updates(self, updates: dict) -> None:
        """Apply updates to the character's state from story generation."""
        # Update relationships
        if "relationships" in updates:
            for char_name, sentiment in updates["relationships"].items():
                await self.update_relationship(char_name, sentiment - self.personality.relationships.get(char_name, 0.0))
                
        # Update goal progress
        if "goal_updates" in updates:
            for goal_update in updates["goal_updates"]:
                for goal in self.personality.goals:
                    if goal.description == goal_update["description"]:
                        goal.progress = min(1.0, max(0.0, goal_update["progress"]))
                        break
                        
        # Store any new knowledge
        if "new_knowledge" in updates:
            for knowledge in updates["new_knowledge"]:
                await self.learn(knowledge)
        
    async def update_relationship(self, other_character: str, sentiment_delta: float) -> None:
        """Update this character's relationship with another character."""
        current = self.personality.relationships.get(other_character, 0.0)
        new_sentiment = max(min(current + sentiment_delta, 1.0), -1.0)
        self.personality.relationships[other_character] = new_sentiment
        
    async def learn(self, knowledge: str, importance: float = 0.5) -> None:
        """Add new knowledge to the character's memory."""
        if not self._memory:
            raise RuntimeError("Character must be bound to a memory bank before learning")
            
        await self._memory.store(
            knowledge,
            metadata={
                "character": self.name,
                "type": "learned_knowledge",
                "importance": importance
            }
        )
        
    async def recall(self, query: str, limit: int = 5) -> List[str]:
        """Retrieve relevant memories for this character."""
        if not self._memory:
            raise RuntimeError("Character must be bound to a memory bank before recalling")
            
        memories = await self._memory.retrieve_relevant(
            query,
            filter_metadata={"character": self.name},
            limit=limit
        )
        return [m.content for m in memories]
        
    def export_state(self) -> dict:
        """Export character state for serialization."""
        return {
            "name": self.name,
            "personality": self.personality.model_dump(),
            "initial_knowledge": self._initial_knowledge
        }
        
    @classmethod
    def from_state(cls, state: dict) -> "Character":
        """Create a character from a saved state."""
        personality = PersonalityModel(**state["personality"])
        return cls(
            name=state["name"],
            personality=personality,
            initial_knowledge=state["initial_knowledge"]
        ) 